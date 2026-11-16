
import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function ProtectedRoute({ adminOnly = false }) {
  const { user, loading } = useAuth();

  // Wait until authentication check is completed
  if (loading) {
    return <p style={{ textAlign: "center", marginTop: "50px" }}>
      Checking authentication...
    </p>;
  }

  // Redirect unauthenticated users
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Prevent customers from accessing admin pages
  if (adminOnly && user.role !== "admin") {
    return <Navigate to="/products" replace />;
  }

  return <Outlet />;
}

export default ProtectedRoute;
