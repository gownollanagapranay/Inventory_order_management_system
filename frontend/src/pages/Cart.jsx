
import { useEffect, useState } from "react";
import { orderAPI, productAPI } from "../services/api";
import { useNavigate } from "react-router-dom";

function Cart() {
  const navigate = useNavigate();

  const [cartItems, setCartItems] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  // Fetch cart and product details
  const fetchCart = async () => {
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
        err.response?.data?.detail || "Unable to load cart."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCart();
  }, []);

  // Find product details using product_id
  const getProduct = (productId) => {
    return products.find((product) => product.id === productId);
  };

  // Calculate total cart amount
  const totalAmount = cartItems.reduce((total, item) => {
    const product = getProduct(item.product_id);

    return total + (product ? product.price * item.quantity : 0);
  }, 0);

  // Update item quantity
  const updateQuantity = async (productId, quantity) => {
    try {
      setError("");
      setMessage("");

      await orderAPI.put(`/cart/${productId}`, {
        quantity,
      });

      setMessage("Cart updated successfully.");
      await fetchCart();
    } catch (err) {
      setError(
        err.response?.data?.detail || "Unable to update quantity."
      );
    }
  };

  // Remove item from cart
  const removeItem = async (productId) => {
    try {
      setError("");
      setMessage("");

      await orderAPI.delete(`/cart/${productId}`);

      setMessage("Product removed from cart.");
      await fetchCart();
    } catch (err) {
      setError(
        err.response?.data?.detail || "Unable to remove product."
      );
    }
  };

  if (loading) {
    return <h3 className="page-message">Loading Cart...</h3>;
  }

  return (
    <div className="cart-page">
      <h2>My Shopping Cart</h2>

      {message && <p className="success-message">{message}</p>}
      {error && <p className="error-message">{error}</p>}

      {cartItems.length === 0 ? (
        <div className="empty-cart">
          <h3>Your cart is empty</h3>
          <button onClick={() => navigate("/products")}>
            Browse Products
          </button>
        </div>
      ) : (
        <>
          <div className="cart-list">
            {cartItems.map((item) => {
              const product = getProduct(item.product_id);

              if (!product) {
                return (
                  <div className="cart-item" key={item.id}>
                    <p>Product #{item.product_id} is unavailable.</p>
                    <button
                      onClick={() => removeItem(item.product_id)}
                    >
                      Remove
                    </button>
                  </div>
                );
              }

              return (
                <div className="cart-item" key={item.id}>
                  <div className="cart-product-info">
                    <h3>{product.name}</h3>
                    <p>Category: {product.category}</p>
                    <p>Price: ₹{Number(product.price).toFixed(2)}</p>
                  </div>

                  <div className="cart-quantity">
                    <button
                      disabled={item.quantity <= 1}
                      onClick={() =>
                        updateQuantity(
                          item.product_id,
                          item.quantity - 1
                        )
                      }
                    >
                      -
                    </button>

                    <span>{item.quantity}</span>

                    <button
                      onClick={() =>
                        updateQuantity(
                          item.product_id,
                          item.quantity + 1
                        )
                      }
                    >
                      +
                    </button>
                  </div>

                  <div className="cart-subtotal">
                    ₹{(product.price * item.quantity).toFixed(2)}
                  </div>

                  <button
                    className="remove-button"
                    onClick={() => removeItem(item.product_id)}
                  >
                    Remove
                  </button>
                </div>
              );
            })}
          </div>

          <div className="cart-summary">
            <h3>
              Total Amount: ₹{totalAmount.toFixed(2)}
            </h3>

            <button
              onClick={() => navigate("/products")}
              className="continue-button"
            >
              Continue Shopping
            </button>

            <button
              onClick={() => navigate("/checkout")}
              className="checkout-button"
            >
              Proceed to Checkout
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default Cart;
