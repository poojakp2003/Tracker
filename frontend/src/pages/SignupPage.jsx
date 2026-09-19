import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Activity, AlertCircle, ArrowRight, Lock, Mail } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export const SignupPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const { signup } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      await signup(email, password);
      navigate("/dashboard");
    } catch (err) {
      console.error(err);
      const detail = err.response?.data?.detail || "Registration failed. Email might already be taken.";
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "20px",
    }}>
      <div className="glass-card animate-fade-in" style={{
        width: "100%",
        maxWidth: "420px",
        padding: "36px 32px",
      }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "28px" }}>
          <div style={{
            width: "48px",
            height: "48px",
            borderRadius: "14px",
            background: "linear-gradient(135deg, #8B5CF6, #06B6D4)",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 0 20px rgba(139, 92, 246, 0.4)",
            marginBottom: "16px",
          }}>
            <Activity size={26} color="#FFFFFF" />
          </div>
          <h1 style={{ fontSize: "1.75rem", marginBottom: "6px" }}>Create account</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
            Start monitoring your productivity and focus
          </p>
        </div>

        {error && (
          <div style={{
            padding: "10px 14px",
            background: "rgba(244, 63, 94, 0.15)",
            border: "1px solid rgba(244, 63, 94, 0.3)",
            borderRadius: "var(--radius-sm)",
            color: "#FB7185",
            fontSize: "0.85rem",
            marginBottom: "18px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <label className="input-label" htmlFor="email">Email address</label>
            <div style={{ position: "relative" }}>
              <Mail size={16} color="var(--text-muted)" style={{ position: "absolute", left: "14px", top: "15px" }} />
              <input
                id="email"
                type="email"
                required
                className="input-field"
                style={{ paddingLeft: "42px" }}
                placeholder="name@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>

          <div className="input-group">
            <label className="input-label" htmlFor="password">Password (min 8 chars)</label>
            <div style={{ position: "relative" }}>
              <Lock size={16} color="var(--text-muted)" style={{ position: "absolute", left: "14px", top: "15px" }} />
              <input
                id="password"
                type="password"
                required
                minLength={8}
                className="input-field"
                style={{ paddingLeft: "42px" }}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <div className="input-group">
            <label className="input-label" htmlFor="confirm-password">Confirm Password</label>
            <div style={{ position: "relative" }}>
              <Lock size={16} color="var(--text-muted)" style={{ position: "absolute", left: "14px", top: "15px" }} />
              <input
                id="confirm-password"
                type="password"
                required
                minLength={8}
                className="input-field"
                style={{ paddingLeft: "42px" }}
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary"
            style={{ width: "100%", marginTop: "10px" }}
          >
            {loading ? "Creating account..." : "Sign Up"}
            {!loading && <ArrowRight size={16} />}
          </button>
        </form>

        {/* Footer */}
        <div style={{ textAlign: "center", marginTop: "24px", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
          Already have an account?{" "}
          <Link to="/login" style={{ fontWeight: 600 }}>Sign in</Link>
        </div>
      </div>
    </div>
  );
};
