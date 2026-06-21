import { useState } from "react";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Equipment from "./pages/Equipment";
import Alerts from "./pages/Alerts";
import Users from "./pages/Users";
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import "./styles/global.css";

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [activePage, setActivePage] = useState("dashboard");

  const handleLogin = (user) => {
    setCurrentUser(user);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    setCurrentUser(null);
    setIsAuthenticated(false);
    setActivePage("dashboard");
  };

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  const renderPage = () => {
    switch (activePage) {
      case "dashboard": return <Dashboard />;
      case "equipment": return <Equipment />;
      case "alerts": return <Alerts />;
      case "users": return <Users />;
      default: return <Dashboard />;
    }
  };

  return (
    <div className="app-layout">
      <Sidebar activePage={activePage} onNavigate={setActivePage} />
      <div className="main-content">
        <Header user={currentUser} onLogout={handleLogout} activePage={activePage} />
        <div className="page-content">
          {renderPage()}
        </div>
      </div>
    </div>
  );
}
