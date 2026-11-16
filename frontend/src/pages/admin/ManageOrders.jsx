
import { useEffect, useState } from "react";
import { orderAPI } from "../../services/api";

const statusFlow = {
  confirmed: "processing",
  processing: "shipped",
  shipped: "out_for_delivery",
  out_for_delivery: "delivered",
};

function ManageOrders() {
  const [orders, setOrders] = useState([]);
  const [selectedStatus, setSelectedStatus] = useState({});
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const response = await orderAPI.get("/orders/admin/all");
      setOrders(response.data);
      setError("");
    } catch (err) {
      setError(
        err.response?.data?.detail || "Failed to load orders."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, []);

  const handleStatusChange = (orderId, newStatus) => {
    setSelectedStatus((previous) => ({
      ...previous,
      [orderId]: newStatus,
    }));
  };

  
  const updateOrderStatus = async (orderId, nextStatus) => {
  const newStatus = selectedStatus[orderId] || nextStatus;

  if (!newStatus) {
    setError("No next status available.");
    return;
  }

  try {
    setUpdatingId(orderId);
    setError("");
    setMessage("");

    await orderAPI.patch(
      `/orders/admin/${orderId}/status`,
      { status: newStatus }
    );

    setMessage(
      `Order #${orderId} updated to ${newStatus.replaceAll("_", " ")}.`
    );

    setSelectedStatus((previous) => {
      const updated = { ...previous };
      delete updated[orderId];
      return updated;
    });

    await fetchOrders();
  } catch (err) {
    setError(
      err.response?.data?.detail || "Failed to update order status."
    );
  } finally {
    setUpdatingId(null);
  }
};


  if (loading) {
    return <p style={{ textAlign: "center" }}>Loading orders...</p>;
  }

  return (
    <div className="manage-orders-container">
      <h2>Manage Customer Orders</h2>

      <button onClick={fetchOrders} className="refresh-orders-btn">
        Refresh Orders
      </button>

      {message && <p className="admin-success">{message}</p>}
      {error && <p className="admin-error">{error}</p>}

      {orders.length === 0 ? (
        <p>No orders found.</p>
      ) : (
        <div className="admin-orders-list">
          {orders.map((order) => {
            const nextStatus = statusFlow[order.status];

            return (
              <div className="admin-order-card" key={order.id}>
                <div className="admin-order-header">
                  <h3>Order #{order.id}</h3>
                  <span className={`status ${order.status}`}>
                    {order.status.replaceAll("_", " ")}
                  </span>
                </div>

                <p>Customer ID: {order.user_id}</p>
                <p>
                  Order Date:{" "}
                  {new Date(order.created_at).toLocaleString()}
                </p>
                <p>
                  Payment:{" "}
                  <span className={`status ${order.payment_status}`}>
                    {order.payment_status}
                  </span>
                </p>

                <div className="admin-order-items">
                  <h4>Items</h4>
                  {order.items?.map((item) => (
                    <p key={item.id}>
                      Product #{item.product_id} — Quantity: {item.quantity}
                    </p>
                  ))}
                </div>

                {order.coupon_code && (
                  <p>Coupon: {order.coupon_code}</p>
                )}

                <h4>
                  Total: ₹{Number(order.total_amount).toFixed(2)}
                </h4>

                <div className="status-update-section">
                  <label>Update Delivery Status</label>

                  {nextStatus ? (
                    <>
                      <select
                        value={
                          selectedStatus[order.id] || nextStatus
                        }
                        onChange={(e) =>
                          handleStatusChange(order.id, e.target.value)
                        }
                        disabled={updatingId === order.id}
                      >
                        <option value={nextStatus}>
                          {nextStatus.replaceAll("_", " ")}
                        </option>
                      </select>

                      <button
                       onClick={() => updateOrderStatus(order.id, nextStatus)}
                        disabled={updatingId === order.id}
                      >
                        {updatingId === order.id
                          ? "Updating..."
                          : "Update Status"}
                      </button>
                    </>
                  ) : (
                    <p className="status-completed">
                      {order.status === "delivered"
                        ? "Delivery completed"
                        : "No delivery status update available"}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default ManageOrders;
