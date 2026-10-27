
# src/validate_data.py

import sqlite3

from src.schema import DB_PATH


def run_check(connection, name, query, expected=0):
    """Run a SQL validation and return True when the result matches expected."""
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

        print("\n" + "=" * 65)
        print("RETENTIONIQ - DATA QUALITY AND BUSINESS RULE VALIDATION")
        print("=" * 65)

        # 1. Required tables
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

        missing_tables = len(
            set(required_tables) - existing_tables
        )

        checks.append(
            run_check(
                connection,
                "All 10 required tables exist",
                f"SELECT {missing_tables}",
            )
        )

        # 2. Primary-key uniqueness and null checks
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

            checks.append(
                run_check(
                    connection,
                    f"Non-null IDs: {table}",
                    f"""
                    SELECT COUNT(*)
                    FROM {table}
                    WHERE {column} IS NULL
                       OR TRIM({column}) = ''
                    """,
                )
            )

        # 3. Foreign-key integrity
        foreign_keys = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        checks.append(len(foreign_keys) == 0)

        print(
            f"{'PASS' if checks[-1] else 'FAIL'}: "
            f"Foreign-key integrity "
            f"(violations: {len(foreign_keys)})"
        )

        # 4. Campaign contact required fields
        checks.append(
            run_check(
                connection,
                "Campaign contact required fields",
                """
                SELECT COUNT(*)
                FROM campaign_contacts
                WHERE contact_id IS NULL
                   OR customer_id IS NULL
                   OR subscription_id IS NULL
                   OR offer_id IS NULL
                   OR campaign_date IS NULL
                   OR experiment_group IS NULL
                   OR contact_status IS NULL
                """,
            )
        )

        # 5. Customer must own the referenced subscription
        checks.append(
            run_check(
                connection,
                "Campaign customer matches subscription owner",
                """
                SELECT COUNT(*)
                FROM campaign_contacts c
                JOIN subscriptions s
                  ON c.subscription_id = s.subscription_id
                WHERE c.customer_id != s.customer_id
                """,
            )
        )

        # 6. Valid experiment groups
        checks.append(
            run_check(
                connection,
                "Valid treatment/control group values",
                """
                SELECT COUNT(*)
                FROM campaign_contacts
                WHERE experiment_group IS NULL
                   OR experiment_group NOT IN ('treatment', 'control')
                """,
            )
        )

        # 7. No treatment/control leakage for one subscription/date
        checks.append(
            run_check(
                connection,
                "No conflicting groups per subscription and campaign date",
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

        # 8. Also check leakage at customer/date level
        checks.append(
            run_check(
                connection,
                "No conflicting groups per customer and campaign date",
                """
                SELECT COUNT(*)
                FROM (
                    SELECT customer_id, campaign_date
                    FROM campaign_contacts
                    GROUP BY customer_id, campaign_date
                    HAVING COUNT(DISTINCT experiment_group) > 1
                )
                """,
            )
        )

        # 9. Every contact must have exactly one retention outcome
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

        # 10. Retention outcomes cannot reference missing contacts
        checks.append(
            run_check(
                connection,
                "Every retention outcome has a valid campaign contact",
                """
                SELECT COUNT(*)
                FROM retention_outcomes r
                LEFT JOIN campaign_contacts c
                  ON r.contact_id = c.contact_id
                WHERE c.contact_id IS NULL
                """,
            )
        )

        # 11. Churn labels and churn types must agree
        checks.append(
            run_check(
                connection,
                "Churn label and churn type consistency",
                """
                SELECT COUNT(*)
                FROM churn_outcomes
                WHERE (
                    ground_truth_churn = 1
                    AND (
                        churn_date IS NULL
                        OR churn_type NOT IN ('voluntary', 'involuntary')
                    )
                )
                OR (
                    ground_truth_churn = 0
                    AND (
                        churn_date IS NOT NULL
                        OR churn_type != 'none'
                    )
                )
                """,
            )
        )

        # 12. Churn must occur after prediction and within the horizon
        checks.append(
            run_check(
                connection,
                "Churn date is after prediction and within evaluation horizon",
                """
                SELECT COUNT(*)
                FROM churn_outcomes
                WHERE (
                    ground_truth_churn = 1
                    AND (
                        prediction_date IS NULL
                        OR horizon_end_date IS NULL
                        OR churn_date IS NULL
                        OR prediction_date >= horizon_end_date
                        OR churn_date <= prediction_date
                        OR churn_date > horizon_end_date
                    )
                )
                OR (
                    ground_truth_churn = 0
                    AND churn_date IS NOT NULL
                )
                """,
            )
        )

        # 13. Prediction date must not be later than the evaluation horizon
        checks.append(
            run_check(
                connection,
                "Evaluation horizon is not before prediction date",
                """
                SELECT COUNT(*)
                FROM churn_outcomes
                WHERE prediction_date IS NULL
                   OR horizon_end_date IS NULL
                   OR horizon_end_date < prediction_date
                """,
            )
        )

        # 14. Every campaign contact must meet an effective eligibility rule.
        # Check rule dates AND offer dates.
        checks.append(
            run_check(
                connection,
                "Campaign contacts satisfy offer eligibility rules",
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
                      AND c.campaign_date >= o.start_date
                      AND c.campaign_date <= o.end_date
                )
                """,
            )
        )

        # 15. Treatment/control assignments should not contradict contact status.
        # Treatment contacts may be assigned, sent, delivered or failed.
        # Control contacts should not have an offer sent or delivered.
        checks.append(
            run_check(
                connection,
                "Control group has no sent or delivered offers",
                """
                SELECT COUNT(*)
                FROM campaign_contacts
                WHERE experiment_group = 'control'
                  AND contact_status IN ('sent', 'delivered')
                """,
            )
        )

        # 16. Control outcomes must have zero realized offer cost
        checks.append(
            run_check(
                connection,
                "Control group has zero realized offer cost",
                """
                SELECT COUNT(*)
                FROM retention_outcomes r
                JOIN campaign_contacts c
                  ON r.contact_id = c.contact_id
                WHERE c.experiment_group = 'control'
                  AND ABS(r.realized_offer_cost) > 0.000001
                """,
            )
        )

        # 17. Realized offer cost must not be negative
        checks.append(
            run_check(
                connection,
                "Realized offer costs are non-negative",
                """
                SELECT COUNT(*)
                FROM retention_outcomes
                WHERE realized_offer_cost < 0
                """,
            )
        )

        # 18. Flag a retained customer attributed to multiple distinct offers.
        # This is a customer-level exception check; investigate each result.
        checks.append(
            run_check(
                connection,
                "No retained customer attributed to multiple distinct offers",
                """
                SELECT COUNT(*)
                FROM (
                    SELECT c.customer_id
                    FROM retention_outcomes r
                    JOIN campaign_contacts c
                      ON r.contact_id = c.contact_id
                    WHERE r.retained = 1
                      AND c.experiment_group = 'treatment'
                    GROUP BY c.customer_id
                    HAVING COUNT(DISTINCT c.offer_id) > 1
                )
                """,
            )
        )

        # 19. Allowed subscription status values
        checks.append(
            run_check(
                connection,
                "Valid subscription statuses",
                """
                SELECT COUNT(*)
                FROM subscriptions
                WHERE status NOT IN ('active', 'paused', 'cancelled')
                   OR status IS NULL
                """,
            )
        )

        # 20. Usage values must be non-negative
        checks.append(
            run_check(
                connection,
                "Valid usage snapshot values",
                """
                SELECT COUNT(*)
                FROM usage_snapshots
                WHERE usage_units < 0
                   OR active_days < 0
                   OR active_days > 31
                """,
            )
        )

        # 21. Support case dates must be ordered
        checks.append(
            run_check(
                connection,
                "Support case dates are valid",
                """
                SELECT COUNT(*)
                FROM support_cases
                WHERE closed_at IS NOT NULL
                  AND closed_at < opened_at
                """,
            )
        )

        # 22. Offer costs and dates must be valid
        checks.append(
            run_check(
                connection,
                "Offer costs and effective dates are valid",
                """
                SELECT COUNT(*)
                FROM offers
                WHERE offer_cost < 0
                   OR end_date < start_date
                """,
            )
        )

    # Final report
    passed = sum(checks)
    total = len(checks)
    failed = total - passed

    print("\n" + "=" * 65)
    print("VALIDATION SUMMARY")
    print("=" * 65)
    print(f"Total checks : {total}")
    print(f"Passed       : {passed}")
    print(f"Failed       : {failed}")

    if failed:
        raise SystemExit(
            "\nValidation failed. Review FAIL messages above."
        )

    print("\nAll validation checks passed.")


if __name__ == "__main__":
    main()
