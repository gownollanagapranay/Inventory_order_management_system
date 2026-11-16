
import { useEffect, useState } from "react";
import { orderAPI } from "../../services/api";

function ManageReturns() {
  const [returns, setReturns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchReturns = async () => {
    try {
      setLoading(true);
      const response = await orderAPI.get(
        "/orders/return-requests/admin/all"
      );
      setReturns(response.data);
      setError("");
    } catch (err) {
      setError(
        err.response?.data?.detail || "Failed to load return requests."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReturns();
  }, []);

  const updateReturnStatus = async (requestId, status) => {
    try {
      await orderAPI.patch(
        `/orders/return-requests/admin/${requestId}`,
        { status }
      );

      alert(`Return request ${status} successfully!`);
      fetchReturns();
    } catch (err) {
      alert(
        err.response?.data?.detail || "Failed to update return request."
      );
    }
  };

  return (
    <div className="admin-page">
      <h2>Manage Return Requests</h2>

      <button onClick={fetchReturns}>Refresh Requests</button>

      {loading ? (
        <p>Loading return requests...</p>
      ) : error ? (
        <p className="admin-error">{error}</p>
      ) : returns.length === 0 ? (
        <p>No return requests found.</p>
      ) : (
        <div className="admin-return-list">
          {returns.map((request) => (
            <div className="admin-return-card" key={request.id}>
              <h4>Return Request #{request.id}</h4>
              <p>Order ID: {request.order_id}</p>
              <p>Customer ID: {request.user_id}</p>
              <p>Reason: {request.reason}</p>
              <p>
                Status: <strong>{request.status}</strong>
              </p>
              <p>
                Created:{" "}
                {new Date(request.created_at).toLocaleString()}
              </p>

              {request.status === "pending" && (
                <div className="return-actions">
                  <button
                    onClick={() =>
                      updateReturnStatus(request.id, "approved")
                    }
                  >
                    Approve
                  </button>

                  <button
                    className="danger-button"
                    onClick={() =>
                      updateReturnStatus(request.id, "rejected")
                    }
                  >
                    Reject
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ManageReturns;
