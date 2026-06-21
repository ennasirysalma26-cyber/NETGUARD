import { useState } from "react";
import "./Equipment.css";

const initialEquipment = [
  { id: 1, name: "Router-Core-01", ip: "192.168.1.1",  type: "Routeur",      status: "UP",   latency: 2,   location: "Salle serveur A" },
  { id: 2, name: "SW-Access-02",   ip: "192.168.1.10", type: "Commutateur",  status: "UP",   latency: 1,   location: "Bureau RDC" },
  { id: 3, name: "AP-Bureau-03",   ip: "192.168.1.20", type: "Point d'accès",status: "DOWN", latency: null,location: "Open space" },
  { id: 4, name: "Srv-Web-04",     ip: "10.0.0.5",     type: "Serveur",      status: "UP",   latency: 8,   location: "Datacenter" },
  { id: 5, name: "Router-Edge-05", ip: "10.0.0.1",     type: "Routeur",      status: "UP",   latency: 12,  location: "DMZ" },
  { id: 6, name: "SW-Core-06",     ip: "192.168.2.1",  type: "Commutateur",  status: "WARN", latency: 89,  location: "Salle serveur B" },
];

const empty = { name: "", ip: "", type: "Routeur", location: "" };

export default function Equipment() {
  const [equipment, setEquipment] = useState(initialEquipment);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("Tous");
  const [showModal, setShowModal] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [form, setForm] = useState(empty);
  const [pinging, setPinging] = useState(null);

  const types = ["Tous", "Routeur", "Commutateur", "Point d'accès", "Serveur"];

  const filtered = equipment.filter((e) => {
    const matchSearch = e.name.toLowerCase().includes(search.toLowerCase()) ||
      e.ip.includes(search);
    const matchFilter = filter === "Tous" || e.type === filter;
    return matchSearch && matchFilter;
  });

  const openAdd = () => {
    setEditItem(null);
    setForm(empty);
    setShowModal(true);
  };

  const openEdit = (item) => {
    setEditItem(item);
    setForm({ name: item.name, ip: item.ip, type: item.type, location: item.location });
    setShowModal(true);
  };

  const handleSave = () => {
    if (!form.name || !form.ip) return;
    if (editItem) {
      setEquipment((prev) => prev.map((e) => e.id === editItem.id ? { ...e, ...form } : e));
    } else {
      const newId = Math.max(...equipment.map((e) => e.id)) + 1;
      setEquipment((prev) => [...prev, { id: newId, ...form, status: "UP", latency: null }]);
    }
    setShowModal(false);
  };

  const handleDelete = (id) => {
    setEquipment((prev) => prev.filter((e) => e.id !== id));
  };

  const handlePing = async (id) => {
    setPinging(id);
    await new Promise((r) => setTimeout(r, 1200));
    setEquipment((prev) => prev.map((e) => {
      if (e.id !== id) return e;
      const success = Math.random() > 0.15;
      return {
        ...e,
        status: success ? "UP" : "DOWN",
        latency: success ? Math.floor(Math.random() * 20) + 1 : null,
      };
    }));
    setPinging(null);
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h2 className="page-title">Équipements réseau</h2>
          <p className="page-subtitle">{equipment.length} équipements enregistrés</p>
        </div>
        <button className="btn btn-primary" onClick={openAdd}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          Ajouter équipement
        </button>
      </div>

      {/* Filters */}
      <div className="eq-controls">
        <div className="search-bar">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--text-muted)" }}>
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            placeholder="Rechercher par nom ou IP..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="type-filters">
          {types.map((t) => (
            <button
              key={t}
              className={`filter-btn ${filter === t ? "active" : ""}`}
              onClick={() => setFilter(t)}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="card">
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Équipement</th>
                <th>Adresse IP</th>
                <th>Type</th>
                <th>Localisation</th>
                <th>Statut</th>
                <th>Latence</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((eq) => (
                <tr key={eq.id}>
                  <td><span className="font-medium">{eq.name}</span></td>
                  <td><span className="mono">{eq.ip}</span></td>
                  <td>
                    <span className="type-tag">{eq.type}</span>
                  </td>
                  <td><span style={{ color: "var(--text-secondary)", fontSize: 12 }}>{eq.location}</span></td>
                  <td>
                    <span className={`badge badge-${eq.status === "UP" ? "up" : eq.status === "DOWN" ? "down" : "warn"}`}>
                      <span className={`badge-dot ${eq.status === "UP" ? "pulse" : ""}`}></span>
                      {eq.status}
                    </span>
                  </td>
                  <td>
                    {eq.latency != null
                      ? <span className={`mono ${eq.latency > 50 ? "warn-text" : "up-text"}`}>{eq.latency}ms</span>
                      : <span style={{ color: "var(--text-muted)" }}>—</span>
                    }
                  </td>
                  <td>
                    <div className="actions">
                      <button
                        className="action-btn ping-btn"
                        title="Ping"
                        onClick={() => handlePing(eq.id)}
                        disabled={pinging === eq.id}
                      >
                        {pinging === eq.id
                          ? <span className="spinner-xs"></span>
                          : <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                            </svg>
                        }
                      </button>
                      <button className="action-btn edit-btn" title="Modifier" onClick={() => openEdit(eq)}>
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                        </svg>
                      </button>
                      <button className="action-btn delete-btn" title="Supprimer" onClick={() => handleDelete(eq.id)}>
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="3 6 5 6 21 6"/>
                          <path d="M19 6l-1 14H6L5 6"/>
                          <path d="M10 11v6"/><path d="M14 11v6"/>
                          <path d="M9 6V4h6v2"/>
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filtered.length === 0 && (
            <div className="empty-state">Aucun équipement trouvé.</div>
          )}
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">{editItem ? "Modifier équipement" : "Nouvel équipement"}</h3>
              <button className="close-btn" onClick={() => setShowModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Nom de l'équipement</label>
                <input className="form-input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Ex: Router-Core-01" />
              </div>
              <div className="form-group">
                <label className="form-label">Adresse IP</label>
                <input className="form-input" value={form.ip} onChange={(e) => setForm({ ...form, ip: e.target.value })} placeholder="192.168.1.1" />
              </div>
              <div className="form-group">
                <label className="form-label">Type</label>
                <select className="form-select" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
                  {["Routeur", "Commutateur", "Point d'accès", "Serveur"].map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Localisation</label>
                <input className="form-input" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} placeholder="Ex: Salle serveur A" />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-ghost" onClick={() => setShowModal(false)}>Annuler</button>
              <button className="btn btn-primary" onClick={handleSave}>
                {editItem ? "Enregistrer" : "Ajouter"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
