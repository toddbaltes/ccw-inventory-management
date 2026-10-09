"""
Tests for spending, report, demand and backlog response shapes.
"""
import pytest


class TestSpendingSummary:
    """Test suite for /api/spending/summary."""

    def test_summary_fields_and_types(self, client):
        """Test summary contains all cost totals and change percentages."""
        data = client.get("/api/spending/summary").json()
        for key in ["procurement", "operational", "labor", "overhead"]:
            assert isinstance(data[f"total_{key}_cost" if key != "overhead" else "total_overhead"], (int, float))
            assert isinstance(data[f"{key}_change"], (int, float))

    def test_summary_totals_positive(self, client):
        """Test summary totals are positive."""
        data = client.get("/api/spending/summary").json()
        for key in ["total_procurement_cost", "total_operational_cost",
                    "total_labor_cost", "total_overhead"]:
            assert data[key] > 0


class TestMonthlySpending:
    """Test suite for /api/spending/monthly."""

    def test_twelve_months_in_calendar_order(self, client):
        """Test that all twelve months are returned in order."""
        data = client.get("/api/spending/monthly").json()
        assert [m["month"] for m in data] == [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ]

    def test_monthly_fields(self, client):
        """Test each month has the expected cost fields."""
        for m in client.get("/api/spending/monthly").json():
            assert set(m.keys()) >= {"month", "procurement", "operational", "labor", "overhead"}


class TestCategorySpending:
    """Test suite for /api/spending/categories."""

    def test_category_structure(self, client):
        """Test categories have name, amount, percentage and change."""
        data = client.get("/api/spending/categories").json()
        assert len(data) > 0
        for cat in data:
            assert isinstance(cat["category"], str)
            assert cat["amount"] > 0
            assert 0 < cat["percentage"] <= 100
            assert isinstance(cat["change"], (int, float))

    def test_category_names_unique(self, client):
        """Test category names are unique."""
        names = [c["category"] for c in client.get("/api/spending/categories").json()]
        assert len(names) == len(set(names))


class TestTransactions:
    """Test suite for /api/spending/transactions."""

    def test_transaction_structure(self, client):
        """Test transactions have all expected fields."""
        data = client.get("/api/spending/transactions").json()
        assert len(data) > 0
        for field in ["id", "date", "description", "category", "warehouse",
                      "amount", "vendor", "type"]:
            assert field in data[0]

    def test_transaction_ids_unique(self, client):
        """Test transaction IDs are unique."""
        ids = [t["id"] for t in client.get("/api/spending/transactions").json()]
        assert len(ids) == len(set(ids))

    def test_transaction_types_and_amounts(self, client):
        """Test transaction types are valid and amounts positive."""
        for t in client.get("/api/spending/transactions").json():
            assert t["type"] in ["Purchase", "Operational", "Overhead"]
            assert t["amount"] > 0

    def test_transaction_dates_sorted_ascending(self, client):
        """Test transactions are in ascending date order, ISO formatted."""
        dates = [t["date"] for t in client.get("/api/spending/transactions").json()]
        assert all(len(d) == 10 and d[4] == "-" for d in dates)
        assert dates == sorted(dates)


class TestQuarterlyReports:
    """Test suite for /api/reports/quarterly."""

    def test_four_quarters_sorted(self, client):
        """Test all four quarters are returned in order."""
        data = client.get("/api/reports/quarterly").json()
        assert [q["quarter"] for q in data] == ["Q1-2025", "Q2-2025", "Q3-2025", "Q4-2025"]

    def test_quarterly_structure(self, client):
        """Test quarterly entries have expected fields."""
        for q in client.get("/api/reports/quarterly").json():
            for field in ["quarter", "total_orders", "total_revenue",
                          "delivered_orders", "avg_order_value", "fulfillment_rate"]:
                assert field in q

    def test_quarterly_matches_orders(self, client):
        """Test quarterly counts and revenue match the orders endpoint."""
        quarters = client.get("/api/reports/quarterly").json()
        for q in quarters:
            orders = client.get(f"/api/orders?month={q['quarter']}").json()
            assert q["total_orders"] == len(orders)
            assert q["delivered_orders"] == sum(1 for o in orders if o["status"] == "Delivered")
            assert abs(q["total_revenue"] - sum(o["total_value"] for o in orders)) < 0.01

    def test_quarterly_derived_values(self, client):
        """Test average order value and fulfillment rate calculations."""
        for q in client.get("/api/reports/quarterly").json():
            assert abs(q["avg_order_value"] - q["total_revenue"] / q["total_orders"]) < 0.01
            expected_rate = q["delivered_orders"] / q["total_orders"] * 100
            assert abs(q["fulfillment_rate"] - expected_rate) < 0.1
            assert 0 <= q["fulfillment_rate"] <= 100

    def test_quarterly_totals_cover_all_orders(self, client):
        """Test quarterly order counts sum to the total number of orders."""
        total = len(client.get("/api/orders").json())
        assert sum(q["total_orders"] for q in client.get("/api/reports/quarterly").json()) == total


class TestMonthlyTrends:
    """Test suite for /api/reports/monthly-trends."""

    def test_twelve_months_sorted(self, client):
        """Test trends cover 2025-01 through 2025-12 in order."""
        data = client.get("/api/reports/monthly-trends").json()
        assert [m["month"] for m in data] == [f"2025-{i:02d}" for i in range(1, 13)]

    def test_monthly_trends_structure(self, client):
        """Test trend entries have expected fields."""
        for m in client.get("/api/reports/monthly-trends").json():
            for field in ["month", "order_count", "revenue", "delivered_count"]:
                assert field in m
            assert m["delivered_count"] <= m["order_count"]

    def test_monthly_trends_match_orders(self, client):
        """Test per-month figures match the orders endpoint."""
        for m in client.get("/api/reports/monthly-trends").json():
            orders = client.get(f"/api/orders?month={m['month']}").json()
            assert m["order_count"] == len(orders)
            assert m["delivered_count"] == sum(1 for o in orders if o["status"] == "Delivered")
            assert abs(m["revenue"] - sum(o["total_value"] for o in orders)) < 0.01

    def test_monthly_trends_consistent_with_quarterly(self, client):
        """Test monthly revenue rolls up to the quarterly revenue."""
        months = client.get("/api/reports/monthly-trends").json()
        quarters = client.get("/api/reports/quarterly").json()
        for idx, q in enumerate(quarters):
            revenue = sum(m["revenue"] for m in months[idx * 3: idx * 3 + 3])
            assert abs(revenue - q["total_revenue"]) < 0.01


class TestDemandAndBacklogShape:
    """Additional shape tests for demand and backlog."""

    def test_demand_field_types_and_unique_ids(self, client):
        """Test demand field types and ID uniqueness."""
        data = client.get("/api/demand").json()
        assert len(data) > 0
        assert len({d["id"] for d in data}) == len(data)
        for d in data:
            assert isinstance(d["current_demand"], int)
            assert isinstance(d["forecasted_demand"], int)
            assert isinstance(d["period"], str)

    def test_increasing_trend_means_higher_forecast(self, client):
        """Test increasing items forecast above and decreasing below current."""
        for d in client.get("/api/demand").json():
            if d["trend"].lower() == "increasing":
                assert d["forecasted_demand"] > d["current_demand"]
            elif d["trend"].lower() == "decreasing":
                assert d["forecasted_demand"] < d["current_demand"]

    def test_backlog_field_types(self, client):
        """Test backlog field types, including purchase order flag."""
        data = client.get("/api/backlog").json()
        assert len(data) > 0
        assert len({b["id"] for b in data}) == len(data)
        for b in data:
            assert isinstance(b["quantity_needed"], int)
            assert isinstance(b["quantity_available"], int)
            assert isinstance(b["days_delayed"], int)
            assert isinstance(b["has_purchase_order"], bool)

    def test_backlog_items_are_short_on_stock(self, client):
        """Test backlog items need more than is available."""
        for b in client.get("/api/backlog").json():
            assert b["quantity_needed"] > b["quantity_available"]
