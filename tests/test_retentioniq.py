
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
        "customers",
        "subscriptions",
        "usage_snapshots",
        "billing_events",
        "support_cases",
        "offers",
        "eligibility_rules",
        "campaign_contacts",
        "churn_outcomes",
        "retention_outcomes",
    }

    actual_tables = {
        row["name"]
        for row in connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
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
def test_primary_ids_are_unique_and_not_null(
    connection, table, id_column
):
    query = f"""
        SELECT COUNT(*)
        FROM (
            SELECT {id_column}
            FROM {table}
            GROUP BY {id_column}
            HAVING {id_column} IS NULL OR COUNT(*) > 1
        )
    """

    violations = connection.execute(query).fetchone()[0]
    assert violations == 0, f"{table} has invalid IDs"


def test_foreign_keys_are_valid(connection):
    violations = connection.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    assert violations == []


def test_churn_labels_match_churn_dates(connection):
    violations = connection.execute(
        """
        SELECT COUNT(*)
        FROM churn_outcomes
        WHERE
            (ground_truth_churn = 1 AND churn_date IS NULL)
            OR
            (ground_truth_churn = 0 AND churn_date IS NOT NULL)
        """
    ).fetchone()[0]

    assert violations == 0


def test_churn_dates_are_within_evaluation_horizon(connection):
    violations = connection.execute(
        """
        SELECT COUNT(*)
        FROM churn_outcomes
        WHERE churn_date IS NOT NULL
          AND (
              churn_date <= prediction_date
              OR churn_date > horizon_end_date
          )
        """
    ).fetchone()[0]

    assert violations == 0


def test_risk_scores_are_between_zero_and_one(connection):
    violations = connection.execute(
        """
        SELECT COUNT(*)
        FROM campaign_contacts
        WHERE risk_score IS NULL
           OR risk_score < 0
           OR risk_score > 1
        """
    ).fetchone()[0]

    assert violations == 0


def test_control_group_has_zero_offer_cost(connection):
    violations = connection.execute(
        """
        SELECT COUNT(*)
        FROM retention_outcomes ro
        JOIN campaign_contacts cc
          ON ro.contact_id = cc.contact_id
        WHERE cc.experiment_group = 'control'
          AND ro.realized_offer_cost != 0
        """
    ).fetchone()[0]

    assert violations == 0


def test_retention_values_are_valid(connection):
    violations = connection.execute(
        """
        SELECT COUNT(*)
        FROM retention_outcomes
        WHERE retained NOT IN (0, 1)
           OR realized_offer_cost < 0
           OR incremental_revenue < 0
        """
    ).fetchone()[0]

    assert violations == 0


def test_each_campaign_contact_has_one_retention_outcome(
    connection,
):
    contacts = connection.execute(
        "SELECT COUNT(*) FROM campaign_contacts"
    ).fetchone()[0]

    outcomes = connection.execute(
        "SELECT COUNT(*) FROM retention_outcomes"
    ).fetchone()[0]

    assert contacts == outcomes
