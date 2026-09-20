import apiClient from "./client";

export const getDashboardSummary = async () => {
  const response = await apiClient.get("/dashboard/summary");
  return response.data;
};

export const getDashboardApps = async (range = "7d") => {
  const response = await apiClient.get(`/dashboard/apps?range=${range}`);
  return response.data;
};

export const getDashboardBrowser = async (range = "7d") => {
  const response = await apiClient.get(`/dashboard/browser?range=${range}`);
  return response.data;
};

export const getDashboardYouTube = async (range = "7d") => {
  const response = await apiClient.get(`/dashboard/youtube?range=${range}`);
  return response.data;
};

export const getDashboardTimeline = async (range = "7d") => {
  const response = await apiClient.get(`/dashboard/timeline?range=${range}`);
  return response.data;
};

export const getDashboardBrowserHistory = async (range = "7d", limit = 50) => {
  const response = await apiClient.get(`/dashboard/browser-history?range=${range}&limit=${limit}`);
  return response.data;
};

