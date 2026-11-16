
import { useEffect, useState } from "react";
import { orderAPI } from "../services/api";

function ReturnRequests() {
  const [requests, setRequests] = useState([]);
  const [orderId, setOrderId] = useState("");
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const fetchRequests = async () => {
    try {
      const response = await orderAPI.get("/orders/return-requests");
      setRequests(response.data);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Failed to load return requests."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage("");
    setError("");

    if (!orderId || !reason.trim()) {
      setError("Please enter an order ID and return reason.");
      return;
    }

    try {
      await orderAPI.post(
        `/orders/${orderId}/return-request`,
        { reason: reason.trim() }
      );

      setMessage("Return request submitted successfully!");
      setOrderId("");
      setReason("");

      await fetchRequests();
    } catch (err) {
      setError(
        err.response?.data?.detail || "Failed to submit return request."
      );
    }
  };

  return (
    <div className="return-container">
      <h2>Return Requests</h2>

      <div className="return-form-card">
        <h3>Request a Return</h3>

        <form onSubmit={handleSubmit}>
          <label>Order ID</label>
          <input
            type="number"
            min="1"
            value={orderId}
            onChange={(e) => setOrderId(e.target.value)}
            placeholder="Enter your order ID"
          />

          <label>Reason for Return</label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Explain why you want to return this order"
            rows="4"
          />

          <button type="submit">Submit Return Request</button>
        </form>

        {message && <p className="return-success">{message}</p>}
        {error && <p className="return-error">{error}</p>}
      </div>

      <div className="return-history">
        <h3>My Return History</h3>

        {loading ? (
          <p>Loading return requests...</p>
        ) : requests.length === 0 ? (
          <p>No return requests found.</p>
        ) : (
          requests.map((request) => (
            <div className="return-card" key={request.id}>
              <div>
                <h4>Return Request #{request.id}</h4>
                <p>Order ID: {request.order_id}</p>
                <p>Reason: {request.reason}</p>
                <p>
                  Submitted:{" "}
                  {new Date(request.created_at).toLocaleString()}
                </p>
              </div>

              <span className={`status ${request.status}`}>
                {request.status}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default ReturnRequests;
