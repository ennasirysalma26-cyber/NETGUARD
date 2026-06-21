import { useState } from "react";
import "./Users.css";

const initialUsers = [
  { id: 1, name: "Admin NetGuard", email: "admin@netguard.io",   role: "Administrateur", status: "Actif",   lastLogin: "Il y a 5 min" },
  { id: 2, name: "Sarah Benali",   email: "s.benali@corp.ma",    role: "Opérateur",      status: "Actif",   lastLogin: "Il y a 2h" },
  { id: 3, name: "Youssef Karim",  email: "y.karim@corp.ma",     role: "Superviseur",    status: "Actif",   lastLogin: "Hier 16:40" },
  { id: 4, name: "Leila Mansouri", email: "l.mansouri@corp.ma",  role: "Opérateur",      status: "Inactif", lastLogin: "Il y a 3j" },
];

const roles = ["Administrateur", "Superviseur", "Opérateur"];
const empty = { name: "", email: "", role: "Opérateur", status: "Actif" };

export default function Users() {
  const [users, setUsers] = useState(initialUsers);
  const [showModal, setShowModal] = useState(false);
  const [editUser, setEditUser] = useState(null);
  const [form, setForm] = useState(empty);

  const openAdd = () => {
    setEditUser(null);
    setForm(empty);
    setShowModal(true);
  };

  const openEdit = (user) => {
    setEditUser(user);
    setForm({ name: user.name, email: user.email, role: user.role, status: user.status });
    setShowModal(true);
  };

  const handleSave = () => {
    if (!form.name || !form.email) return;
    if (editUser) {
      setUsers((prev) => prev.map((u) => u.id === editUser.id ? { ...u, ...form } : u));
    } else {
      const newId = Math.max(...users.map((u) => u.id)) + 1;
      setUsers((prev) => [...prev, { id: newId, ...form, lastLogin: "Jamais" }]);
    }
    setShowModal(false);
  };

  const handleDelete = (id) => {
    setUsers((prev) => prev.filter((u) => u.id !== id));
  };

  const toggleStatus = (id) => {
    setUsers((prev) => prev.map((u) =>
      u.id === id ? { ...u, status: u.status === "Actif" ? "Inactif" : "Actif" } : u
    ));
  };

  const roleColors = {
    "Administrateur": { bg: "rgba(37,99,235,0.12)", color: "#60a5fa" },
    "Superviseur":    { bg: "rgba(245,158,11,0.1)", color: "var(--status-warn)" },
    "Opérateur":      { bg: "rgba(16,185,129,0.1)", color: "var(--status-up)" },
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h2 className="page-title">Gestion des utilisateurs</h2>
          <p className="page-subtitle">{users.filter((u) => u.status === "Actif").length} utilisateurs actifs</p>
        </div>
        <button className="btn btn-primary" onClick={openAdd}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          Ajouter utilisateur
        </button>
      </div>

      {/* User cards */}
      <div className="users-grid">
        {users.map((user) => {
          const rc = roleColors[user.role] || roleColors["Opérateur"];
          const initials = user.name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase();
          return (
            <div className="user-card card" key={user.id}>
              <div className="user-card-header">
                <div className="user-card-avatar" style={{ background: `linear-gradient(135deg, ${rc.color}, #7c3aed)` }}>
                  {initials}
                </div>
                <div className={`user-status-dot ${user.status === "Actif" ? "dot-active" : "dot-inactive"}`}></div>
              </div>
              <div className="user-card-name">{user.name}</div>
              <div className="user-card-email">{user.email}</div>
              <div className="user-card-role" style={{ background: rc.bg, color: rc.color }}>
                {user.role}
              </div>
              <div className="user-card-login">Dernière connexion : {user.lastLogin}</div>
              <div className="user-card-actions">
                <button className="btn btn-ghost btn-sm" onClick={() => toggleStatus(user.id)}>
                  {user.status === "Actif" ? "Désactiver" : "Activer"}
                </button>
                <button className="btn btn-ghost btn-sm" onClick={() => openEdit(user)}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                  </svg>
                </button>
                <button className="btn btn-danger btn-sm" onClick={() => handleDelete(user.id)}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6l-1 14H6L5 6"/><path d="M9 6V4h6v2"/>
                  </svg>
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">{editUser ? "Modifier utilisateur" : "Nouvel utilisateur"}</h3>
              <button className="close-btn" onClick={() => setShowModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Nom complet</label>
                <input className="form-input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Prénom Nom" />
              </div>
              <div className="form-group">
                <label className="form-label">Email</label>
                <input type="email" className="form-input" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="email@corp.ma" />
              </div>
              <div className="form-group">
                <label className="form-label">Rôle</label>
                <select className="form-select" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                  {roles.map((r) => <option key={r} value={r}>{r}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Statut</label>
                <select className="form-select" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                  <option value="Actif">Actif</option>
                  <option value="Inactif">Inactif</option>
                </select>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-ghost" onClick={() => setShowModal(false)}>Annuler</button>
              <button className="btn btn-primary" onClick={handleSave}>
                {editUser ? "Enregistrer" : "Créer"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
