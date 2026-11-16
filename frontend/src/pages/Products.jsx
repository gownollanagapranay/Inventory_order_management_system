
import { useEffect, useState } from "react";
import { productAPI, orderAPI } from "../services/api";

function Products() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [addingId, setAddingId] = useState(null);

  // Fetch all products
  const fetchProducts = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await productAPI.get("/products/");
      setProducts(response.data);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Unable to load products."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  // Add product to cart
  const addToCart = async (productId) => {
    try {
      setAddingId(productId);
      setMessage("");
      setError("");

      await orderAPI.post("/cart/", {
        product_id: productId,
        quantity: 1,
      });

      setMessage("Product added to cart successfully!");
    } catch (err) {
      setError(
        err.response?.data?.detail || "Unable to add product to cart."
      );
    } finally {
      setAddingId(null);
    }
  };

  if (loading) {
    return <h3 className="page-message">Loading products...</h3>;
  }

  return (
    <div className="products-page">
      <div className="products-header">
        <h2>Available Products</h2>
        <button onClick={fetchProducts}>Refresh Products</button>
      </div>

      {message && <p className="success-message">{message}</p>}
      {error && <p className="error-message">{error}</p>}

      {products.length === 0 ? (
        <p>No products available.</p>
      ) : (
        <div className="products-grid">
          {products.map((product) => (
            <div className="product-card" key={product.id}>
              
              {/* Product Image */}
              <div className="product-image-container">
                <img
                  src={
                    product.image_url ||
                    "https://placehold.co/400x300?text=No+Image"
                  }
                  alt={product.name}
                  className="product-image"
                  onError={(e) => {
                    e.currentTarget.onerror = null;
                    e.currentTarget.src =
                      "https://placehold.co/400x300?text=Image+Not+Available";
                  }}
                />
              </div>

              <span className="product-category">
                {product.category}
              </span>

              <h3>{product.name}</h3>

              <p className="product-description">
                {product.description || "No description available."}
              </p>

              <h3 className="product-price">
                ₹{Number(product.price).toFixed(2)}
              </h3>

              <p>
                Stock Available: <strong>{product.stock_quantity}</strong>
              </p>

              <button
                onClick={() => addToCart(product.id)}
                disabled={product.stock_quantity <= 0 || addingId !== null}
              >
                {addingId === product.id
                  ? "Adding..."
                  : product.stock_quantity <= 0
                  ? "Out of Stock"
                  : "Add to Cart"}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Products;
