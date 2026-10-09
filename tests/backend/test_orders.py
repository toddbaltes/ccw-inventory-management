"""
Tests for orders API endpoints.
"""
import pytest

ORDER_FIELDS = [
    "id", "order_number", "customer", "items", "status", "order_date",
    "expected_delivery", "total_value", "actual_delivery", "warehouse", "category",
]


class TestOrdersEndpoints:
    """Test suite for order-related endpoints."""

    def test_get_all_orders(self, client):
        """Test getting all orders."""
        response = client.get("/api/orders")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        for field in ORDER_FIELDS:
            assert field in data[0]

    def test_order_status_values(self, client):
        """Test that orders have valid status values."""
        data = client.get("/api/orders").json()
        valid = {"delivered", "shipped", "processing", "backordered"}
        for order in data:
            assert order["status"].lower() in valid

    def test_order_items_structure(self, client):
        """Test that order items have proper structure and types."""
        data = client.get("/api/orders").json()
        for order in data:
            assert isinstance(order["items"], list)
            assert len(order["items"]) > 0
            for item in order["items"]:
                assert "sku" in item
                assert "name" in item
                assert isinstance(item["quantity"], int)
                assert isinstance(item["unit_price"], (int, float))

    def test_order_total_value_calculation(self, client):
        """Test that total_value equals sum of item quantity * unit_price."""
        data = client.get("/api/orders").json()
        for order in data:
            calculated = sum(i["quantity"] * i["unit_price"] for i in order["items"])
            assert abs(order["total_value"] - calculated) < 0.01, order["order_number"]

    def test_order_dates_format(self, client):
        """Test that order dates are ISO formatted 2025 timestamps."""
        data = client.get("/api/orders").json()
        for order in data:
            assert order["order_date"].startswith("2025-")
            assert "T" in order["order_date"]
            assert "T" in order["expected_delivery"]

    def test_delivered_orders_have_actual_delivery_date(self, client):
        """Test that non-delivered orders have no actual delivery date."""
        data = client.get("/api/orders").json()
        for order in data:
            if order["status"] != "Delivered":
                assert order["actual_delivery"] is None

    def test_get_orders_by_warehouse(self, client):
        """Test filtering orders by warehouse."""
        response = client.get("/api/orders?warehouse=Tokyo")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        for order in data:
            assert order["warehouse"] == "Tokyo"

    def test_get_orders_by_category_case_insensitive(self, client):
        """Test category filter ignores case."""
        lower = client.get("/api/orders?category=sensors").json()
        proper = client.get("/api/orders?category=Sensors").json()
        assert len(lower) > 0
        assert lower == proper
        for order in lower:
            assert order["category"].lower() == "sensors"

    def test_get_orders_by_status(self, client):
        """Test filtering orders by status (case-insensitive)."""
        data = client.get("/api/orders?status=delivered").json()
        assert len(data) > 0
        for order in data:
            assert order["status"].lower() == "delivered"

    def test_get_orders_by_month(self, client):
        """Test filtering orders by a single month."""
        data = client.get("/api/orders?month=2025-03").json()
        assert len(data) > 0
        for order in data:
            assert order["order_date"].startswith("2025-03")

    def test_get_orders_by_quarter(self, client):
        """Test filtering orders by quarter."""
        data = client.get("/api/orders?month=Q2-2025").json()
        assert len(data) > 0
        for order in data:
            assert order["order_date"][:7] in ["2025-04", "2025-05", "2025-06"]

    def test_quarters_partition_all_orders(self, client):
        """Test that the four quarters together cover every order."""
        total = len(client.get("/api/orders").json())
        quarter_total = sum(
            len(client.get(f"/api/orders?month=Q{q}-2025").json()) for q in range(1, 5)
        )
        assert quarter_total == total

    def test_month_all_returns_everything(self, client):
        """Test that month=all and filter 'all' values apply no filtering."""
        everything = client.get("/api/orders").json()
        filtered = client.get(
            "/api/orders?month=all&warehouse=all&category=all&status=all"
        ).json()
        assert filtered == everything

    def test_get_orders_multiple_filters(self, client):
        """Test combining all filters."""
        response = client.get(
            "/api/orders?warehouse=London&category=Sensors&status=Delivered&month=Q1-2025"
        )
        assert response.status_code == 200
        for order in response.json():
            assert order["warehouse"] == "London"
            assert order["category"].lower() == "sensors"
            assert order["status"].lower() == "delivered"
            assert order["order_date"][:7] in ["2025-01", "2025-02", "2025-03"]

    def test_filter_with_no_matches_returns_empty_list(self, client):
        """Test that a month with no orders returns an empty list."""
        response = client.get("/api/orders?month=2030-01")
        assert response.status_code == 200
        assert response.json() == []

    def test_unknown_warehouse_returns_empty_list(self, client):
        """Test that an unknown warehouse yields no results."""
        response = client.get("/api/orders?warehouse=Atlantis")
        assert response.status_code == 200
        assert response.json() == []

    def test_filtered_results_are_subset_of_all(self, client):
        """Test that a filtered result is a subset of the unfiltered list."""
        all_orders = client.get("/api/orders").json()
        filtered = client.get("/api/orders?status=Shipped").json()
        assert 0 < len(filtered) < len(all_orders)
        all_numbers = [o["order_number"] for o in all_orders]
        for order in filtered:
            assert order["order_number"] in all_numbers

    def test_get_order_by_id(self, client):
        """Test getting a specific order by ID."""
        first_id = client.get("/api/orders").json()[0]["id"]
        response = client.get(f"/api/orders/{first_id}")
        assert response.status_code == 200
        order = response.json()
        assert order["id"] == first_id
        for field in ORDER_FIELDS:
            assert field in order

    def test_get_order_by_id_matches_list_entry(self, client, sample_order):
        """Test that the single-order response matches the known first order."""
        order = client.get("/api/orders/1").json()
        assert order == sample_order

    def test_get_nonexistent_order(self, client):
        """Test getting an order that doesn't exist."""
        response = client.get("/api/orders/nonexistent-order-999")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
