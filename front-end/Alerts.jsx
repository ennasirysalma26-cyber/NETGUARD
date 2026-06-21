import { useState } from "react";
import "./Alerts.css";

const allAlerts = [
  { id: 1,  eq: "AP-Bureau-03",   event: "Équipement hors ligne",          sev: "critical", time: "2025-01-15 14:32:10", resolved: false },
  { id: 2,  eq: "SW-Core-06",     event: "Latence élevée détectée (89ms)", sev: "warning",  time: "2025-01-15 14:28:44", resolved: false },
  { id: 3,  eq: "Router-Core-01", event: "Redémarrage détecté",            sev: "info",     time: "2025-01-15 14:05:02", resolved: true },
  { id: 4,  eq: "Srv-Web-04",     event: "Équipement de nouveau en ligne", sev: "info",     time: "2025-01-15 12:10:55", resolved: true },
  { id: 5,  eq: "Router-Edge-05", event: "Perte de paquets (12%)",         sev: "warning",  time: "2025-01-15 10:44:18", resolved: true },
  { id: 6,  eq: "AP-Bureau-03",   event: "Équipement hors ligne",          sev: "critical", time: "2025-01-14 22:15:07", resolved: true },
  { id: 7,  eq: "SW-Access-02",   event: "Latence élevée détectée (54ms)", sev: "warning",  time: "2025-01-14 18:33:21", resolved: true },
  { id: 8,  eq: "Router-Core-01", event: "Équipement de nouveau en ligne", sev: "info",     time: "2025-01-14 09:00:05", resolved: true },
];

const sevConfig = {
  critical: { label: "Critique", color: "var(--status-down)", bg: "var(--status-down-bg)", badge: "badge-down" },
  warning:  { label: "Avertissement", color: "var(--status-warn)", bg: "var(--status-warn-bg)", badge: "badge-warn" },
  info:     { label: "Information", color: "var(--accent)", bg: "rgba(37,99,235,0.08)", badge: "badge-info" },
};

export default function Alerts() {
  const [filterSev, setFilterSev] = useState("Tous");
  const [filterStatus, setFilterStatus] = useState("Tous");
  const [alerts, setAlerts] = useState(allAlerts);

  const filtered = alerts.filter((a) => {
    const matchSev = filterSev === "Tous" || a.sev === filterSev.toLowerCase();
    const matchStatus = filterStatus === "Tous"
      || (filterStatus === "Active" && !a.resolved)
      || (filterStatus === "Résolue" && a.resolved);
    return matchSev && matchStatus;
  });

  const resolve = (id) => {
    setAlerts((prev) => prev.map((a) => a.id === id ? { ...a, resolved: true } : a));
  };

  const stats = {
    total: alerts.length,
    active: alerts.filter((a) => !a.resolved).length,
    critical: alerts.filter((a) => a.sev === "critical").length,
    warning: alerts.filter((a) => a.sev === "warning").length,
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h2 className="page-title">Alertes & Historique</h2>
          <p className="page-subtitle">{stats.active} alertes actives</p>
        </div>
      </div>

      {/* Stats */}
      <div className="alert-stats">
        {[
          { label: "Total",      value: stats.total,    color: "var(--accent)" },
          { label: "Actives",    value: stats.active,   color: "var(--status-down)" },
          { label: "Critiques",  value: stats.critical, color: "var(--status-down)" },
          { label: "Avert.",     value: stats.warning,  color: "var(--status-warn)" },
        ].map((s) => (
          <div className="alert-stat-card card" key={s.label}>
            <div className="alert-stat-value" style={{ color: s.color }}>{s.value}</div>
            <div className="alert-stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="alert-filters">
        <div className="filter-group">
          <span className="filter-label">Sévérité :</span>
          {["Tous", "Critical", "Warning", "Info"].map((s) => (
            <button key={s} className={`filter-btn ${filterSev === s ? "active" : ""}`}
              onClick={() => setFilterSev(s)}>{s}</button>
          ))}
        </div>
        <div className="filter-group">
          <span className="filter-label">Statut :</span>
          {["Tous", "Active", "Résolue"].map((s) => (
            <button key={s} className={`filter-btn ${filterStatus === s ? "active" : ""}`}
              onClick={() => setFilterStatus(s)}>{s}</button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="card">
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Sévérité</th>
                <th>Équipement</th>
                <th>Événement</th>
                <th>Date / Heure</th>
                <th>Statut</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((alert) => {
                const cfg = sevConfig[alert.sev];
                return (
                  <tr key={alert.id}>
                    <td>
                      <span className={`badge ${cfg.badge}`}>
                        <span className="badge-dot"></span>
                        {cfg.label}
                      </span>
                    </td>
                    <td><span className="font-medium">{alert.eq}</span></td>
                    <td style={{ fontSize: 13 }}>{alert.event}</td>
                    <td><span className="mono">{alert.time}</span></td>
                    <td>
                      {alert.resolved
                        ? <span className="resolved-tag">Résolue</span>
                        : <span className="active-tag">Active</span>
                      }
                    </td>
                    <td>
                      {!alert.resolved && (
                        <button className="btn btn-ghost btn-sm" onClick={() => resolve(alert.id)}>
                          Résoudre
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {filtered.length === 0 && (
            <div className="empty-state">Aucune alerte pour ces filtres.</div>
          )}
        </div>
      </div>
    </div>
  );
}
