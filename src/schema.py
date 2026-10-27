
import sqlite3
from pathlib import Path

# Find the main project folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Store the database inside the data folder
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "retentioniq.db"


def create_database():
    # Create the data folder if it does not exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Connect to SQLite and create the database file
    with sqlite3.connect(DB_PATH) as connection:
        # Enforce foreign-key relationships
        connection.execute("PRAGMA foreign_keys = ON")

        connection.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            signup_date TEXT NOT NULL,
            region TEXT NOT NULL,
            customer_segment TEXT NOT NULL,
            acquisition_channel TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS subscriptions (
            subscription_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            plan_type TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT,
            monthly_price REAL NOT NULL CHECK (monthly_price >= 0),
            status TEXT NOT NULL
                CHECK (status IN ('active', 'paused', 'cancelled')),
            FOREIGN KEY (customer_id)
                REFERENCES customers(customer_id),
            CHECK (end_date IS NULL OR end_date >= start_date)
        );

        CREATE TABLE IF NOT EXISTS usage_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            subscription_id TEXT NOT NULL,
            snapshot_date TEXT NOT NULL,
            usage_units REAL NOT NULL CHECK (usage_units >= 0),
            active_days INTEGER NOT NULL
                CHECK (active_days BETWEEN 0 AND 31),
            FOREIGN KEY (subscription_id)
                REFERENCES subscriptions(subscription_id),
            UNIQUE (subscription_id, snapshot_date)
        );

        CREATE TABLE IF NOT EXISTS billing_events (
            billing_event_id TEXT PRIMARY KEY,
            subscription_id TEXT NOT NULL,
            event_date TEXT NOT NULL,
            event_type TEXT NOT NULL
                CHECK (event_type IN
                    ('invoice', 'payment', 'refund', 'adjustment')),
            amount REAL NOT NULL,
            payment_status TEXT NOT NULL
                CHECK (payment_status IN
                    ('pending', 'paid', 'overdue', 'failed', 'not_applicable')),
            FOREIGN KEY (subscription_id)
                REFERENCES subscriptions(subscription_id)
        );

        CREATE TABLE IF NOT EXISTS support_cases (
            support_case_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            opened_at TEXT NOT NULL,
            closed_at TEXT,
            issue_type TEXT NOT NULL,
            severity TEXT NOT NULL
                CHECK (severity IN ('low', 'medium', 'high', 'critical')),
            status TEXT NOT NULL
                CHECK (status IN ('open', 'in_progress', 'resolved')),
            FOREIGN KEY (customer_id)
                REFERENCES customers(customer_id),
            CHECK (closed_at IS NULL OR closed_at >= opened_at)
        );

        CREATE TABLE IF NOT EXISTS offers (
            offer_id TEXT PRIMARY KEY,
            offer_name TEXT NOT NULL,
            discount_percent REAL NOT NULL
                CHECK (discount_percent BETWEEN 0 AND 100),
            offer_cost REAL NOT NULL CHECK (offer_cost >= 0),
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            CHECK (end_date >= start_date)
        );

        CREATE TABLE IF NOT EXISTS eligibility_rules (
            rule_id TEXT PRIMARY KEY,
            offer_id TEXT NOT NULL,
            min_risk_score REAL NOT NULL
                CHECK (min_risk_score BETWEEN 0 AND 1),
            max_offer_cost REAL NOT NULL
                CHECK (max_offer_cost >= 0),
            min_monthly_price REAL NOT NULL
                CHECK (min_monthly_price >= 0),
            effective_from TEXT NOT NULL,
            effective_to TEXT,
            FOREIGN KEY (offer_id) REFERENCES offers(offer_id),
            CHECK (effective_to IS NULL OR effective_to >= effective_from)
        );

        CREATE TABLE IF NOT EXISTS campaign_contacts (
            contact_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            subscription_id TEXT NOT NULL,
            offer_id TEXT NOT NULL,
            campaign_date TEXT NOT NULL,
            experiment_group TEXT NOT NULL
                CHECK (experiment_group IN ('treatment', 'control')),
            contact_status TEXT NOT NULL
                CHECK (contact_status IN
                    ('assigned', 'sent', 'delivered', 'failed', 'not_sent')),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id),
            FOREIGN KEY (offer_id) REFERENCES offers(offer_id)
        );

        CREATE TABLE IF NOT EXISTS churn_outcomes (
            churn_outcome_id TEXT PRIMARY KEY,
            subscription_id TEXT NOT NULL,
            prediction_date TEXT NOT NULL,
            horizon_end_date TEXT NOT NULL,
            churn_date TEXT,
            churn_type TEXT NOT NULL
                CHECK (churn_type IN ('voluntary', 'involuntary', 'none')),
            ground_truth_churn INTEGER NOT NULL
                CHECK (ground_truth_churn IN (0, 1)),
            FOREIGN KEY (subscription_id)
                REFERENCES subscriptions(subscription_id),
            CHECK (horizon_end_date >= prediction_date),
            CHECK (
                (ground_truth_churn = 1 AND churn_date IS NOT NULL)
                OR
                (ground_truth_churn = 0 AND churn_date IS NULL)
            ),
            CHECK (churn_date IS NULL OR churn_date > prediction_date),
            CHECK (
                (ground_truth_churn = 1 AND churn_type IN
                    ('voluntary', 'involuntary'))
                OR
                (ground_truth_churn = 0 AND churn_type = 'none')
            )
        );

        CREATE TABLE IF NOT EXISTS retention_outcomes (
            retention_outcome_id TEXT PRIMARY KEY,
            contact_id TEXT NOT NULL,
            outcome_date TEXT NOT NULL,
            retained INTEGER NOT NULL CHECK (retained IN (0, 1)),
            realized_offer_cost REAL NOT NULL
                CHECK (realized_offer_cost >= 0),
            incremental_revenue REAL NOT NULL,
            outcome_reason TEXT NOT NULL,
            FOREIGN KEY (contact_id)
                REFERENCES campaign_contacts(contact_id),
            UNIQUE (contact_id)
        );

        CREATE INDEX IF NOT EXISTS idx_subscriptions_customer
            ON subscriptions(customer_id);

        CREATE INDEX IF NOT EXISTS idx_usage_subscription_date
            ON usage_snapshots(subscription_id, snapshot_date);

        CREATE INDEX IF NOT EXISTS idx_billing_subscription_date
            ON billing_events(subscription_id, event_date);

        CREATE INDEX IF NOT EXISTS idx_support_customer_date
            ON support_cases(customer_id, opened_at);
        """)

    print(f"Database created successfully: {DB_PATH}")


if __name__ == "__main__":
    create_database()
