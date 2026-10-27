
import sqlite3

import pytest

from src.schema import DB_PATH


@pytest.fixture
def connection():
    """Open the RetentionIQ database for testing."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn


def test_all_required_tables_exist(connection):
    expected_tables = {
        "customers", "subscriptions", "usage_snapshots",
        "billing_events", "support_cases", "offers",
        "eligibility_rules", "campaign_contacts",
        "churn_outcomes", "retention_outcomes",
    }
    actual_tables = {
        row["name"]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    assert expected_tables.issubset(actual_tables)


@pytest.mark.parametrize(
    "table, id_column",
    [
        ("customers", "customer_id"),
        ("subscriptions", "subscription_id"),
        ("usage_snapshots", "snapshot_id"),
        ("billing_events", "billing_event_id"),
        ("support_cases", "support_case_id"),
        ("offers", "offer_id"),
        ("eligibility_rules", "rule_id"),
        ("campaign_contacts", "contact_id"),
        ("churn_outcomes", "churn_outcome_id"),
        ("retention_outcomes", "retention_outcome_id"),
    ],
)
def test_primary_ids_are_unique_and_not_null(connection, table, id_column):
    query = f"""
        SELECT COUNT(*) FROM (
            SELECT {id_column} FROM {table}
            GROUP BY {id_column}
            HAVING {id_column} IS NULL OR COUNT(*) > 1
        )
    """
    violations = connection.execute(query).fetchone()[0]
    assert violations == 0, f"{table} has invalid IDs"


def test_foreign_keys_are_valid(connection):
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_churn_labels_match_churn_dates(connection):
    violations = connection.execute("""
        SELECT COUNT(*) FROM churn_outcomes
        WHERE (ground_truth_churn = 1 AND churn_date IS NULL)
           OR (ground_truth_churn = 0 AND churn_date IS NOT NULL)
    """).fetchone()[0]
    assert violations == 0


def test_churn_dates_are_within_evaluation_horizon(connection):
    violations = connection.execute("""
        SELECT COUNT(*) FROM churn_outcomes
        WHERE churn_date IS NOT NULL
          AND (churn_date <= prediction_date
               OR churn_date > horizon_end_date)
    """).fetchone()[0]
    assert violations == 0


def test_risk_scores_are_between_zero_and_one(connection):
    violations = connection.execute("""
        SELECT COUNT(*) FROM campaign_contacts
        WHERE risk_score IS NULL OR risk_score < 0 OR risk_score > 1
    """).fetchone()[0]
    assert violations == 0


def test_control_group_has_zero_offer_cost(connection):
    violations = connection.execute("""
        SELECT COUNT(*)
        FROM retention_outcomes ro
        JOIN campaign_contacts cc ON ro.contact_id = cc.contact_id
        WHERE cc.experiment_group = 'control'
          AND ro.realized_offer_cost != 0
    """).fetchone()[0]
    assert violations == 0


def test_retention_values_are_valid(connection):
    violations = connection.execute("""
        SELECT COUNT(*) FROM retention_outcomes
        WHERE retained NOT IN (0, 1)
           OR realized_offer_cost < 0
           OR incremental_revenue < 0
    """).fetchone()[0]
    assert violations == 0


def test_each_campaign_contact_has_one_retention_outcome(connection):
    contacts = connection.execute(
        "SELECT COUNT(*) FROM campaign_contacts"
    ).fetchone()[0]
    outcomes = connection.execute(
        "SELECT COUNT(*) FROM retention_outcomes"
    ).fetchone()[0]
    assert contacts == outcomes


def test_rejects_churn_before_prediction_date():
    with sqlite3.connect(":memory:") as conn:
        conn.execute("""
            CREATE TABLE churn_outcomes (
                prediction_date TEXT,
                horizon_end_date TEXT,
                churn_date TEXT,
                ground_truth_churn INTEGER
            )
        """)
        conn.execute("""
            INSERT INTO churn_outcomes
            VALUES ('2026-06-15', '2026-07-15', '2026-06-10', 1)
        """)
        violations = conn.execute("""
            SELECT COUNT(*) FROM churn_outcomes
            WHERE churn_date IS NOT NULL
              AND (churn_date <= prediction_date
                   OR churn_date > horizon_end_date)
        """).fetchone()[0]
        assert violations == 1


def test_detects_offer_sent_to_ineligible_customer():
    with sqlite3.connect(":memory:") as conn:
        conn.executescript("""
            CREATE TABLE campaign_contacts (
                contact_id TEXT, offer_id TEXT, campaign_date TEXT
            );
            CREATE TABLE eligibility_rules (
                offer_id TEXT, min_risk_score REAL,
                max_offer_cost REAL, min_monthly_price REAL,
                effective_from TEXT, effective_to TEXT
            );
            CREATE TABLE offers (
                offer_id TEXT, offer_cost REAL,
                start_date TEXT, end_date TEXT
            );
            CREATE TABLE test_customer (
                contact_id TEXT, risk_score REAL, monthly_price REAL
            );
        """)
        conn.execute("""
            INSERT INTO campaign_contacts VALUES ('C1','O1','2026-06-20')
        """)
        conn.execute("""
            INSERT INTO eligibility_rules
            VALUES ('O1',0.70,200,100,'2026-06-01','2026-06-30')
        """)
        conn.execute("""
            INSERT INTO offers VALUES ('O1',150,'2026-06-01','2026-06-30')
        """)
        conn.execute("""
            INSERT INTO test_customer VALUES ('C1',0.40,500)
        """)
        violations = conn.execute("""
            SELECT COUNT(*) FROM campaign_contacts cc
            JOIN test_customer c ON c.contact_id = cc.contact_id
            JOIN offers o ON o.offer_id = cc.offer_id
            WHERE NOT EXISTS (
                SELECT 1 FROM eligibility_rules er
                WHERE er.offer_id = cc.offer_id
                  AND c.risk_score >= er.min_risk_score
                  AND o.offer_cost <= er.max_offer_cost
                  AND c.monthly_price >= er.min_monthly_price
                  AND cc.campaign_date
                      BETWEEN er.effective_from AND er.effective_to
                  AND cc.campaign_date
                      BETWEEN o.start_date AND o.end_date
            )
        """).fetchone()[0]
        assert violations == 1


def test_detects_treatment_control_leakage():
    with sqlite3.connect(":memory:") as conn:
        conn.execute("""
            CREATE TABLE campaign_contacts (
                customer_id TEXT, campaign_date TEXT, experiment_group TEXT
            )
        """)
        conn.executemany("""
            INSERT INTO campaign_contacts VALUES (?, ?, ?)
        """, [
            ("C1", "2026-06-20", "treatment"),
            ("C1", "2026-06-20", "control"),
        ])
        violations = conn.execute("""
            SELECT COUNT(*) FROM (
                SELECT customer_id, campaign_date
                FROM campaign_contacts
                GROUP BY customer_id, campaign_date
                HAVING COUNT(DISTINCT experiment_group) > 1
            )
        """).fetchone()[0]
        assert violations == 1


def test_detects_retained_customer_attributed_to_multiple_offers():
    with sqlite3.connect(":memory:") as conn:
        conn.executescript("""
            CREATE TABLE campaign_contacts (
                contact_id TEXT, customer_id TEXT,
                experiment_group TEXT, offer_id TEXT
            );
            CREATE TABLE retention_outcomes (
                contact_id TEXT, retained INTEGER
            );
        """)
        conn.executemany("""
            INSERT INTO campaign_contacts VALUES (?, ?, ?, ?)
        """, [
            ("C1", "CUSTOMER1", "treatment", "OFFER1"),
            ("C2", "CUSTOMER1", "treatment", "OFFER2"),
        ])
        conn.executemany("""
            INSERT INTO retention_outcomes VALUES (?, ?)
        """, [("C1", 1), ("C2", 1)])
        violations = conn.execute("""
            SELECT COUNT(*) FROM (
                SELECT cc.customer_id
                FROM campaign_contacts cc
                JOIN retention_outcomes ro
                  ON ro.contact_id = cc.contact_id
                WHERE cc.experiment_group = 'treatment'
                  AND ro.retained = 1
                GROUP BY cc.customer_id
                HAVING COUNT(DISTINCT cc.offer_id) > 1
            )
        """).fetchone()[0]
        assert violations == 1
