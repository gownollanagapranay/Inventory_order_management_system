
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { orderAPI, productAPI } from "../services/api";
import "./Checkout.css";
import StripePayment from "./StripePayment";

function Checkout() {
  const [cartItems, setCartItems] = useState([]);
  const [products, setProducts] = useState([]);
  const [couponCode, setCouponCode] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [order, setOrder] = useState(null);

  useEffect(() => {
    fetchCheckoutData();
  }, []);

  const fetchCheckoutData = async () => {
    try {
      setLoading(true);
      setError("");

      const [cartResponse, productsResponse] = await Promise.all([
        orderAPI.get("/cart/"),
        productAPI.get("/products/"),
      ]);

      setCartItems(cartResponse.data);
      setProducts(productsResponse.data);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Unable to load checkout details."
      );
    } finally {
      setLoading(false);
    }
  };

  const getProduct = (productId) => {
    return products.find((product) => product.id === productId);
  };

  const subtotal = cartItems.reduce((total, item) => {
    const product = getProduct(item.product_id);
    return total + (product ? product.price * item.quantity : 0);
  }, 0);

  const handleCheckout = async (e) => {
    e.preventDefault();

    try {
      setSubmitting(true);
      setError("");

      const response = await orderAPI.post("orders/checkout", {
        coupon_code: couponCode.trim() || null,
      });

      setOrder(response.data);
      setCartItems([]);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Checkout failed. Please try again."
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <p className="checkout-message">Loading checkout...</p>;
  }

  // Show the created order after successful checkout.
  if (order) {
    return (
      <div className="checkout-container">
        <div className="checkout-card">
          <h2>Order Created Successfully!</h2>
          <p>Your order has been created. Payment is still pending.</p>

          <div className="order-details">
            <p><strong>Order ID:</strong> {order.id}</p>
            <p>
              <strong>Order Amount:</strong>{" "}
              ₹{Number(order.total_amount).toFixed(2)}
            </p>
            <p>
              <strong>Discount:</strong>{" "}
              ₹{Number(order.discount_amount || 0).toFixed(2)}
            </p>
            <p><strong>Payment Status:</strong> {order.payment_status}</p>
            <p><strong>Order Status:</strong> {order.status}</p>
          </div>

          <StripePayment order={order} />

          <Link to="/orders" className="checkout-button">
            View My Orders
          </Link>
        </div>
      </div>
    );
  }

  if (cartItems.length === 0) {
    return (
      <div className="checkout-container">
        <div className="checkout-card">
          <h2>Your cart is empty</h2>
          <Link to="/products" className="checkout-button">
            Continue Shopping
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="checkout-container">
      <div className="checkout-card">
        <h2>Checkout</h2>

        {error && <p className="checkout-error">{error}</p>}

        <h3>Order Summary</h3>

        <div className="checkout-items">
          {cartItems.map((item) => {
            const product = getProduct(item.product_id);

            return (
              <div className="checkout-item" key={item.id}>
                <div>
                  <strong>
                    {product?.name || `Product #${item.product_id}`}
                  </strong>
                  <p>Quantity: {item.quantity}</p>
                </div>

                <strong>
                  ₹
                  {product
                    ? (product.price * item.quantity).toFixed(2)
                    : "0.00"}
                </strong>
              </div>
            );
          })}
        </div>

        <div className="checkout-total">
          <strong>Subtotal</strong>
          <strong>₹{subtotal.toFixed(2)}</strong>
        </div>

        <form onSubmit={handleCheckout}>
          <label htmlFor="couponCode">Coupon Code (Optional)</label>

          <input
            id="couponCode"
            type="text"
            value={couponCode}
            onChange={(e) => setCouponCode(e.target.value)}
            placeholder="Enter coupon code"
          />

          <button
            type="submit"
            className="checkout-button"
            disabled={submitting}
          >
            {submitting ? "Creating Order..." : "Place Order"}
          </button>
        </form>

        <Link to="/cart" className="back-to-cart">
          Back to Cart
        </Link>
      </div>
    </div>
  );
}

export default Checkout;
