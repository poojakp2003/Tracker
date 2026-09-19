import apiClient from "./client";

export const getPermissions = async () => {
  const response = await apiClient.get("/track/permissions");
  return response.data;
};

export const updatePermissions = async (data) => {
  const response = await apiClient.put("/track/permissions", data);
  return response.data;
};
