
import { useEffect, useState } from "react";
import { productAPI } from "../../services/api";

function ManageProducts() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stockValues, setStockValues] = useState({});
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    name: "",
    description: "",
    image_url: "",
    category: "",
    price: "",
    stock_quantity: "",
    low_stock_threshold: 5,
  });

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const response = await productAPI.get("/products/");
      setProducts(response.data);
      setError("");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load products.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  // Create product
  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      await productAPI.post("/products/", {
        ...form,
        image_url: form.image_url.trim() || null,
        price: Number(form.price),
        stock_quantity: Number(form.stock_quantity),
        low_stock_threshold: Number(form.low_stock_threshold),
      });

      alert("Product created successfully!");

      setForm({
        name: "",
        description: "",
        image_url: "",
        category: "",
        price: "",
        stock_quantity: "",
        low_stock_threshold: 5,
      });

      fetchProducts();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to create product.");
    }
  };

  // Delete product
  const handleDelete = async (productId) => {
    if (!window.confirm("Are you sure you want to delete this product?")) {
      return;
    }

    try {
      await productAPI.delete(`/products/${productId}`);
      alert("Product deleted successfully!");
      fetchProducts();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to delete product.");
    }
  };

  // Handle stock input
  const handleStockChange = (productId, quantity) => {
    setStockValues((previous) => ({
      ...previous,
      [productId]: quantity,
    }));
  };

  // Update stock
  const updateStock = async (productId) => {
    const quantity = Number(stockValues[productId]);

    if (
      stockValues[productId] === undefined ||
      stockValues[productId] === "" ||
      !Number.isInteger(quantity) ||
      quantity < 0
    ) {
      alert("Enter a valid stock quantity (0 or greater).");
      return;
    }

    try {
      await productAPI.patch(
        `/products/${productId}/stock`,
        { quantity }
      );

      alert("Product stock updated successfully!");

      setStockValues((previous) => {
        const updated = { ...previous };
        delete updated[productId];
        return updated;
      });

      await fetchProducts();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to update stock.");
    }
  };

  return (
    <div className="admin-page">
      <h2>Manage Products</h2>

      {/* Add Product Form */}
      <form className="admin-form" onSubmit={handleSubmit}>
        <h3>Add New Product</h3>

        <input
          name="name"
          placeholder="Product Name"
          value={form.name}
          onChange={handleChange}
          required
        />

        <input
          name="description"
          placeholder="Description"
          value={form.description}
          onChange={handleChange}
        />

        {/* Image URL */}
        <input
          name="image_url"
          type="url"
          placeholder="Product Image URL"
          value={form.image_url}
          onChange={handleChange}
        />

        {/* Image Preview */}
        {form.image_url && (
          <div className="admin-image-preview">
            <img
              src={form.image_url}
              alt="Product preview"
              onError={(e) => {
                e.currentTarget.style.display = "none";
              }}
              onLoad={(e) => {
                e.currentTarget.style.display = "block";
              }}
            />
          </div>
        )}

        <input
          name="category"
          placeholder="Category"
          value={form.category}
          onChange={handleChange}
          required
        />

        <input
          name="price"
          type="number"
          min="0.01"
          step="0.01"
          placeholder="Price"
          value={form.price}
          onChange={handleChange}
          required
        />

        <input
          name="stock_quantity"
          type="number"
          min="0"
          placeholder="Stock Quantity"
          value={form.stock_quantity}
          onChange={handleChange}
          required
        />

        <input
          name="low_stock_threshold"
          type="number"
          min="0"
          placeholder="Low Stock Threshold"
          value={form.low_stock_threshold}
          onChange={handleChange}
          required
        />

        <button type="submit">Add Product</button>
      </form>

      <h3>Existing Products</h3>

      {loading ? (
        <p>Loading products...</p>
      ) : error ? (
        <p className="admin-error">{error}</p>
      ) : products.length === 0 ? (
        <p>No products found.</p>
      ) : (
        <div className="admin-product-list">
          {products.map((product) => (
            <div className="admin-product-card" key={product.id}>

              {/* Product Image */}
              <div className="admin-product-image">
                <img
                  src={
                    product.image_url ||
                    "https://placehold.co/300x200?text=No+Image"
                  }
                  alt={product.name}
                  onError={(e) => {
                    e.currentTarget.onerror = null;
                    e.currentTarget.src =
                      "https://placehold.co/300x200?text=Image+Not+Available";
                  }}
                />
              </div>

              <h4>{product.name}</h4>
              <p>Category: {product.category}</p>
              <p>Price: ₹{product.price}</p>
              <p>Available Stock: {product.stock_quantity}</p>

              <div className="stock-update-controls">
                <p>
                  <strong>Current Stock:</strong> {product.stock_quantity}
                </p>

                <input
                  type="number"
                  min="0"
                  step="1"
                  placeholder="Enter new quantity"
                  value={stockValues[product.id] ?? product.stock_quantity}
                  onChange={(e) =>
                    handleStockChange(product.id, e.target.value)
                  }
                />

                <button onClick={() => updateStock(product.id)}>
                  Update Stock
                </button>
              </div>

              <button
                className="danger-button"
                onClick={() => handleDelete(product.id)}
              >
                Delete Product
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ManageProducts;
