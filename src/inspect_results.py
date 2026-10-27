
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "retentioniq.db"

with sqlite3.connect(DB_PATH) as connection:
    cursor = connection.cursor()

    print("\n--- Churn Distribution ---")
    cursor.execute("""
        SELECT churn_type, ground_truth_churn, COUNT(*)
        FROM churn_outcomes
        GROUP BY churn_type, ground_truth_churn
        ORDER BY churn_type
    """)
    for row in cursor.fetchall():
        print(row)

    print("\n--- Experiment Groups ---")
    cursor.execute("""
        SELECT experiment_group, COUNT(*)
        FROM campaign_contacts
        GROUP BY experiment_group
    """)
    for row in cursor.fetchall():
        print(row)

    print("\n--- Retention by Experiment Group ---")
    cursor.execute("""
        SELECT
            c.experiment_group,
            COUNT(*) AS total_contacts,
            ROUND(AVG(r.retained) * 100, 2) AS retention_percent,
            SUM(r.realized_offer_cost) AS total_offer_cost
        FROM campaign_contacts c
        JOIN retention_outcomes r
            ON c.contact_id = r.contact_id
        GROUP BY c.experiment_group
    """)
    for row in cursor.fetchall():
        print(row)
    
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
    """)

    for row in cursor.fetchall():
        print(row)
