
import random
import sqlite3
from datetime import date, timedelta

import numpy as np

from src.schema import DB_PATH, create_database


# ============================================================
# CONFIGURATION
# ============================================================

SEED = 20261022
CUSTOMER_COUNT = 20000
CAMPAIGN_DATE = date(2026, 10, 1)
HORIZON_END = date(2026, 12, 30)

random.seed(SEED)
np.random.seed(SEED)


# ============================================================
# DATABASE RESET
# ============================================================

def reset_database():
    create_database()

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")

        columns = [
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(campaign_contacts)"
            ).fetchall()
        ]

        if "risk_score" not in columns:
            connection.execute("""
                ALTER TABLE campaign_contacts
                ADD COLUMN risk_score REAL NOT NULL DEFAULT 0.0
                CHECK (risk_score >= 0.0 AND risk_score <= 1.0)
            """)

        tables = [
            "retention_outcomes",
            "churn_outcomes",
            "campaign_contacts",
            "eligibility_rules",
            "offers",
            "support_cases",
            "billing_events",
            "usage_snapshots",
            "subscriptions",
            "customers",
        ]

        for table in tables:
            connection.execute(f"DELETE FROM {table}")

        connection.commit()
        connection.execute("PRAGMA foreign_keys = ON")

    print("Database cleared successfully.")


# ============================================================
# CUSTOMERS
# ============================================================

def random_signup_date():
    start_date = CAMPAIGN_DATE - timedelta(days=18 * 30)
    days = (CAMPAIGN_DATE - start_date).days

    return start_date + timedelta(
        days=random.randint(0, days)
    )


def generate_customers(count=CUSTOMER_COUNT):
    regions = ["North", "South", "East", "West", "Central"]
    segments = ["Consumer", "Small Business", "Enterprise"]
    channels = ["Website", "Referral", "Social Media", "Partner"]

    customers = []

    for number in range(1, count + 1):
        customers.append((
            f"CUS-{number:06d}",
            random_signup_date().isoformat(),
            random.choice(regions),
            random.choice(segments),
            random.choice(channels),
            CAMPAIGN_DATE.isoformat(),
        ))

    return customers


def save_customers(customers):
    with sqlite3.connect(DB_PATH) as connection:
        connection.executemany("""
            INSERT INTO customers
            (
                customer_id,
                signup_date,
                region,
                customer_segment,
                acquisition_channel,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, customers)


# ============================================================
# SUBSCRIPTIONS
# ============================================================

def generate_subscriptions(customers):
    plans = {
        "Basic": 299.0,
        "Standard": 599.0,
        "Premium": 999.0,
        "Enterprise": 1999.0,
    }

    subscriptions = []

    for customer in customers:
        plan = random.choice(list(plans.keys()))

        subscriptions.append((
            f"SUB-{customer[0]}-01",
            customer[0],
            "Mobile",
            plan,
            customer[1],
            None,
            plans[plan],
            "active",
        ))

    return subscriptions


def save_subscriptions(subscriptions):
    with sqlite3.connect(DB_PATH) as connection:
        connection.executemany("""
            INSERT INTO subscriptions
            (
                subscription_id,
                customer_id,
                product_name,
                plan_type,
                start_date,
                end_date,
                monthly_price,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, subscriptions)


# ============================================================
# USAGE SNAPSHOTS
# ============================================================

def generate_usage_snapshots(subscriptions):
    snapshots = []

    for subscription in subscriptions:
        subscription_id = subscription[0]
        start_date = date.fromisoformat(subscription[4])

        behavior = random.choices(
            ["declining", "stable", "increasing"],
            weights=[40, 35, 25],
            k=1,
        )[0]

        current = date(start_date.year, start_date.month, 1)
        final_month = date(2026, 9, 1)

        base_usage = random.randint(180, 400)
        month_number = 0

        while current <= final_month:
            if behavior == "declining":
                usage = base_usage * (0.90 ** month_number)
            elif behavior == "increasing":
                usage = base_usage * (1.04 ** month_number)
            else:
                usage = base_usage + random.randint(-20, 20)

            usage += random.randint(-8, 8)
            usage = max(10, min(500, int(usage)))

            snapshot_day = random.randint(1, 28)

            snapshot_date = date(
                current.year,
                current.month,
                snapshot_day,
            )

            snapshots.append((
                f"SNAP-{subscription_id}-{current.year}-{current.month:02d}",
                subscription_id,
                snapshot_date.isoformat(),
                usage,
                random.randint(1, 30),
            ))

            month_number += 1

            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(
                    current.year,
                    current.month + 1,
                    1,
                )

    return snapshots


def save_usage_snapshots(snapshots):
    with sqlite3.connect(DB_PATH) as connection:
        connection.executemany("""
            INSERT INTO usage_snapshots
            (
                snapshot_id,
                subscription_id,
                snapshot_date,
                usage_units,
                active_days
            )
            VALUES (?, ?, ?, ?, ?)
        """, snapshots)


# ============================================================
# BILLING EVENTS
# ============================================================

def generate_billing_events(subscriptions):
    events = []
    event_number = 1

    for subscription in subscriptions:
        subscription_id = subscription[0]
        monthly_price = subscription[6]
        start_date = date.fromisoformat(subscription[4])

        current = date(start_date.year, start_date.month, 1)

        while current <= CAMPAIGN_DATE:
            events.append((
                f"BILL-{event_number:08d}",
                subscription_id,
                current.isoformat(),
                "invoice",
                monthly_price,
                "not_applicable",
            ))
            event_number += 1

            payment_status = random.choices(
                ["paid", "overdue", "failed"],
                weights=[85, 10, 5],
                k=1,
            )[0]

            payment_date = current + timedelta(days=5)

            events.append((
                f"BILL-{event_number:08d}",
                subscription_id,
                payment_date.isoformat(),
                "payment",
                monthly_price,
                payment_status,
            ))
            event_number += 1

            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(
                    current.year,
                    current.month + 1,
                    1,
                )

    return events


def save_billing_events(events):
    with sqlite3.connect(DB_PATH) as connection:
        connection.executemany("""
            INSERT INTO billing_events
            (
                billing_event_id,
                subscription_id,
                event_date,
                event_type,
                amount,
                payment_status
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, events)


# ============================================================
# SUPPORT CASES
# ============================================================

def generate_support_cases(customers):
    cases = []
    case_number = 1

    for customer in customers:
        if random.random() >= 0.40:
            continue

        number_of_cases = random.randint(1, 3)

        for _ in range(number_of_cases):
            signup_date = date.fromisoformat(customer[1])

            earliest_open_date = max(
                signup_date,
                CAMPAIGN_DATE - timedelta(days=180),
            )

            latest_open_date = CAMPAIGN_DATE - timedelta(days=1)

            if earliest_open_date > latest_open_date:
                continue

            available_days = (
                latest_open_date - earliest_open_date
            ).days

            opened_date = earliest_open_date + timedelta(
                days=random.randint(0, available_days)
            )

            severity = random.choices(
                ["low", "medium", "high", "critical"],
                weights=[35, 30, 25, 10],
                k=1,
            )[0]

            status = random.choice([
                "open",
                "in_progress",
                "resolved",
            ])

            closed_at = None

            if status == "resolved":
                closed_date = min(
                    opened_date + timedelta(
                        days=random.randint(1, 10)
                    ),
                    CAMPAIGN_DATE - timedelta(days=1),
                )
                closed_at = closed_date.isoformat()

            cases.append((
                f"CASE-{case_number:08d}",
                customer[0],
                opened_date.isoformat(),
                closed_at,
                random.choice([
                    "Billing",
                    "Technical",
                    "Network",
                    "Account",
                    "Cancellation",
                ]),
                severity,
                status,
            ))

            case_number += 1

    return cases


def save_support_cases(cases):
    with sqlite3.connect(DB_PATH) as connection:
        connection.executemany("""
            INSERT INTO support_cases
            (
                support_case_id,
                customer_id,
                opened_at,
                closed_at,
                issue_type,
                severity,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, cases)


# ============================================================
# OFFERS AND ELIGIBILITY RULES
# ============================================================

def generate_offers():
    offers = [
        (
            "OFF-2026-000001",
            "10 Percent Discount",
            10.0,
            100.0,
            "2026-01-01",
            "2026-12-31",
        ),
        (
            "OFF-2026-000002",
            "20 Percent Discount",
            20.0,
            200.0,
            "2026-01-01",
            "2026-12-31",
        ),
        (
            "OFF-2026-000003",
            "Loyalty Offer",
            15.0,
            150.0,
            "2026-01-01",
            "2026-12-31",
        ),
    ]

    rules = [
        (
            "RULE-000001",
            "OFF-2026-000001",
            0.40,
            100.0,
            299.0,
            "2026-01-01",
            "2026-12-31",
        ),
        (
            "RULE-000002",
            "OFF-2026-000002",
            0.70,
            200.0,
            599.0,
            "2026-01-01",
            "2026-12-31",
        ),
        (
            "RULE-000003",
            "OFF-2026-000003",
            0.50,
            150.0,
            599.0,
            "2026-01-01",
            "2026-12-31",
        ),
    ]

    return offers, rules


def save_offers_and_rules(offers, rules):
    with sqlite3.connect(DB_PATH) as connection:
        connection.executemany("""
            INSERT INTO offers
            (
                offer_id,
                offer_name,
                discount_percent,
                offer_cost,
                start_date,
                end_date
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, offers)

        connection.executemany("""
            INSERT INTO eligibility_rules
            (
                rule_id,
                offer_id,
                min_risk_score,
                max_offer_cost,
                min_monthly_price,
                effective_from,
                effective_to
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, rules)


# ============================================================
# CUSTOMER RISK SCORES
# ============================================================

def calculate_customer_risk_scores(
    customers,
    subscriptions,
    usage_snapshots,
    billing_events,
    support_cases,
):
    recent_start = CAMPAIGN_DATE - timedelta(days=90)

    snapshots_by_subscription = {}

    for snapshot in usage_snapshots:
        snapshot_date = date.fromisoformat(snapshot[2])

        if snapshot_date < CAMPAIGN_DATE:
            snapshots_by_subscription.setdefault(
                snapshot[1], []
            ).append(snapshot)

    billing_by_subscription = {}

    for event in billing_events:
        event_date = date.fromisoformat(event[2])

        if (
            event[3] == "payment"
            and recent_start <= event_date < CAMPAIGN_DATE
        ):
            billing_by_subscription.setdefault(
                event[1], []
            ).append(event)

    cases_by_customer = {}

    for case in support_cases:
        opened_date = date.fromisoformat(case[2])

        if recent_start <= opened_date < CAMPAIGN_DATE:
            cases_by_customer.setdefault(
                case[1], []
            ).append(case)

    subscriptions_by_customer = {
        subscription[1]: subscription
        for subscription in subscriptions
    }

    customer_scores = {}

    for customer in customers:
        customer_id = customer[0]

        subscription = subscriptions_by_customer.get(customer_id)

        if subscription is None:
            customer_scores[customer_id] = 0.0
            continue

        subscription_id = subscription[0]

        history = sorted(
            snapshots_by_subscription.get(
                subscription_id, []
            ),
            key=lambda item: item[2],
        )

        usage_decline = 0.0

        if len(history) >= 2:
            previous_usage = history[-2][3]
            latest_usage = history[-1][3]

            if previous_usage > 0 and latest_usage < previous_usage:
                raw_decline = (
                    previous_usage - latest_usage
                ) / previous_usage

                usage_decline = min(
                    raw_decline / 0.20,
                    1.0,
                )

        recent_payments = billing_by_subscription.get(
            subscription_id, []
        )

        billing_risk = 0.0

        if recent_payments:
            risky_payments = sum(
                1
                for event in recent_payments
                if event[5] in ("overdue", "failed")
            )

            billing_risk = risky_payments / len(recent_payments)

        support_risk = 0.0

        for case in cases_by_customer.get(customer_id, []):
            if case[5] in ("high", "critical"):
                support_risk += 0.50

            if case[6] in ("open", "in_progress"):
                support_risk += 0.25

        support_risk = min(support_risk, 1.0)

        score = (
            0.50 * usage_decline
            + 0.30 * billing_risk
            + 0.20 * support_risk
        )

        customer_scores[customer_id] = round(
            min(max(score, 0.0), 1.0),
            4,
        )

    return customer_scores


def print_risk_distribution(customer_scores):
    scores = list(customer_scores.values())

    if not scores:
        print("No risk scores were generated.")
        return

    print("\nRisk score distribution for all customers:")
    print("Total customers:", len(scores))
    print("Minimum risk:", min(scores))
    print("Average risk:", round(sum(scores) / len(scores), 4))
    print("Maximum risk:", max(scores))
    print("Scores >= 0.40:", sum(s >= 0.40 for s in scores))
    print("Scores >= 0.50:", sum(s >= 0.50 for s in scores))
    print("Scores >= 0.70:", sum(s >= 0.70 for s in scores))


# ============================================================
# CAMPAIGN CONTACTS
# ============================================================

def generate_campaign_contacts(
    customers,
    subscriptions,
    offers,
    rules,
    usage_snapshots,
    billing_events,
    support_cases,
):
    customer_scores = calculate_customer_risk_scores(
        customers,
        subscriptions,
        usage_snapshots,
        billing_events,
        support_cases,
    )

    print_risk_distribution(customer_scores)

    subscriptions_by_customer = {
        subscription[1]: subscription
        for subscription in subscriptions
    }

    offers_by_id = {
        offer[0]: offer
        for offer in offers
    }

    eligible_customers = []

    for customer in customers:
        customer_id = customer[0]

        subscription = subscriptions_by_customer.get(customer_id)

        if subscription is None:
            continue

        risk_score = customer_scores[customer_id]
        monthly_price = subscription[6]
        eligible_offers = []

        for rule in rules:
            offer = offers_by_id.get(rule[1])

            if offer is None:
                continue

            rule_start = date.fromisoformat(rule[5])
            rule_end = (
                date.fromisoformat(rule[6])
                if rule[6]
                else date.max
            )

            offer_start = date.fromisoformat(offer[4])
            offer_end = date.fromisoformat(offer[5])

            is_eligible = (
                risk_score >= rule[2]
                and offer[3] <= rule[3]
                and monthly_price >= rule[4]
                and rule_start <= CAMPAIGN_DATE <= rule_end
                and offer_start <= CAMPAIGN_DATE <= offer_end
            )

            if is_eligible:
                eligible_offers.append((rule, offer))

        if eligible_offers:
            eligible_customers.append({
                "customer": customer,
                "subscription": subscription,
                "risk_score": risk_score,
                "eligible_offers": eligible_offers,
            })

    risk_bands = {
        "low": [],
        "medium": [],
        "high": [],
    }

    for item in eligible_customers:
        risk = item["risk_score"]

        if risk < 0.40:
            risk_bands["low"].append(item)
        elif risk < 0.60:
            risk_bands["medium"].append(item)
        else:
            risk_bands["high"].append(item)

    contacts = []
    contact_number = 1

    for band in risk_bands.values():
        random.shuffle(band)

        for index, item in enumerate(band):
            customer = item["customer"]
            subscription = item["subscription"]
            risk_score = item["risk_score"]
            eligible_offers = item["eligible_offers"]

            experiment_group = (
                "treatment" if index % 2 == 0
                else "control"
            )

            rule, offer = random.choice(eligible_offers)

            if experiment_group == "treatment":
                contact_status = random.choices(
                    ["sent", "delivered", "failed", "not_sent"],
                    weights=[50, 30, 10, 10],
                    k=1,
                )[0]
            else:
                contact_status = "not_sent"

            contacts.append((
                f"CONTACT-{contact_number:08d}",
                customer[0],
                subscription[0],
                offer[0],
                CAMPAIGN_DATE.isoformat(),
                experiment_group,
                contact_status,
                risk_score,
            ))

            contact_number += 1

    random.shuffle(contacts)

    return contacts


def save_campaign_contacts(contacts):
    with sqlite3.connect(DB_PATH) as connection:
        connection.executemany("""
            INSERT INTO campaign_contacts
            (
                contact_id,
                customer_id,
                subscription_id,
                offer_id,
                campaign_date,
                experiment_group,
                contact_status,
                risk_score
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, contacts)


# ============================================================
# CHURN OUTCOMES
# ============================================================

def generate_churn_outcomes(
    subscriptions,
    contacts,
    customer_scores,
):
    outcomes = []

    risk_by_subscription = {
        subscription[0]: customer_scores.get(
            subscription[1], 0.0
        )
        for subscription in subscriptions
    }

    treated_subscriptions = {
        contact[2]
        for contact in contacts
        if contact[5] == "treatment"
        and contact[6] in ("sent", "delivered")
    }

    for outcome_number, subscription in enumerate(
        subscriptions, start=1
    ):
        subscription_id = subscription[0]
        risk_score = risk_by_subscription.get(
            subscription_id, 0.0
        )

        if risk_score < 0.20:
            churn_probability = 0.05
        elif risk_score < 0.40:
            churn_probability = 0.10
        elif risk_score < 0.60:
            churn_probability = 0.15
        else:
            churn_probability = 0.20

        # This is an explicitly simulated treatment effect.
        if subscription_id in treated_subscriptions:
            churn_probability *= 0.70

        churned = random.random() < churn_probability

        churn_date = None
        churn_type = "none"
        ground_truth = 0

        if churned:
            churn_date = (
                CAMPAIGN_DATE
                + timedelta(days=random.randint(1, 90))
            ).isoformat()

            churn_type = random.choices(
                ["voluntary", "involuntary"],
                weights=[70, 30],
                k=1,
            )[0]

            ground_truth = 1

        outcomes.append((
            f"CHURN-{outcome_number:08d}",
            subscription_id,
            CAMPAIGN_DATE.isoformat(),
            HORIZON_END.isoformat(),
            churn_date,
            churn_type,
            ground_truth,
        ))

    return outcomes


def save_churn_outcomes(outcomes):
    with sqlite3.connect(DB_PATH) as connection:
        connection.executemany("""
            INSERT INTO churn_outcomes
            (
                churn_outcome_id,
                subscription_id,
                prediction_date,
                horizon_end_date,
                churn_date,
                churn_type,
                ground_truth_churn
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, outcomes)


# ============================================================
# RETENTION OUTCOMES
# ============================================================


def generate_retention_outcomes(
    contacts,
    churn_outcomes,
    subscriptions,
):
    """
    Generate one retention outcome per campaign contact.

    The incremental_revenue database column stores estimated
    subscription revenue during the evaluation horizon.
    It does not represent proven causal incremental revenue.
    """

    churn_by_subscription = {
        outcome[1]: outcome
        for outcome in churn_outcomes
    }

    subscription_by_id = {
        subscription[0]: subscription
        for subscription in subscriptions
    }

    retention_outcomes = []

    for number, contact in enumerate(contacts, start=1):
        contact_id = contact[0]
        subscription_id = contact[2]
        experiment_group = contact[5]
        contact_status = contact[6]

        churn_outcome = churn_by_subscription.get(
            subscription_id
        )

        if churn_outcome is None:
            raise ValueError(
                f"Missing churn outcome for subscription "
                f"{subscription_id}"
            )

        subscription = subscription_by_id.get(
            subscription_id
        )

        if subscription is None:
            raise ValueError(
                f"Missing subscription record for "
                f"{subscription_id}"
            )

        monthly_price = float(subscription[6])

        churn_date = (
            date.fromisoformat(churn_outcome[4])
            if churn_outcome[4]
            else None
        )

        # Retained means no churn during the evaluation horizon.
        retained = int(
            churn_date is None
            or churn_date > HORIZON_END
        )

        # Count offer costs only for treatment contacts
        # whose offer was sent or delivered.
        offer_cost = (
            100.0
            if (
                experiment_group == "treatment"
                and contact_status in ("sent", "delivered")
            )
            else 0.0
        )

        # Estimate revenue from the campaign date until churn
        # or the end of the evaluation horizon.
        revenue_end_date = (
            min(churn_date, HORIZON_END)
            if churn_date is not None
            else HORIZON_END
        )

        active_days = max(
            0,
            (revenue_end_date - CAMPAIGN_DATE).days,
        )

        estimated_revenue = round(
            monthly_price * active_days / 30.0,
            2,
        )

        outcome_reason = (
            "retained" if retained else "churned"
        )

        retention_outcomes.append((
            f"RET-{number:08d}",
            contact_id,
            HORIZON_END.isoformat(),
            retained,
            offer_cost,
            estimated_revenue,
            outcome_reason,
        ))

    return retention_outcomes



def save_retention_outcomes(outcomes):
    with sqlite3.connect(DB_PATH) as connection:
        connection.executemany("""
            INSERT INTO retention_outcomes
            (
                retention_outcome_id,
                contact_id,
                outcome_date,
                retained,
                realized_offer_cost,
                incremental_revenue,
                outcome_reason
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, outcomes)


# ============================================================
# REPORTING
# ============================================================

def print_table_counts():
    tables = [
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

    with sqlite3.connect(DB_PATH) as connection:
        for table in tables:
            count = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            print(f"{table}: {count}")


def print_experiment_groups(contacts):
    treatment_count = sum(
        1 for contact in contacts
        if contact[5] == "treatment"
    )

    control_count = sum(
        1 for contact in contacts
        if contact[5] == "control"
    )

    print("\nCampaign experiment groups:")
    print("Treatment:", treatment_count)
    print("Control:", control_count)


# ============================================================
# MAIN
# ============================================================

def main():
    reset_database()

    customers = generate_customers(CUSTOMER_COUNT)
    save_customers(customers)

    subscriptions = generate_subscriptions(customers)
    save_subscriptions(subscriptions)

    usage_snapshots = generate_usage_snapshots(subscriptions)
    save_usage_snapshots(usage_snapshots)

    billing_events = generate_billing_events(subscriptions)
    save_billing_events(billing_events)

    support_cases = generate_support_cases(customers)
    save_support_cases(support_cases)

    offers, rules = generate_offers()
    save_offers_and_rules(offers, rules)

    contacts = generate_campaign_contacts(
        customers,
        subscriptions,
        offers,
        rules,
        usage_snapshots,
        billing_events,
        support_cases,
    )
    save_campaign_contacts(contacts)

    customer_scores = calculate_customer_risk_scores(
        customers,
        subscriptions,
        usage_snapshots,
        billing_events,
        support_cases,
    )

    churn_outcomes = generate_churn_outcomes(
        subscriptions,
        contacts,
        customer_scores,
    )
    save_churn_outcomes(churn_outcomes)

    retention_outcomes = generate_retention_outcomes(
        contacts,
        churn_outcomes,
        subscriptions,
    )
    save_retention_outcomes(retention_outcomes)

    print("\nData generation completed.")
    print("Random seed:", SEED)
    print("Customers generated:", len(customers))
    print("Eligible campaign contacts:", len(contacts))

    print_experiment_groups(contacts)

    if contacts:
        average_risk = sum(
            float(contact[7]) for contact in contacts
        ) / len(contacts)

        print(
            "Average eligible-contact risk score:",
            round(average_risk, 4),
        )

    print("\nTable counts:")
    print_table_counts()


if __name__ == "__main__":
    main()
