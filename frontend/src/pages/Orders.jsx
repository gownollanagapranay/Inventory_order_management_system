
import { useEffect, useState } from "react";
import { orderAPI } from "../services/api";

function Orders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const response = await orderAPI.get("/orders/");
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

  if (loading) {
    return <p className="orders-message">Loading your orders...</p>;
  }

  if (error) {
    return <p className="orders-error">{error}</p>;
  }

  return (
    <div className="orders-container">
      <h2>My Orders</h2>

      {orders.length === 0 ? (
        <p className="orders-message">You haven't placed any orders yet.</p>
      ) : (
        <div className="orders-list">
          {orders.map((order) => (
            <div className="order-card" key={order.id}>
              <div className="order-header">
                <div>
                  <h3>Order #{order.id}</h3>
                  <p>
                    {new Date(order.created_at).toLocaleString()}
                  </p>
                </div>
              </div>

              <div className="order-items">
                <h4>Ordered Items</h4>

                {order.items.map((item) => (
                  <div className="order-item" key={item.id}>
                    <span>Product #{item.product_id}</span>
                    <span>Qty: {item.quantity}</span>
                    <span>
                      ₹{Number(item.subtotal).toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>

              <div className="order-details">
                <p>
                  Original Amount: ₹
                  {order.items
                    .reduce(
                      (sum, item) => sum + Number(item.subtotal),
                      0
                    )
                    .toFixed(2)}
                </p>

                {order.coupon_code && (
                  <p>Coupon: {order.coupon_code}</p>
                )}

                <p>
                  Discount: ₹
                  {Number(order.discount_amount || 0).toFixed(2)}
                </p>

                <h3>
                  Total Paid: ₹
                  {Number(order.total_amount).toFixed(2)}
                </h3>

                <p>
                  Payment Status:{" "}
                  <span className={`status ${order.payment_status}`}>
                    {order.payment_status}
                  </span>
                </p>

                <p>
                  Order Status:{" "}
                  <span className={`status ${order.status}`}>
                    {order.status.replaceAll("_", " ")}
                  </span>
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Orders;
