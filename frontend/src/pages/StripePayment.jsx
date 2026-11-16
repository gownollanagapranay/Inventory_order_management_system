
import { useEffect, useRef, useState } from "react";
import { loadStripe } from "@stripe/stripe-js";
import {
  Elements,
  PaymentElement,
  useElements,
  useStripe,
} from "@stripe/react-stripe-js";
import { orderAPI } from "../services/api";

const stripePromise = loadStripe(
  import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY
);

function PaymentForm({ orderId }) {
  const stripe = useStripe();
  const elements = useElements();

  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handlePayment = async (e) => {
    e.preventDefault();

    if (!stripe || !elements) return;

    try {
      setProcessing(true);
      setError("");

      const result = await stripe.confirmPayment({
        elements,
        confirmParams: {
          return_url: `${window.location.origin}/payment-result?order_id=${orderId}`,
        },
        redirect: "if_required",
      });

      if (result.error) {
        setError(result.error.message || "Payment failed.");
        return;
      }

      if (result.paymentIntent?.status === "succeeded") {
        const response = await orderAPI.post(
          `/orders/${orderId}/verify-payment`
        );

        setSuccess(true);
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Unable to complete payment."
      );
    } finally {
      setProcessing(false);
    }
  };

  if (success) {
    return (
      <div className="payment-success">
        <h3>Payment Successful!</h3>
        <p>Your payment has been verified.</p>
        <p>Order ID: {orderId}</p>
      </div>
    );
  }

  return (
    <form onSubmit={handlePayment} className="payment-form">
      <h3>Payment Details</h3>

      <PaymentElement />

      {error && <p className="checkout-error">{error}</p>}

      <button
        type="submit"
        className="checkout-button"
        disabled={!stripe || !elements || processing}
      >
        {processing ? "Processing Payment..." : "Pay Now"}
      </button>
    </form>
  );
}

function StripePayment({ order }) {
  const [clientSecret, setClientSecret] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    const createPaymentIntent = async () => {
      try {
        const response = await orderAPI.post(
          `/orders/${order.id}/payment`
        );

        setClientSecret(response.data.client_secret);
      } catch (err) {
        setError(
          err.response?.data?.detail ||
            "Unable to initialize payment."
        );
      } finally {
        setLoading(false);
      }
    };

    createPaymentIntent();
  }, [order.id]);

  if (loading) {
    return <p>Initializing secure payment...</p>;
  }

  if (error) {
    return <p className="checkout-error">{error}</p>;
  }

  if (!clientSecret) {
    return <p className="checkout-error">Payment could not be initialized.</p>;
  }

  return (
    <div className="stripe-payment-container">
      <p>
        <strong>Amount to pay:</strong>{" "}
        ₹{Number(order.total_amount).toFixed(2)}
      </p>

      <Elements
        stripe={stripePromise}
        options={{ clientSecret }}
      >
        <PaymentForm orderId={order.id} />
      </Elements>
    </div>
  );
}

export default StripePayment;
