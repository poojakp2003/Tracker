import axios from "axios";

// Create shared Axios instance
const apiClient = axios.create({
  baseURL: "http://localhost:8000", // or relative proxy
  headers: {
    "Content-Type": "application/json",
  },
});

// Request Interceptor: Automatically attach JWT Bearer token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("tracker_access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor: Handle 401 Unauthorized globally
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Token is expired, invalid, or missing
      localStorage.removeItem("tracker_access_token");
      // Prevent infinite loop if already on /login or /signup
      if (
        !window.location.pathname.includes("/login") &&
        !window.location.pathname.includes("/signup")
      ) {
        window.location.href = "/login?session_expired=true";
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
