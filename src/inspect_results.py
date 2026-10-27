
import sqlite3
from pathlib import Path

DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "retentioniq.db"
)


def print_query_results(cursor):
    for row in cursor.fetchall():
        print(row)


with sqlite3.connect(DB_PATH) as connection:
    cursor = connection.cursor()

    print("\n--- Churn Distribution ---")
    cursor.execute("""
        SELECT
            churn_type,
            ground_truth_churn,
            COUNT(*) AS customer_count
        FROM churn_outcomes
        GROUP BY churn_type, ground_truth_churn
        ORDER BY churn_type
    """)
    print_query_results(cursor)

    print("\n--- Experiment Groups ---")
    cursor.execute("""
        SELECT
            experiment_group,
            COUNT(*) AS total_contacts
        FROM campaign_contacts
        GROUP BY experiment_group
        ORDER BY experiment_group
    """)
    print_query_results(cursor)

    print("\n--- Retention by Experiment Group ---")
    cursor.execute("""
        SELECT
            c.experiment_group,
            COUNT(*) AS total_contacts,
            ROUND(AVG(r.retained) * 100, 2)
                AS retention_percent,
            ROUND(SUM(r.realized_offer_cost), 2)
                AS total_offer_cost
        FROM campaign_contacts c
        JOIN retention_outcomes r
            ON c.contact_id = r.contact_id
        GROUP BY c.experiment_group
        ORDER BY c.experiment_group
    """)
    print_query_results(cursor)

    print("\n--- Revenue and Offer Economics ---")
    cursor.execute("""
        SELECT
            c.experiment_group,
            COUNT(*) AS total_contacts,
            ROUND(SUM(r.incremental_revenue), 2)
                AS estimated_subscription_revenue,
            ROUND(SUM(r.realized_offer_cost), 2)
                AS total_offer_cost,
            ROUND(
                SUM(r.incremental_revenue)
                - SUM(r.realized_offer_cost),
                2
            ) AS estimated_net_value,
            ROUND(AVG(r.incremental_revenue), 2)
                AS average_revenue_per_contact,
            ROUND(AVG(r.realized_offer_cost), 2)
                AS average_offer_cost_per_contact
        FROM campaign_contacts c
        JOIN retention_outcomes r
            ON c.contact_id = r.contact_id
        GROUP BY c.experiment_group
        ORDER BY c.experiment_group
    """)
    print_query_results(cursor)

    print("\n--- Average Risk by Experiment Group ---")
    cursor.execute("""
        SELECT
            experiment_group,
            COUNT(*) AS contacts,
            ROUND(AVG(risk_score), 4) AS average_risk,
            ROUND(MIN(risk_score), 4) AS minimum_risk,
            ROUND(MAX(risk_score), 4) AS maximum_risk
        FROM campaign_contacts
        GROUP BY experiment_group
        ORDER BY experiment_group
    """)
    print_query_results(cursor)

    print("\n--- Interpretation Notes ---")
    print(
        "Estimated net value = estimated subscription revenue "
        "- realized offer cost."
    )
    print(
        "Revenue is simulated/estimated, not proven incremental "
        "revenue or profit."
    )
    print(
        "Treatment-control differences are simulation results, "
        "not proof of real-world causal impact."
    )
