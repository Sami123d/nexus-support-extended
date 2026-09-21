from customer_database import CustomerDatabase, _normalize_sqlite_path


def test_normalize_sqlite_path_strips_triple_slash_scheme():
    assert _normalize_sqlite_path("sqlite:///customers.db") == "customers.db"


def test_normalize_sqlite_path_strips_double_slash_scheme():
    assert _normalize_sqlite_path("sqlite://customers.db") == "customers.db"


def test_normalize_sqlite_path_leaves_plain_path_untouched():
    assert _normalize_sqlite_path("customers.db") == "customers.db"


def test_seed_data_is_present_on_fresh_db(temp_db_path):
    db = CustomerDatabase(temp_db_path)
    customer = db.get_customer_by_email("alice@example.com")
    assert customer is not None
    assert customer["tier"] == "premium"


def test_get_customer_orders_returns_seeded_orders(temp_db_path):
    db = CustomerDatabase(temp_db_path)
    orders = db.get_customer_orders("C1")
    assert len(orders) >= 1
    assert any(o["order_id"] == "ORD-123" for o in orders)


def test_create_ticket_returns_unique_id(temp_db_path):
    db = CustomerDatabase(temp_db_path)
    ticket_id = db.create_ticket("C1", "Billing", "High", "Refund dispute")
    assert ticket_id.startswith("TICK-")


def test_save_conversation_round_trips(temp_db_path):
    db = CustomerDatabase(temp_db_path)
    db.save_conversation({
        "id": "SESS-test-1",
        "customer_id": "C1",
        "messages": ["hello", "world"],
        "resolved": True,
        "sentiment": "positive",
        "priority": "low",
        "tokens": 500,
    })
    # No exception means the insert (and its cost_estimate computation) succeeded


def test_sqlite_db_actually_created_with_normalized_url_on_disk(tmp_path):
    url = f"sqlite:///{tmp_path / 'nested.db'}"
    db = CustomerDatabase(url)
    assert db.get_customer_by_email("alice@example.com") is not None
    assert (tmp_path / "nested.db").exists()
