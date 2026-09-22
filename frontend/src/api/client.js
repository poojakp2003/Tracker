import axios from "axios";

const API_BASE_URL = "http://localhost:8000"; // or relative proxy

export const ACCESS_KEY = "tracker_access_token";
export const REFRESH_KEY = "tracker_refresh_token";

export const saveTokens = (accessToken, refreshToken) => {
  if (accessToken) localStorage.setItem(ACCESS_KEY, accessToken);
  if (refreshToken) localStorage.setItem(REFRESH_KEY, refreshToken);
};

export const clearTokens = () => {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
};

// Create shared Axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request Interceptor: Automatically attach JWT Bearer token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(ACCESS_KEY);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Single-flight refresh: if several requests fail at once, only one refresh call is made
let refreshPromise = null;

const refreshAccessToken = () => {
  if (!refreshPromise) {
    const refreshToken = localStorage.getItem(REFRESH_KEY);
    if (!refreshToken) {
      return Promise.reject(new Error("NO_REFRESH_TOKEN"));
    }
    // Plain axios (not apiClient) so this call never re-enters the interceptor
    refreshPromise = axios
      .post(`${API_BASE_URL}/auth/refresh`, { refresh_token: refreshToken })
      .then((res) => {
        saveTokens(res.data.access_token, res.data.refresh_token);
        return res.data.access_token;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
};

const isAuthEndpoint = (url = "") =>
  url.includes("/auth/login") ||
  url.includes("/auth/signup") ||
  url.includes("/auth/refresh");

const redirectToLogin = () => {
  // Prevent infinite loop if already on /login or /signup
  if (
    !window.location.pathname.includes("/login") &&
    !window.location.pathname.includes("/signup")
  ) {
    window.location.href = "/login?session_expired=true";
  }
};

// Response Interceptor: on 401, refresh once and retry the original request
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const status = error.response?.status;

    if (
      status !== 401 ||
      !original ||
      original._retry ||
      original.skipAuthRefresh ||
      isAuthEndpoint(original.url)
    ) {
      return Promise.reject(error);
    }

    original._retry = true;

    try {
      const newToken = await refreshAccessToken();
      original.headers.Authorization = `Bearer ${newToken}`;
      return apiClient(original);
    } catch (refreshError) {
      // Only end the session if it is really dead, not on a temporary network error
      const refreshStatus = refreshError.response?.status;
      const sessionDead =
        refreshError.message === "NO_REFRESH_TOKEN" ||
        [400, 401, 403].includes(refreshStatus);

      if (sessionDead) {
        clearTokens();
        redirectToLogin();
      }
      return Promise.reject(refreshError);
    }
  }
);

export default apiClient;