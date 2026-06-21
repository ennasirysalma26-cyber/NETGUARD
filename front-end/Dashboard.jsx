import { useState, useEffect } from "react";
import "./Dashboard.css";

const initialEquipment = [
  { id: 1, name: "Router-Core-01", ip: "192.168.1.1",  type: "Routeur",     status: "UP",   latency: 2,   lastCheck: "Il y a 30s" },
  { id: 2, name: "SW-Access-02",   ip: "192.168.1.10", type: "Commutateur", status: "UP",   latency: 1,   lastCheck: "Il y a 30s" },
  { id: 3, name: "AP-Bureau-03",   ip: "192.168.1.20", type: "Point d'accès",status: "DOWN", latency: null,lastCheck: "Il y a 2min" },
  { id: 4, name: "Srv-Web-04",     ip: "10.0.0.5",     type: "Serveur",     status: "UP",   latency: 8,   lastCheck: "Il y a 30s" },
  { id: 5, name: "Router-Edge-05", ip: "10.0.0.1",     type: "Routeur",     status: "UP",   latency: 12,  lastCheck: "Il y a 30s" },
  { id: 6, name: "SW-Core-06",     ip: "192.168.2.1",  type: "Commutateur", status: "WARN", latency: 89,  lastCheck: "Il y a 1min" },
];

export default function Dashboard() {
  const [equipment, setEquipment] = useState(initialEquipment);
  const [lastRefresh, setLastRefresh] = useState(new Date());

  const up   = equipment.filter((e) => e.status === "UP").length;
  const down = equipment.filter((e) => e.status === "DOWN").length;
  const warn = equipment.filter((e) => e.status === "WARN").length;
  const total = equipment.length;
  const uptime = Math.round((up / total) * 100);

  const simulatePing = () => {
    setEquipment((prev) =>
      prev.map((eq) => {
        if (eq.status === "DOWN") return eq;
        const jitter = Math.floor(Math.random() * 10) - 4;
        const newLatency = Math.max(1, (eq.latency || 5) + jitter);
        return { ...eq, latency: newLatency, lastCheck: "À l'instant" };
      })
    );
    setLastRefresh(new Date());
  };

  useEffect(() => {
    const interval = setInterval(simulatePing, 15000);
    return () => clearInterval(interval);
  }, []);

  const stats = [
    { label: "Total équipements", value: total, icon: "🖧",  color: "#2563eb", bg: "rgba(37,99,235,0.1)" },
    { label: "En ligne (UP)",     value: up,    icon: "✓",   color: "#10b981", bg: "rgba(16,185,129,0.1)" },
    { label: "Hors ligne (DOWN)", value: down,  icon: "✕",   color: "#ef4444", bg: "rgba(239,68,68,0.1)" },
    { label: "Disponibilité",     value: `${uptime}%`, icon: "◈", color: "#f59e0b", bg: "rgba(245,158,11,0.1)" },
  ];

  const recentAlerts = [
    { id: 1, msg: "AP-Bureau-03 est hors ligne",        time: "Il y a 2 min",  sev: "high" },
    { id: 2, msg: "SW-Core-06 latence élevée (89ms)",   time: "Il y a 5 min",  sev: "warn" },
    { id: 3, msg: "Router-Core-01 redémarré",           time: "Il y a 22 min", sev: "info" },
  ];

  return (
    <div>
      {/* Stats */}
      <div className="stat-grid">
        {stats.map((s) => (
          <div className="stat-card" key={s.label}>
            <div className="stat-icon" style={{ background: s.bg, color: s.color, fontSize: 18 }}>
              {s.icon}
            </div>
            <div className="stat-info">
              <div className="stat-value" style={{ color: s.color }}>{s.value}</div>
              <div className="stat-label">{s.label}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="dashboard-grid">
        {/* Equipment table */}
        <div className="card dash-main">
          <div className="card-head">
            <div>
              <div className="section-title">État des équipements</div>
            </div>
            <button className="btn btn-ghost btn-sm" onClick={simulatePing}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
              </svg>
              Actualiser
            </button>
          </div>
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Nom</th>
                  <th>IP</th>
                  <th>Type</th>
                  <th>Statut</th>
                  <th>Latence</th>
                  <th>Dernière vérif.</th>
                </tr>
              </thead>
              <tbody>
                {equipment.map((eq) => (
                  <tr key={eq.id}>
                    <td><span className="eq-name">{eq.name}</span></td>
                    <td><span className="mono">{eq.ip}</span></td>
                    <td><span className="eq-type">{eq.type}</span></td>
                    <td>
                      <span className={`badge badge-${eq.status === "UP" ? "up" : eq.status === "DOWN" ? "down" : "warn"}`}>
                        <span className={`badge-dot ${eq.status === "UP" ? "pulse" : ""}`}></span>
                        {eq.status}
                      </span>
                    </td>
                    <td>
                      {eq.latency != null ? (
                        <span className={`latency ${eq.latency > 50 ? "high" : ""}`}>
                          {eq.latency} ms
                        </span>
                      ) : (
                        <span className="text-muted">—</span>
                      )}
                    </td>
                    <td><span className="text-muted">{eq.lastCheck}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="refresh-info">
            Dernière actualisation : {lastRefresh.toLocaleTimeString("fr-FR")}
          </div>
        </div>

        {/* Alerts panel */}
        <div className="card dash-side">
          <div className="section-title">Alertes récentes</div>
          <div className="alert-list">
            {recentAlerts.map((a) => (
              <div key={a.id} className={`alert-item alert-${a.sev}`}>
                <div className={`alert-dot alert-dot-${a.sev}`}></div>
                <div className="alert-content">
                  <div className="alert-msg">{a.msg}</div>
                  <div className="alert-time">{a.time}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Mini topology */}
          <div className="topo-section">
            <div className="section-title" style={{ marginTop: 24 }}>Topologie réseau</div>
            <div className="topo-map">
              <div className="topo-node topo-core">
                <div className="topo-icon">⬡</div>
                <div className="topo-label">Core</div>
              </div>
              <div className="topo-branches">
                {["Router", "Switch", "AP", "Srv"].map((n, i) => (
                  <div className="topo-leaf" key={n}>
                    <div className={`topo-dot ${i === 2 ? "dot-down" : i === 3 ? "dot-warn" : "dot-up"}`}></div>
                    <div className="topo-leaf-label">{n}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
