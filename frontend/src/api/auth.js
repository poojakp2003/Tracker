import apiClient from "./client";

export const loginUser = async (email, password) => {
  const response = await apiClient.post("/auth/login", { email, password });
  return response.data;
};

export const signupUser = async (email, password) => {
  const response = await apiClient.post("/auth/signup", { email, password });
  return response.data;
};

export const getMe = async () => {
  const response = await apiClient.get("/auth/me");
  return response.data;
};

export const logoutUser = async () => {
  try {
    await apiClient.post("/auth/logout");
  } finally {
    localStorage.removeItem("tracker_access_token");
  }
};
