# src/validate_data.py

import sqlite3

from src.schema import DB_PATH


def run_check(connection, name, query, expected=0):
    result = connection.execute(query).fetchone()[0]
    passed = result == expected

    print(
        f"{'PASS' if passed else 'FAIL'}: {name} "
        f"(found: {result}, expected: {expected})"
    )

    return passed


def main():
    checks = []

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        required_tables = [
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
        ]

        existing_tables = {
            row[0]
            for row in connection.execute("""
                SELECT name FROM sqlite_master
                WHERE type = 'table'
            """).fetchall()
        }

        checks.append(
            len(set(required_tables) & existing_tables) == len(required_tables)
        )
        print(
            f"{'PASS' if checks[-1] else 'FAIL'}: All 10 required tables exist"
        )

        unique_id_checks = [
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
        ]

        for table, column in unique_id_checks:
            query = f"""
                SELECT COUNT(*) FROM (
                    SELECT {column}
                    FROM {table}
                    GROUP BY {column}
                    HAVING COUNT(*) > 1
                )
            """
            checks.append(
                run_check(
                    connection,
                    f"Unique IDs: {table}",
                    query,
                )
            )

        foreign_keys = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        checks.append(len(foreign_keys) == 0)
        print(
            f"{'PASS' if checks[-1] else 'FAIL'}: Foreign key integrity "
            f"(violations: {len(foreign_keys)})"
        )

        checks.append(run_check(
            connection,
            "Churn dates within evaluation horizon",
            """
            SELECT COUNT(*)
            FROM churn_outcomes
            WHERE churn_date IS NOT NULL
              AND (
                churn_date <= prediction_date
                OR churn_date > horizon_end_date
              )
            """,
        ))

        checks.append(run_check(
            connection,
            "Churn labels consistent",
            """
            SELECT COUNT(*)
            FROM churn_outcomes
            WHERE
              (ground_truth_churn = 1 AND churn_date IS NULL)
              OR (ground_truth_churn = 0 AND churn_date IS NOT NULL)
              OR (ground_truth_churn = 1 AND churn_type = 'none')
              OR (ground_truth_churn = 0 AND churn_type != 'none')
            """,
        ))

        checks.append(run_check(
            connection,
            "Retention values valid",
            """
            SELECT COUNT(*)
            FROM retention_outcomes
            WHERE retained NOT IN (0, 1)
               OR realized_offer_cost < 0
               OR incremental_revenue < 0
            """,
        ))

        checks.append(run_check(
            connection,
            "Campaign risk scores within 0-1",
            """
            SELECT COUNT(*)
            FROM campaign_contacts
            WHERE risk_score < 0 OR risk_score > 1
            """,
        ))

        checks.append(run_check(
            connection,
            "Campaign offer and risk eligibility",
            """
            SELECT COUNT(*)
            FROM campaign_contacts c
            JOIN subscriptions s
              ON c.subscription_id = s.subscription_id
            JOIN offers o
              ON c.offer_id = o.offer_id
            JOIN eligibility_rules e
              ON e.offer_id = o.offer_id
            WHERE o.offer_cost > e.max_offer_cost
               OR s.monthly_price < e.min_monthly_price
               OR c.risk_score < e.min_risk_score
               OR c.campaign_date < e.effective_from
               OR c.campaign_date > e.effective_to
               OR c.campaign_date < o.start_date
               OR c.campaign_date > o.end_date
            """,
        ))

        checks.append(run_check(
            connection,
            "Control group has zero offer cost",
            """
            SELECT COUNT(*)
            FROM campaign_contacts c
            JOIN retention_outcomes r
              ON c.contact_id = r.contact_id
            WHERE c.experiment_group = 'control'
              AND r.realized_offer_cost != 0
            """,
        ))

    passed = sum(checks)
    total = len(checks)

    print(f"\nValidation summary: {passed}/{total} checks passed.")

    if passed != total:
        raise SystemExit("Validation failed. Review the failed checks.")


if __name__ == "__main__":
    main()