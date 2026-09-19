import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Activity, LayoutDashboard, LogOut, Settings, User as UserIcon } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export const Navbar = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <header className="navbar">
      <div style={{ display: "flex", alignItems: "center", gap: "32px" }}>
        <Link to="/dashboard" className="nav-brand">
          <div style={{
            width: "32px",
            height: "32px",
            borderRadius: "8px",
            background: "linear-gradient(135deg, #06B6D4, #8B5CF6)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 0 12px rgba(6, 182, 212, 0.4)",
          }}>
            <Activity size={18} color="#FFFFFF" />
          </div>
          <span>Track<span className="nav-brand-gradient">Pulse</span></span>
        </Link>

        <nav className="nav-links">
          <Link
            to="/dashboard"
            className={`nav-link ${location.pathname === "/dashboard" ? "active" : ""}`}
            style={{ display: "flex", alignItems: "center", gap: "6px" }}
          >
            <LayoutDashboard size={16} />
            <span>Dashboard</span>
          </Link>
          <Link
            to="/settings"
            className={`nav-link ${location.pathname === "/settings" ? "active" : ""}`}
            style={{ display: "flex", alignItems: "center", gap: "6px" }}
          >
            <Settings size={16} />
            <span>Settings</span>
          </Link>
        </nav>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
        {user && (
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: "6px 12px",
            background: "rgba(255, 255, 255, 0.04)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "9999px",
            fontSize: "0.85rem",
            color: "var(--text-secondary)",
          }}>
            <UserIcon size={14} color="var(--primary)" />
            <span>{user.email}</span>
          </div>
        )}

        <button
          onClick={handleLogout}
          className="btn btn-secondary"
          style={{ padding: "8px 14px", fontSize: "0.85rem" }}
          title="Sign out"
        >
          <LogOut size={15} />
          <span>Logout</span>
        </button>
      </div>
    </header>
  );
};
