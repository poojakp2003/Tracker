import apiClient from "./client";
 
export const getPermissions = async () => {
  const response = await apiClient.get("/permissions");
  return response.data;
};
 
export const updatePermissions = async (data) => {
  const response = await apiClient.put("/permissions", data);
  return response.data;
};

