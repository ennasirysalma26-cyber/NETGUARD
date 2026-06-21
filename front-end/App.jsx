import { useState } from "react";

import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from "react-router-dom";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Equipment from "./pages/Equipment";
import Alerts from "./pages/Alerts";
import Users from "./pages/Users";
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import "./global.css";

const ProtectedRoute = ({ isAuthenticated, children }) => {
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

const AppLayout = ({ currentUser, handleLogout }) => {
  return (
    <div className="app-layout">
      <Sidebar /> 
      <div className="main-content">
        <Header user={currentUser} onLogout={handleLogout} />
        <div className="page-content">
          

          
          <Outlet /> 
        </div>
      </div>
    </div>
  );
};

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);

  const handleLogin = (user) => {
    setCurrentUser(user);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    setCurrentUser(null);
    setIsAuthenticated(false);
  };

  return (
    <Router>
      <Routes>
        
        <Route path="/login" element={
          isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login onLogin={handleLogin} />
        } />

        
        <Route path="/" element={
          <ProtectedRoute isAuthenticated={isAuthenticated}>
            <AppLayout currentUser={currentUser} handleLogout={handleLogout} />
          </ProtectedRoute>
        }>
        
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="equipment" element={<Equipment />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="users" element={<Users />} />
          
         
          <Route index element={<Navigate to="/dashboard" replace />} />
        </Route>


        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}