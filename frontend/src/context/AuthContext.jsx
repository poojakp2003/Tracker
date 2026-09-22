import React, { createContext, useContext, useEffect, useState } from "react";
import { getMe, loginUser, logoutUser, signupUser } from "../api/auth";
import { ACCESS_KEY, clearTokens, saveTokens } from "../api/client";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => localStorage.getItem(ACCESS_KEY));
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
          // Only drop the session if the server rejected it, not on a network error
          if (err.response?.status === 401) {
            setToken(null);
            setUser(null);
            clearTokens();
          }
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
    saveTokens(res.access_token, res.refresh_token);
    setToken(res.access_token);
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
      clearTokens();
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