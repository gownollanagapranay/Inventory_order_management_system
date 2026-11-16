
import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

import { authAPI } from "../services/api";

// Create authentication context
const AuthContext = createContext(null);

// Provider component
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Load existing login session when application starts
  useEffect(() => {
    const loadUser = async () => {
      const token = localStorage.getItem("access_token");

      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const response = await authAPI.get("/auth/me");
        setUser(response.data);
      } catch (error) {
        localStorage.removeItem("access_token");
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    loadUser();
  }, []);

  // Register new user
  const register = async (name, email, password) => {
    const response = await authAPI.post("/auth/register", {
      name,
      email,
      password,
    });

    return response.data;
  };

  // Login existing user
  const login = async (email, password) => {
    const response = await authAPI.post("/auth/login", {
      email,
      password,
    });

    const token = response.data.access_token;

    // Save JWT token
    localStorage.setItem("access_token", token);

    try {
      // Fetch logged-in user's profile
      const profileResponse = await authAPI.get("/auth/me");

      setUser(profileResponse.data);

      return profileResponse.data;
    } catch (error) {
      localStorage.removeItem("access_token");
      setUser(null);
      throw error;
    }
  };

  // Logout user
  const logout = () => {
    localStorage.removeItem("access_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        register,
        login,
        logout,
        isAuthenticated: !!user,
        isAdmin: user?.role === "admin",
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook to access authentication
export function useAuth() {
  return useContext(AuthContext);
}
