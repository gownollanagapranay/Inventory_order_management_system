
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { orderAPI } from "../services/api";

function PaymentResult() {
  const [searchParams] = useSearchParams();
  const orderId = searchParams.get("order_id");

  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const verifyPayment = async () => {
      if (!orderId) {
        setMessage("Order ID is missing.");
        setLoading(false);
        return;
      }

      try {
        const response = await orderAPI.post(
          `/orders/${orderId}/verify-payment`
        );

        setMessage(response.data.message || "Payment verified successfully.");
      } catch (err) {
        setMessage(
          err.response?.data?.detail || "Payment verification failed."
        );
      } finally {
        setLoading(false);
      }
    };

    verifyPayment();
  }, [orderId]);

  return (
    <div className="checkout-container">
      <div className="checkout-card">
        {loading ? (
          <h2>Verifying your payment...</h2>
        ) : (
          <>
            <h2>Payment Result</h2>
            <p>{message}</p>
            <p>Order ID: {orderId || "Not available"}</p>
            <Link to="/orders" className="checkout-button">
              View My Orders
            </Link>
          </>
        )}
      </div>
    </div>
  );
}

export default PaymentResult;
