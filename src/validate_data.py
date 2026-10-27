
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

        # 1. Check that all required tables exist.
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
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
            """).fetchall()
        }

        checks.append(
            len(set(required_tables) & existing_tables)
            == len(required_tables)
        )

        print(
            f"{'PASS' if checks[-1] else 'FAIL'}: "
            "All 10 required tables exist"
        )

        # 2. Check that IDs are unique.
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
                SELECT COUNT(*)
                FROM (
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

        # 3. Check foreign-key integrity.
        foreign_keys = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        checks.append(len(foreign_keys) == 0)

        print(
            f"{'PASS' if checks[-1] else 'FAIL'}: "
            f"Foreign key integrity "
            f"(violations: {len(foreign_keys)})"
        )

        # 4. Check that campaign contact IDs and foreign keys are present.
        checks.append(
            run_check(
                connection,
                "Campaign contact IDs are not null",
                """
                SELECT COUNT(*)
                FROM campaign_contacts
                WHERE contact_id IS NULL
                   OR customer_id IS NULL
                   OR subscription_id IS NULL
                   OR offer_id IS NULL
                """,
            )
        )

        # 5. Check valid experiment group values.
        checks.append(
            run_check(
                connection,
                "Valid experiment group values",
                """
                SELECT COUNT(*)
                FROM campaign_contacts
                WHERE experiment_group NOT IN ('treatment', 'control')
                   OR experiment_group IS NULL
                """,
            )
        )

        # 6. Every campaign contact must have exactly one retention outcome.
        # This correctly detects both missing and duplicate outcomes.
        checks.append(
            run_check(
                connection,
                "Exactly one retention outcome per campaign contact",
                """
                SELECT COUNT(*)
                FROM campaign_contacts c
                WHERE (
                    SELECT COUNT(*)
                    FROM retention_outcomes r
                    WHERE r.contact_id = c.contact_id
                ) != 1
                """,
            )
        )

        # 7. Prevent a subscription from being assigned to both groups
        # on the same campaign date.
        checks.append(
            run_check(
                connection,
                "No conflicting experiment assignments per subscription and date",
                """
                SELECT COUNT(*)
                FROM (
                    SELECT subscription_id, campaign_date
                    FROM campaign_contacts
                    GROUP BY subscription_id, campaign_date
                    HAVING COUNT(DISTINCT experiment_group) > 1
                )
                """,
            )
        )

        # 8. Every campaign contact must satisfy at least one effective
        # eligibility rule for the selected offer.
        checks.append(
            run_check(
                connection,
                "Campaign contacts have an effective eligibility rule",
                """
                SELECT COUNT(*)
                FROM campaign_contacts c
                JOIN subscriptions s
                  ON c.subscription_id = s.subscription_id
                JOIN offers o
                  ON c.offer_id = o.offer_id
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM eligibility_rules e
                    WHERE e.offer_id = c.offer_id
                      AND c.risk_score >= e.min_risk_score
                      AND o.offer_cost <= e.max_offer_cost
                      AND s.monthly_price >= e.min_monthly_price
                      AND c.campaign_date >= e.effective_from
                      AND (
                          e.effective_to IS NULL
                          OR c.campaign_date <= e.effective_to
                      )
                )
                """,
            )
        )

    # 9. Print the final validation summary.
    passed = sum(checks)
    total = len(checks)

    print(f"\nValidation summary: {passed}/{total} checks passed.")

    if passed != total:
        raise SystemExit(
            "Validation failed. Review the failed checks."
        )


if __name__ == "__main__":
    main()
