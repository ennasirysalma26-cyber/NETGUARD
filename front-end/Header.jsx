import "./Header.css";

const pageLabels = {
  dashboard: "Tableau de bord",
  equipment: "Équipements réseau",
  alerts: "Alertes & Historique",
  users: "Gestion utilisateurs",
};

export default function Header({ user, onLogout, activePage }) {
  const now = new Date().toLocaleString("fr-FR", {
    weekday: "long", day: "numeric", month: "long",
    hour: "2-digit", minute: "2-digit"
  });

  return (
    <header className="header">
      <div className="header-left">
        <div>
          <h1 className="header-title">{pageLabels[activePage]}</h1>
          <p className="header-date">{now}</p>
        </div>
      </div>

      <div className="header-right">
        <div className="live-indicator">
          <span className="live-dot"></span>
          <span className="live-text">Live</span>
        </div>

        <button className="notif-btn" title="Notifications">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
          <span className="notif-count">3</span>
        </button>

        <div className="user-menu">
          <div className="user-avatar">
            {user?.name?.charAt(0).toUpperCase() || "A"}
          </div>
          <div className="user-info">
            <div className="user-name">{user?.name || "Administrateur"}</div>
            <div className="user-role">{user?.role || "Admin"}</div>
          </div>
          <button className="logout-btn" onClick={onLogout} title="Déconnexion">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
}
