
import axios from "axios";

// Backend service URLs
const AUTH_URL = "http://localhost:8001";
const PRODUCT_URL = "http://localhost:8002";
const ORDER_URL = "http://localhost:8003";

// Create Axios instances
const authAPI = axios.create({
  baseURL: AUTH_URL,
});

const productAPI = axios.create({
  baseURL: PRODUCT_URL,
});

const orderAPI = axios.create({
  baseURL: ORDER_URL,
});

// Attach JWT token to requests automatically
const addToken = (config) => {
  const token = localStorage.getItem("access_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
};

// Apply token interceptor to all services
authAPI.interceptors.request.use(addToken);
productAPI.interceptors.request.use(addToken);
orderAPI.interceptors.request.use(addToken);

// Export API clients
export { authAPI, productAPI, orderAPI };
