# customer_database.py

import sqlite3
import json
import logging
import os
from datetime import datetime
from typing import Optional, Dict, List, Any
import operator

# Setup logging
logger = logging.getLogger("CustomerDatabase")

def _normalize_sqlite_path(db_url: str) -> str:
    """
    sqlite3.connect() expects a plain filesystem path, not a SQLAlchemy-style
    URL. Without this, a DATABASE_URL like "sqlite:///customers.db" (the
    documented default) is passed through literally — which fails outright
    on Windows since ':' isn't a valid filename character.
    """
    if db_url.startswith("sqlite:///"):
        return db_url[len("sqlite:///"):]
    if db_url.startswith("sqlite://"):
        return db_url[len("sqlite://"):]
    return db_url

class DBConnection:
    """Context manager for SQLite and PostgreSQL with connection pooling logic."""
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn = None
        self.is_postgres = db_url.startswith("postgres://") or db_url.startswith("postgresql://")

    def __enter__(self):
        if self.is_postgres:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            self.conn = psycopg2.connect(self.db_url)
            # Use RealDictCursor for compatibility with sqlite3.Row
            return self.conn
        else:
            self.conn = sqlite3.connect(_normalize_sqlite_path(self.db_url), check_same_thread=False, timeout=30)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")
            return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if not self.is_postgres:
                self.conn.commit()
            else:
                if exc_type is None:
                    self.conn.commit()
                else:
                    self.conn.rollback()
            self.conn.close()

class CustomerDatabase:
    """Enhanced Customer Database with PostgreSQL support and BI-ready analytics."""
    
    def __init__(self, db_url: Optional[str] = None):
        # Default to local SQLite if no URL provided
        self.db_url = db_url or os.getenv("DATABASE_URL", "customers.db")
        self.is_postgres = self.db_url.startswith("postgres")
        self.placeholder = "%s" if self.is_postgres else "?"
        self._create_tables()
        self._seed_data()

    def _get_cursor(self, conn):
        if self.is_postgres:
            import psycopg2.extras
            return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        return conn.cursor()

    def _create_tables(self):
        with DBConnection(self.db_url) as conn:
            cursor = self._get_cursor(conn)
            
            # Decimal type in Postgres, Real/Float in SQLite
            numeric_type = "DECIMAL(10,2)" if self.is_postgres else "REAL"
            json_type = "JSONB" if self.is_postgres else "TEXT"
            
            # 1. Customers Table
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                tier TEXT DEFAULT 'standard',
                total_spent {numeric_type} DEFAULT 0.00
            )
            """)
            
            # 2. Orders Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                customer_id TEXT,
                status TEXT,
                items TEXT,
                estimated_delivery DATE,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            )
            """)
            
            # 3. Tickets Table (Escalations)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id TEXT PRIMARY KEY,
                customer_id TEXT,
                created_date TIMESTAMP,
                status TEXT DEFAULT 'OPEN',
                priority TEXT,
                category TEXT,
                description TEXT
            )
            """)
            
            # 4. Conversations Table (Refactored for 10/10 Analytics)
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                customer_id TEXT,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                messages_json {json_type}, 
                resolved_status BOOLEAN,
                final_sentiment TEXT,
                final_priority TEXT,
                total_tokens INTEGER,
                is_human_takeover BOOLEAN DEFAULT FALSE,
                cost_estimate {numeric_type} DEFAULT 0.0
            )
            """)

    def get_customer_by_email(self, email: str) -> Optional[Dict]:
        with DBConnection(self.db_url) as conn:
            cursor = self._get_cursor(conn)
            cursor.execute(f"SELECT * FROM customers WHERE email = {self.placeholder}", (email,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_customer_orders(self, customer_id: str) -> List[Dict]:
        with DBConnection(self.db_url) as conn:
            cursor = self._get_cursor(conn)
            cursor.execute(f"SELECT * FROM orders WHERE customer_id = {self.placeholder}", (customer_id,))
            return [dict(row) for row in cursor.fetchall()]

    def create_ticket(self, customer_id: str, category: str, priority: str, description: str) -> str:
        ticket_id = f"TICK-{datetime.now().strftime('%y%m%d%H%M%S')}"
        with DBConnection(self.db_url) as conn:
            cursor = self._get_cursor(conn)
            cursor.execute(
                f"INSERT INTO tickets (ticket_id, customer_id, created_date, status, priority, category, description) VALUES ({self.placeholder}, {self.placeholder}, {self.placeholder}, {self.placeholder}, {self.placeholder}, {self.placeholder}, {self.placeholder})",
                (ticket_id, customer_id, datetime.now(), "OPEN", priority, category, description)
            )
        return ticket_id

    def save_conversation(self, data: Dict):
        """Saves session with analytics columns for BI tools."""
        with DBConnection(self.db_url) as conn:
            cursor = self._get_cursor(conn)
            
            # Postgres upsert vs SQLite
            if self.is_postgres:
                sql = """
                    INSERT INTO conversations 
                    (conversation_id, customer_id, messages_json, resolved_status, 
                     final_sentiment, final_priority, total_tokens, cost_estimate)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (conversation_id) DO UPDATE SET
                    messages_json = EXCLUDED.messages_json,
                    resolved_status = EXCLUDED.resolved_status,
                    total_tokens = EXCLUDED.total_tokens,
                    cost_estimate = EXCLUDED.cost_estimate
                """
            else:
                sql = """
                    INSERT OR REPLACE INTO conversations 
                    (conversation_id, customer_id, messages_json, resolved_status, 
                     final_sentiment, final_priority, total_tokens, cost_estimate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                
            cursor.execute(sql, (
                data['id'],
                data.get('customer_id', 'GUEST'),
                json.dumps(data.get('messages', [])),
                data.get('resolved', False),
                data.get('sentiment', 'neutral'),
                data.get('priority', 'medium'),
                data.get('tokens', 0),
                data.get('tokens', 0) * 0.00000014
            ))

    def _seed_data(self):
        with DBConnection(self.db_url) as conn:
            cursor = self._get_cursor(conn)
            # Use universal seeding with placeholder abstraction
            # Seed Customers
            cursor.execute(f"INSERT INTO customers (customer_id, name, email, tier, total_spent) VALUES ({self.placeholder}, {self.placeholder}, {self.placeholder}, {self.placeholder}, {self.placeholder}) ON CONFLICT DO NOTHING", ('C1', 'Alice Johnson', 'alice@example.com', 'premium', 1250.50))
            if not self.is_postgres: # SQLite specific ignore syntax handled by DBConnection if needed, but here we use manual
                 cursor.execute("INSERT OR IGNORE INTO customers VALUES ('C1', 'Alice Johnson', 'alice@example.com', 'premium', 1250.50)")
                 cursor.execute("INSERT OR IGNORE INTO customers VALUES ('C2', 'Bob Smith', 'bob@example.com', 'standard', 45.00)")
                 cursor.execute("INSERT OR IGNORE INTO orders VALUES ('ORD-123', 'C1', 'Shipped', 'Wireless Headphones, USB-C Cable', '2026-01-30')")
                 cursor.execute("INSERT OR IGNORE INTO orders VALUES ('ORD-456', 'C1', 'Processing', 'Smart Watch', '2026-02-05')")
            else:
                cursor.execute("INSERT INTO customers VALUES ('C1', 'Alice Johnson', 'alice@example.com', 'premium', 1250.50) ON CONFLICT DO NOTHING")
                cursor.execute("INSERT INTO customers VALUES ('C2', 'Bob Smith', 'bob@example.com', 'standard', 45.00) ON CONFLICT DO NOTHING")
                cursor.execute("INSERT INTO orders VALUES ('ORD-123', 'C1', 'Shipped', 'Wireless Headphones, USB-C Cable', '2026-01-30') ON CONFLICT DO NOTHING")
                cursor.execute("INSERT INTO orders VALUES ('ORD-456', 'C1', 'Processing', 'Smart Watch', '2026-02-05') ON CONFLICT DO NOTHING")
            
            logger.info("Database seeding completed.")
