
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { orderAPI } from "../../services/api";

function AdminDashboard() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchSummary = async () => {
    try {
      setLoading(true);
      const response = await orderAPI.get("/orders/admin/sales-summary");
      setSummary(response.data);
      setError("");
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Failed to load dashboard statistics."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const stats = [
    {
      title: "Total Orders",
      value: summary?.total_orders ?? 0,
    },
    {
      title: "Paid Orders",
      value: summary?.total_paid_orders ?? 0,
    },
    {
      title: "Total Revenue",
      value: `₹${Number(summary?.total_revenue ?? 0).toFixed(2)}`,
    },
    {
      title: "Pending Orders",
      value: summary?.pending_orders ?? 0,
    },
    {
      title: "Delivered Orders",
      value: summary?.delivered_orders ?? 0,
    },
    {
      title: "Cancelled Orders",
      value: summary?.cancelled_orders ?? 0,
    },
  ];

  return (
    <div className="admin-dashboard">
      <h2>Admin Dashboard</h2>
      <p>Welcome to the Inventory Management Admin Panel.</p>

      <div className="admin-dashboard-links">
        <Link to="/admin/manage-products">
          Manage Products
        </Link>

        <Link to="/admin/manage-orders">
          Manage Orders
        </Link>

        <Link to="/admin/manage-returns">
          Manage Return Requests
        </Link>
      </div>

      <div className="dashboard-heading">
        <h3>Sales Overview</h3>
        <button onClick={fetchSummary}>Refresh Statistics</button>
      </div>

      {loading ? (
        <p>Loading dashboard statistics...</p>
      ) : error ? (
        <p className="admin-error">{error}</p>
      ) : (
        <div className="dashboard-stats">
          {stats.map((stat) => (
            <div className="dashboard-stat-card" key={stat.title}>
              <h4>{stat.title}</h4>
              <h2>{stat.value}</h2>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default AdminDashboard;
