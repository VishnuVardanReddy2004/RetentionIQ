
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.schema import DB_PATH


st.set_page_config(
    page_title="RetentionIQ | Churn Analytics",
    page_icon="📊",
    layout="wide",
)

st.title("RetentionIQ")
st.caption(
    "Customer churn intelligence and retention campaign analytics"
)


@st.cache_data
def load_data():
    with sqlite3.connect(DB_PATH) as connection:
        customers = pd.read_sql_query(
            "SELECT * FROM customers", connection
        )
        contacts = pd.read_sql_query(
            "SELECT * FROM campaign_contacts", connection
        )
        churn = pd.read_sql_query(
            "SELECT * FROM churn_outcomes", connection
        )
        retention = pd.read_sql_query(
            """
            SELECT
                rc.*,
                cc.customer_id,
                cc.subscription_id,
                cc.offer_id,
                cc.experiment_group,
                cc.contact_status,
                cc.risk_score
            FROM retention_outcomes rc
            JOIN campaign_contacts cc
                ON rc.contact_id = cc.contact_id
            """,
            connection,
        )
        offers = pd.read_sql_query(
            "SELECT * FROM offers", connection
        )
        subscriptions = pd.read_sql_query(
            "SELECT * FROM subscriptions", connection
        )

    return (
        customers,
        contacts,
        churn,
        retention,
        offers,
        subscriptions,
    )


(
    customers,
    contacts,
    churn,
    retention,
    offers,
    subscriptions,
) = load_data()


# Sidebar filters
st.sidebar.header("Dashboard Filters")

risk_min, risk_max = st.sidebar.slider(
    "Customer risk score",
    min_value=0.0,
    max_value=1.0,
    value=(0.0, 1.0),
    step=0.05,
)

filtered_contacts = contacts[
    contacts["risk_score"].between(risk_min, risk_max)
].copy()

filtered_retention = retention[
    retention["risk_score"].between(risk_min, risk_max)
].copy()

# Join churn outcomes with subscriptions for churn analysis.
churn_analysis = churn.merge(
    subscriptions[["subscription_id", "customer_id"]],
    on="subscription_id",
    how="left",
)

st.subheader("Business Overview")

total_customers = len(customers)
total_churned = int(churn["ground_truth_churn"].sum())
churn_rate = (
    total_churned / len(churn) * 100 if len(churn) else 0
)

total_contacts = len(filtered_contacts)
treatment = filtered_retention[
    filtered_retention["experiment_group"] == "treatment"
]
control = filtered_retention[
    filtered_retention["experiment_group"] == "control"
]

treatment_rate = (
    treatment["retained"].mean() * 100
    if not treatment.empty else 0
)
control_rate = (
    control["retained"].mean() * 100
    if not control.empty else 0
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Customers", f"{total_customers:,}")
col2.metric("Customers Churned", f"{total_churned:,}")
col3.metric("Churn Rate", f"{churn_rate:.2f}%")
col4.metric("Filtered Campaign Contacts", f"{total_contacts:,}")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Churn Distribution")

    churn_distribution = (
        churn[churn["ground_truth_churn"] == 1]
        ["churn_type"]
        .value_counts()
        .rename_axis("Churn Type")
        .reset_index(name="Customers")
    )

    if not churn_distribution.empty:
        fig = px.pie(
            churn_distribution,
            names="Churn Type",
            values="Customers",
            title="Voluntary vs Involuntary Churn",
            hole=0.4,
        )
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("No churn events found.")

with right:
    st.subheader("Customer Risk Distribution")

    fig = px.histogram(
        filtered_contacts,
        x="risk_score",
        nbins=20,
        title="Risk Scores of Campaign-Eligible Customers",
        labels={"risk_score": "Risk Score"},
    )
    st.plotly_chart(fig, width="stretch")

st.divider()

st.subheader("Retention Experiment")

experiment_summary = (
    filtered_retention.groupby("experiment_group")
    .agg(
        contacts=("contact_id", "count"),
        retention_rate=("retained", "mean"),
        offer_cost=("realized_offer_cost", "sum"),
    )
    .reset_index()
)

if not experiment_summary.empty:
    experiment_summary["retention_rate"] *= 100

    fig = px.bar(
        experiment_summary,
        x="experiment_group",
        y="retention_rate",
        color="experiment_group",
        text="retention_rate",
        title="Retention Rate by Experiment Group",
        labels={
            "experiment_group": "Experiment Group",
            "retention_rate": "Retention Rate (%)",
        },
    )
    fig.update_traces(texttemplate="%{text:.2f}%")
    st.plotly_chart(fig, width="stretch")

    st.dataframe(
        experiment_summary,
        width="stretch",
        hide_index=True,
    )

    st.caption(
        "Treatment effects are simulated. "
        "These results are not evidence of real-world causality."
    )

st.divider()

st.subheader("Offer Performance")

offer_summary = (
    filtered_retention.groupby("offer_id")
    .agg(
        contacts=("contact_id", "count"),
        retained_customers=("retained", "sum"),
        offer_cost=("realized_offer_cost", "sum"),
        retention_rate=("retained", "mean"),
    )
    .reset_index()
)

offer_summary["retention_rate"] *= 100

offer_summary = offer_summary.merge(
    offers[["offer_id", "offer_name"]],
    on="offer_id",
    how="left",
)

if not offer_summary.empty:
    st.dataframe(
        offer_summary[
            [
                "offer_name",
                "contacts",
                "retained_customers",
                "retention_rate",
                "offer_cost",
            ]
        ],
        width="stretch",
        hide_index=True,
    )

st.divider()

st.subheader("Campaign Contact Details")

st.dataframe(
    filtered_contacts.sort_values(
        "risk_score", ascending=False
    ),
    width="stretch",
    hide_index=True,
)

st.download_button(
    "Download filtered campaign contacts (CSV)",
    data=filtered_contacts.to_csv(index=False).encode("utf-8"),
    file_name="retentioniq_campaign_contacts.csv",
    mime="text/csv",
)

st.caption(
    "RetentionIQ | Synthetic demonstration data | "
    "Fixed seed: 20261022"
)
