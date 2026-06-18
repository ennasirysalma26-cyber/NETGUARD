"""
Service de sonde réseau — Ping ICMP et SNMP.

Dépendances système requises :
  pip install icmplib pysnmp

Pour le ping, ce service nécessite soit :
  - des privilèges root (socket raw)
  - ou la commande `fping` installée sur le système

En production, lancer le worker avec les capabilities réseau :
  setcap cap_net_raw+ep $(which python3)
"""
import asyncio
import socket
from datetime import datetime, timezone
from typing import Optional

try:
    from icmplib import async_ping, SocketPermissionError
    ICMPLIB_AVAILABLE = True
except ImportError:
    ICMPLIB_AVAILABLE = False

try:
    from pysnmp.hlapi.asyncio import (
        getCmd, nextCmd, SnmpEngine,
        CommunityData, UdpTransportTarget,
        ContextData, ObjectType, ObjectIdentity,
    )
    PYSNMP_AVAILABLE = True
except ImportError:
    PYSNMP_AVAILABLE = False


# ─── PING ────────────────────────────────────────────────────────────────────

async def ping_host(
    ip: str,
    count: int = 4,
    timeout: float = 1.0,
    interval: float = 0.2,
) -> dict:
    """
    Envoie `count` paquets ICMP vers `ip`.
    Retourne un dict avec rtt_avg, rtt_min, rtt_max, packet_loss, status.
    """
    if not ICMPLIB_AVAILABLE:
        return await _ping_fallback(ip, count, timeout)

    try:
        host = await async_ping(ip, count=count, timeout=timeout, interval=interval)
        if host.is_alive:
            return {
                "status":       "up",
                "rtt_avg_ms":   round(host.avg_rtt, 2),
                "rtt_min_ms":   round(host.min_rtt, 2),
                "rtt_max_ms":   round(host.max_rtt, 2),
                "packet_loss":  round(host.packet_loss * 100, 1),
            }
        else:
            return {
                "status":       "down",
                "rtt_avg_ms":   None,
                "rtt_min_ms":   None,
                "rtt_max_ms":   None,
                "packet_loss":  100.0,
            }
    except SocketPermissionError:
        # Pas de permissions raw socket — fallback TCP
        return await _ping_fallback(ip, count, timeout)
    except Exception as e:
        return {
            "status":       "error",
            "rtt_avg_ms":   None,
            "rtt_min_ms":   None,
            "rtt_max_ms":   None,
            "packet_loss":  100.0,
            "error":        str(e),
        }


async def _ping_fallback(ip: str, count: int = 4, timeout: float = 1.0) -> dict:
    """
    Fallback : tente une connexion TCP sur le port 80 ou 443.
    Moins précis que l'ICMP mais ne nécessite pas de permissions root.
    """
    rtts = []
    for _ in range(count):
        t0 = asyncio.get_event_loop().time()
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, 80), timeout=timeout
            )
            rtt = (asyncio.get_event_loop().time() - t0) * 1000
            rtts.append(rtt)
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
        await asyncio.sleep(0.1)

    if rtts:
        return {
            "status":       "up",
            "rtt_avg_ms":   round(sum(rtts) / len(rtts), 2),
            "rtt_min_ms":   round(min(rtts), 2),
            "rtt_max_ms":   round(max(rtts), 2),
            "packet_loss":  round((1 - len(rtts) / count) * 100, 1),
        }
    return {
        "status": "down", "rtt_avg_ms": None,
        "rtt_min_ms": None, "rtt_max_ms": None, "packet_loss": 100.0,
    }


# ─── SNMP ────────────────────────────────────────────────────────────────────

# OIDs standards
OIDS = {
    "sysDescr":    "1.3.6.1.2.1.1.1.0",
    "sysUpTime":   "1.3.6.1.2.1.1.3.0",
    "sysName":     "1.3.6.1.2.1.1.5.0",
    "sysLocation": "1.3.6.1.2.1.1.6.0",
    "ifNumber":    "1.3.6.1.2.1.2.1.0",
    # ifTable : 1.3.6.1.2.1.2.2.1.*
    "ifDescr":     "1.3.6.1.2.1.2.2.1.2",
    "ifOperStatus":"1.3.6.1.2.1.2.2.1.8",
    "ifSpeed":     "1.3.6.1.2.1.2.2.1.5",
    "ifInOctets":  "1.3.6.1.2.1.2.2.1.10",
    "ifOutOctets": "1.3.6.1.2.1.2.2.1.16",
    "ifInErrors":  "1.3.6.1.2.1.2.2.1.14",
    "ifOutErrors": "1.3.6.1.2.1.2.2.1.20",
    # HOST-RESOURCES-MIB (CPU / Mémoire)
    "hrProcessorLoad": "1.3.6.1.2.1.25.3.3.1.2",
    "hrStorageUsed":   "1.3.6.1.2.1.25.2.3.1.6",
    "hrStorageSize":   "1.3.6.1.2.1.25.2.3.1.5",
}


async def snmp_get_system(ip: str, community: str = "public", port: int = 161) -> dict:
    """Récupère les informations système via SNMP GET."""
    if not PYSNMP_AVAILABLE:
        return {"error": "pysnmp non installé"}

    results = {}
    system_oids = ["sysDescr", "sysUpTime", "sysName", "sysLocation"]

    try:
        error_indication, error_status, error_index, var_binds = await getCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((ip, port), timeout=3, retries=1),
            ContextData(),
            *[ObjectType(ObjectIdentity(OIDS[k])) for k in system_oids],
        )
        if error_indication or error_status:
            return {"error": str(error_indication or error_status)}

        for name, key in zip(var_binds, system_oids):
            results[key] = str(name[1])

    except Exception as e:
        return {"error": str(e)}

    return results


async def snmp_walk_interfaces(ip: str, community: str = "public", port: int = 161) -> list:
    """
    Parcourt l'ifTable SNMP et retourne la liste des interfaces.
    """
    if not PYSNMP_AVAILABLE:
        return []

    iface_map: dict = {}
    walk_oids = {
        "ifDescr":     OIDS["ifDescr"],
        "ifOperStatus":OIDS["ifOperStatus"],
        "ifSpeed":     OIDS["ifSpeed"],
        "ifInOctets":  OIDS["ifInOctets"],
        "ifOutOctets": OIDS["ifOutOctets"],
        "ifInErrors":  OIDS["ifInErrors"],
        "ifOutErrors": OIDS["ifOutErrors"],
    }

    try:
        for field, base_oid in walk_oids.items():
            async for (err_ind, err_stat, _, var_binds) in nextCmd(
                SnmpEngine(),
                CommunityData(community),
                UdpTransportTarget((ip, port), timeout=3, retries=1),
                ContextData(),
                ObjectType(ObjectIdentity(base_oid)),
                lexicographicMode=False,
            ):
                if err_ind or err_stat:
                    break
                for binding in var_binds:
                    oid_str = str(binding[0])
                    index = oid_str.rsplit(".", 1)[-1]
                    val   = str(binding[1])
                    iface_map.setdefault(index, {})["index"] = index
                    iface_map[index][field] = val
    except Exception:
        pass

    interfaces = []
    for idx, data in iface_map.items():
        interfaces.append({
            "index":      int(idx),
            "name":       data.get("ifDescr", f"if{idx}"),
            "status":     "up" if data.get("ifOperStatus") == "1" else "down",
            "speed_bps":  int(data.get("ifSpeed", 0) or 0),
            "in_octets":  int(data.get("ifInOctets", 0) or 0),
            "out_octets": int(data.get("ifOutOctets", 0) or 0),
            "in_errors":  int(data.get("ifInErrors", 0) or 0),
            "out_errors": int(data.get("ifOutErrors", 0) or 0),
        })
    return sorted(interfaces, key=lambda x: x["index"])


async def collect_snmp_full(ip: str, community: str = "public") -> dict:
    """Collecte complète : système + interfaces."""
    system_data, interfaces = await asyncio.gather(
        snmp_get_system(ip, community),
        snmp_walk_interfaces(ip, community),
    )
    return {
        "system":    system_data,
        "resources": {
            "cpu_percent":    None,
            "memory_percent": None,
            "temperature_c":  None,
            "note": "Nécessite HOST-RESOURCES-MIB (OID 1.3.6.1.2.1.25)",
        },
        "interfaces": interfaces,
    }
