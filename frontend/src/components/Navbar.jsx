
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function Navbar() {
  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="navbar">
      <Link to="/products" className="navbar-brand">
        Inventory System
      </Link>

      <div className="navbar-links">
        <Link to="/products">Products</Link>
        <Link to="/cart">Cart</Link>
        <Link to="/orders">My Orders</Link>
        <Link to="/return-requests">Returns</Link>

        {isAdmin && (
          <Link to="/admin">Admin Dashboard</Link>
        )}
      </div>

      <div className="navbar-user">
        <span>
          {user?.name} ({user?.role})
        </span>

        <button onClick={handleLogout}>
          Logout
        </button>
      </div>
    </nav>
  );
}

export default Navbar;
