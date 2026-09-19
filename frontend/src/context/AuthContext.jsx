import React, { createContext, useContext, useEffect, useState } from "react";
import { getMe, loginUser, logoutUser, signupUser } from "../api/auth";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => localStorage.getItem("tracker_access_token"));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch current user on mount or token change
  useEffect(() => {
    const fetchUser = async () => {
      if (token) {
        try {
          const userData = await getMe();
          setUser(userData);
        } catch (err) {
          console.error("Failed to load user info:", err);
          setToken(null);
          setUser(null);
          localStorage.removeItem("tracker_access_token");
        }
      } else {
        setUser(null);
      }
      setLoading(false);
    };

    fetchUser();
  }, [token]);

  const login = async (email, password) => {
    const res = await loginUser(email, password);
    const accessToken = res.access_token;
    localStorage.setItem("tracker_access_token", accessToken);
    setToken(accessToken);
    const userData = await getMe();
    setUser(userData);
    return userData;
  };

  const signup = async (email, password) => {
    await signupUser(email, password);
    // After successful signup, immediately log in
    return await login(email, password);
  };

  const logout = async () => {
    try {
      await logoutUser();
    } catch (e) {
      console.warn("Logout API returned error or already expired", e);
    } finally {
      localStorage.removeItem("tracker_access_token");
      setToken(null);
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        isAuthenticated: !!token,
        loading,
        login,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
