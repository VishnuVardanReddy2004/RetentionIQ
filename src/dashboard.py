import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st

from src.schema import DB_PATH


# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="RetentionIQ | Churn Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

PURPLE = "#5B35B5"
PURPLE_LIGHT = "#A78BFA"
BLUE = "#3B82F6"
RED = "#E05260"
GREEN = "#168A52"
AMBER = "#D99116"
TEXT = "#1F2340"
MUTED = "#68708A"
BORDER = "#E7E8F0"


# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'DM Sans', sans-serif;
    }}

    .stApp {{
        background: #F8F9FD;
        color: {TEXT};
    }}

    [data-testid="stSidebar"] {{
        background: linear-gradient(
            180deg, #F1EDFF 0%, #FAF9FF 100%
        );
        border-right: 1px solid #E5DFF8;
    }}

    .hero {{
        background: linear-gradient(
            115deg, #392078 0%, #5B35B5 58%, #9475EE 100%
        );
        color: white;
        padding: 28px 30px;
        border-radius: 18px;
        margin-bottom: 24px;
        box-shadow: 0 8px 24px rgba(76, 48, 155, 0.15);
    }}

    .hero h1 {{
        color: white;
        font-size: 2.3rem;
        font-weight: 700;
        margin: 0 0 6px 0;
    }}

    .hero p {{
        color: #E9E1FF;
        font-size: 1rem;
        margin: 0;
    }}

    .section-heading {{
        color: {TEXT};
        font-size: 1.4rem;
        font-weight: 700;
        margin: 12px 0 16px 0;
    }}

    .kpi-card {{
        background: white;
        border: 1px solid {BORDER};
        border-top: 4px solid {PURPLE};
        border-radius: 15px;
        padding: 19px;
        min-height: 125px;
        box-shadow: 0 3px 12px rgba(28, 31, 61, 0.04);
    }}

    .kpi-label {{
        color: {MUTED};
        font-size: 0.88rem;
        font-weight: 600;
        margin-bottom: 10px;
    }}

    .kpi-value {{
        color: {TEXT};
        font-size: 1.9rem;
        line-height: 1.2;
        font-weight: 700;
    }}

    .kpi-note {{
        color: {MUTED};
        font-size: 0.78rem;
        margin-top: 8px;
    }}

    .panel {{
        background: white;
        border: 1px solid {BORDER};
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 3px 12px rgba(28, 31, 61, 0.025);
        margin-bottom: 12px;
    }}

    .insight-card {{
        background: white;
        border: 1px solid {BORDER};
        border-left: 4px solid {PURPLE};
        border-radius: 12px;
        padding: 15px;
        min-height: 112px;
    }}

    .insight-title {{
        color: {MUTED};
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 7px;
    }}

    .insight-value {{
        color: {TEXT};
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 5px;
        overflow-wrap: anywhere;
    }}

    .insight-detail {{
        color: {MUTED};
        font-size: 0.82rem;
    }}

    div[data-testid="stDataFrame"] {{
        border: 1px solid {BORDER};
        border-radius: 12px;
        overflow: hidden;
    }}

    div.stButton > button,
    div.stDownloadButton > button {{
        border-radius: 10px;
        font-weight: 600;
    }}

    hr {{
        border-color: {BORDER};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# LOAD DATABASE DATA
# =========================================================
@st.cache_data
def load_data():
    with sqlite3.connect(DB_PATH) as connection:

        customers = pd.read_sql_query(
            "SELECT * FROM customers",
            connection,
        )

        contacts = pd.read_sql_query(
            "SELECT * FROM campaign_contacts",
            connection,
        )

        churn = pd.read_sql_query(
            "SELECT * FROM churn_outcomes",
            connection,
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
            "SELECT * FROM offers",
            connection,
        )

        subscriptions = pd.read_sql_query(
            "SELECT * FROM subscriptions",
            connection,
        )

    return (
        customers,
        contacts,
        churn,
        retention,
        offers,
        subscriptions,
    )


try:
    (
        customers,
        contacts,
        churn,
        retention,
        offers,
        subscriptions,
    ) = load_data()

except Exception as error:
    st.error(
        "Unable to load RetentionIQ data. "
        "Please generate the database first."
    )
    st.exception(error)
    st.stop()


# =========================================================
# HELPER FUNCTIONS
# =========================================================
def money(value):
    """Format values in Indian rupees."""
    try:
        return f"₹{float(value):,.0f}"
    except (TypeError, ValueError):
        return "₹0"


def kpi_card(label, value, note, accent):
    """Display a KPI card."""
    st.markdown(
        f"""
        <div class="kpi-card"
             style="border-top-color: {accent};">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_chart(fig, height=330):
    """Apply consistent styling to Plotly charts."""
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="DM Sans, sans-serif",
            color=TEXT,
            size=12,
        ),
        title=dict(
            font=dict(size=16, color=TEXT),
            x=0.02,
        ),
        margin=dict(l=12, r=12, t=45, b=12),
    )

    fig.update_xaxes(
        showgrid=False,
        linecolor=BORDER,
        tickfont=dict(color=MUTED),
    )

    fig.update_yaxes(
        gridcolor="#EEF0F6",
        zeroline=False,
        tickfont=dict(color=MUTED),
    )

    return fig


# =========================================================
# DASHBOARD HEADER
# =========================================================
st.markdown(
    """
    <div class="hero">
        <h1>📊 RetentionIQ</h1>
        <p>
            Customer Churn Intelligence
            &amp; Retention Campaign Analytics
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR FILTERS
# =========================================================
st.sidebar.markdown("## Dashboard Filters")
st.sidebar.caption("Filter your customer retention analysis")

risk_min, risk_max = st.sidebar.slider(
    "Customer risk score",
    min_value=0.0,
    max_value=1.0,
    value=(0.0, 1.0),
    step=0.05,
)

experiment_options = ["All"] + sorted(
    retention["experiment_group"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

selected_experiment = st.sidebar.selectbox(
    "Experiment Group",
    experiment_options,
)

offer_names = offers[
    ["offer_id", "offer_name"]
].copy()

offer_names["offer_name"] = (
    offer_names["offer_name"].fillna("Unknown Offer")
)

offer_options = ["All"] + offer_names[
    "offer_name"
].tolist()

selected_offer = st.sidebar.selectbox(
    "Retention Offer",
    offer_options,
)

filtered_contacts = contacts[
    contacts["risk_score"].between(risk_min, risk_max)
].copy()

filtered_retention = retention[
    retention["risk_score"].between(risk_min, risk_max)
].copy()

if selected_experiment != "All":

    filtered_contacts = filtered_contacts[
        filtered_contacts["experiment_group"]
        == selected_experiment
    ]

    filtered_retention = filtered_retention[
        filtered_retention["experiment_group"]
        == selected_experiment
    ]

if selected_offer != "All":

    selected_offer_ids = offer_names.loc[
        offer_names["offer_name"] == selected_offer,
        "offer_id",
    ]

    filtered_contacts = filtered_contacts[
        filtered_contacts["offer_id"].isin(
            selected_offer_ids
        )
    ]

    filtered_retention = filtered_retention[
        filtered_retention["offer_id"].isin(
            selected_offer_ids
        )
    ]

if st.sidebar.button(
    "Reset Dashboard Cache",
    use_container_width=True,
):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()

st.sidebar.caption(
    "Synthetic demonstration data | Seed: 20261022"
)


# =========================================================
# BUSINESS OVERVIEW
# =========================================================
st.markdown(
    '<div class="section-heading">Business Overview</div>',
    unsafe_allow_html=True,
)

total_customers = len(customers)

total_churned = (
    int(churn["ground_truth_churn"].sum())
    if not churn.empty
    else 0
)

churn_rate = (
    total_churned / len(churn) * 100
    if len(churn)
    else 0
)

total_contacts = len(filtered_contacts)

col1, col2, col3, col4 = st.columns(4, gap="medium")

with col1:
    kpi_card(
        "Total Customers",
        f"{total_customers:,}",
        "Customers in the database",
        BLUE,
    )

with col2:
    kpi_card(
        "Customers Churned",
        f"{total_churned:,}",
        "Simulated churn outcomes",
        RED,
    )

with col3:
    kpi_card(
        "Overall Churn Rate",
        f"{churn_rate:.2f}%",
        "Churned / total outcomes",
        AMBER,
    )

with col4:
    kpi_card(
        "Campaign Contacts",
        f"{total_contacts:,}",
        "Matching current filters",
        GREEN,
    )

st.write("")


# =========================================================
# CHURN DISTRIBUTION
# =========================================================
left, right = st.columns(2, gap="large")

with left:

    st.markdown(
        '<div class="panel">',
        unsafe_allow_html=True,
    )

    st.markdown("### Churn Distribution")

    churned_rows = churn[
        churn["ground_truth_churn"] == 1
    ]

    churn_distribution = (
        churned_rows["churn_type"]
        .fillna("Unknown")
        .value_counts()
        .rename_axis("Churn Type")
        .reset_index(name="Customers")
    )

    if not churn_distribution.empty:

        fig = px.pie(
            churn_distribution,
            names="Churn Type",
            values="Customers",
            hole=0.60,
            color="Churn Type",
            color_discrete_sequence=[
                PURPLE,
                PURPLE_LIGHT,
                BLUE,
                AMBER,
            ],
        )

        fig.update_traces(
            textposition="inside",
            textinfo="percent",
            marker=dict(
                line=dict(color="white", width=3)
            ),
        )

        fig.add_annotation(
            text=f"<b>{total_churned:,}</b><br>Churned",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=17, color=TEXT),
        )

        fig = style_chart(fig, 330)

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    else:
        st.info("No churn events found.")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# CUSTOMER RISK DISTRIBUTION
# =========================================================
with right:

    st.markdown(
        '<div class="panel">',
        unsafe_allow_html=True,
    )

    st.markdown("### Customer Risk Distribution")

    if not filtered_contacts.empty:

        fig = px.histogram(
            filtered_contacts,
            x="risk_score",
            nbins=20,
            color_discrete_sequence=[PURPLE],
            labels={
                "risk_score": "Risk Score",
                "count": "Customers",
            },
        )

        fig.update_traces(
            marker_line_color="white",
            marker_line_width=1,
        )

        fig = style_chart(fig, 330)
        fig.update_layout(bargap=0.08)

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

        st.caption(
            "Average risk score: "
            f"**{filtered_contacts['risk_score'].mean():.4f}**"
        )

    else:
        st.info(
            "No contacts match the selected filters."
        )

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# RETENTION EXPERIMENT
# =========================================================
st.markdown(
    '<div class="section-heading">Retention Experiment</div>',
    unsafe_allow_html=True,
)

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
        category_orders={
            "experiment_group": ["control", "treatment"]
        },
        color_discrete_map={
            "control": BLUE,
            "treatment": PURPLE_LIGHT,
        },
        labels={
            "experiment_group": "Experiment Group",
            "retention_rate": "Retention Rate (%)",
        },
    )

    fig.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
        cliponaxis=False,
    )

    fig.update_yaxes(
        range=[
            0,
            min(
                110,
                max(
                    100,
                    experiment_summary["retention_rate"].max() + 8,
                ),
            ),
        ]
    )

    fig = style_chart(fig, 330)
    fig.update_layout(showlegend=False)

    chart_col, summary_col = st.columns(
        [2.2, 1],
        gap="large",
    )

    with chart_col:
        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    with summary_col:

        st.markdown(
            '<div class="panel">',
            unsafe_allow_html=True,
        )

        st.markdown("#### Experiment Summary")

        control = experiment_summary[
            experiment_summary["experiment_group"] == "control"
        ]

        treatment = experiment_summary[
            experiment_summary["experiment_group"] == "treatment"
        ]

        if not control.empty and not treatment.empty:

            control_rate = float(
                control["retention_rate"].iloc[0]
            )

            treatment_rate = float(
                treatment["retention_rate"].iloc[0]
            )

            difference = treatment_rate - control_rate

            st.metric(
                "Treatment vs Control",
                f"{difference:+.2f} pp",
                help="Simulated difference in percentage points.",
            )

        else:
            st.info(
                "Select All experiment groups to compare both groups."
            )

        for _, row in experiment_summary.iterrows():

            st.write(
                f"**{str(row['experiment_group']).title()}**"
            )

            st.caption(
                f"{int(row['contacts']):,} contacts | "
                f"{row['retention_rate']:.2f}% retained"
            )

        st.markdown("</div>", unsafe_allow_html=True)

    display_experiment = experiment_summary.copy()

    display_experiment["retention_rate"] = (
        display_experiment["retention_rate"]
        .map(lambda value: f"{value:.2f}%")
    )

    display_experiment["offer_cost"] = (
        display_experiment["offer_cost"].map(money)
    )

    display_experiment = display_experiment.rename(
        columns={
            "experiment_group": "Experiment Group",
            "contacts": "Contacts",
            "retention_rate": "Retention Rate",
            "offer_cost": "Realized Offer Cost",
        }
    )

    st.dataframe(
        display_experiment,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Results are simulated using synthetic data. "
        "They do not establish real-world causal impact."
    )

else:
    st.info(
        "No retention outcomes match the selected filters."
    )


# =========================================================
# OFFER PERFORMANCE
# =========================================================
st.markdown(
    '<div class="section-heading">Offer Performance</div>',
    unsafe_allow_html=True,
)

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

if not offer_summary.empty:

    offer_summary["retention_rate"] *= 100

    offer_summary = offer_summary.merge(
        offers[["offer_id", "offer_name"]],
        on="offer_id",
        how="left",
    )

    offer_summary["offer_name"] = (
        offer_summary["offer_name"].fillna("Unknown Offer")
    )

    offer_display = offer_summary[
        [
            "offer_name",
            "contacts",
            "retained_customers",
            "retention_rate",
            "offer_cost",
        ]
    ].copy()

    offer_display["retention_rate"] = (
        offer_display["retention_rate"]
        .map(lambda value: f"{value:.2f}%")
    )

    offer_display["offer_cost"] = (
        offer_display["offer_cost"].map(money)
    )

    offer_display = offer_display.rename(
        columns={
            "offer_name": "Offer",
            "contacts": "Contacts",
            "retained_customers": "Retained Customers",
            "retention_rate": "Retention Rate",
            "offer_cost": "Realized Offer Cost",
        }
    )

    st.dataframe(
        offer_display,
        use_container_width=True,
        hide_index=True,
    )

else:
    st.info(
        "No offer performance data matches the selected filters."
    )


# =========================================================
# KEY BUSINESS INSIGHTS
# =========================================================
st.markdown(
    '<div class="section-heading">Key Business Insights</div>',
    unsafe_allow_html=True,
)

insight_cols = st.columns(4, gap="medium")

with insight_cols[0]:

    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-title">Campaign Reach</div>
            <div class="insight-value">{total_contacts:,}</div>
            <div class="insight-detail">
                Contacts matching current filters
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with insight_cols[1]:

    avg_risk = (
        f"{filtered_contacts['risk_score'].mean():.4f}"
        if not filtered_contacts.empty
        else "N/A"
    )

    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-title">Average Customer Risk</div>
            <div class="insight-value">{avg_risk}</div>
            <div class="insight-detail">
                Mean risk score of filtered contacts
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with insight_cols[2]:

    if not offer_summary.empty:

        best_offer = offer_summary.sort_values(
            "contacts",
            ascending=False,
        ).iloc[0]

        offer_title = str(best_offer["offer_name"])
        offer_detail = f"{int(best_offer['contacts']):,} contacts"

    else:
        offer_title = "No offer data"
        offer_detail = "Adjust the filters to view offers"

    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-title">Highest Campaign Reach</div>
            <div class="insight-value">{offer_title}</div>
            <div class="insight-detail">{offer_detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with insight_cols[3]:

    groups_present = set(
        experiment_summary["experiment_group"].astype(str)
    )

    if {"control", "treatment"}.issubset(groups_present):

        rates = experiment_summary.set_index(
            "experiment_group"
        )["retention_rate"]

        difference = float(
            rates["treatment"] - rates["control"]
        )

        difference_text = f"{difference:+.2f} pp"
        difference_detail = "Treatment minus control; simulated"

    else:
        difference_text = "N/A"
        difference_detail = "Select both experiment groups"

    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-title">Retention-Rate Difference</div>
            <div class="insight-value">{difference_text}</div>
            <div class="insight-detail">{difference_detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# CAMPAIGN CONTACT DETAILS
# =========================================================
st.markdown(
    '<div class="section-heading">Campaign Contact Details</div>',
    unsafe_allow_html=True,
)

st.caption(
    "Highest-risk customers are shown first. "
    "Use the filters to narrow the table."
)

if not filtered_contacts.empty:

    display_contacts = filtered_contacts.sort_values(
        "risk_score",
        ascending=False,
    )

    st.dataframe(
        display_contacts,
        use_container_width=True,
        hide_index=True,
        height=360,
    )

else:
    st.info(
        "No campaign contacts match the selected filters."
    )


# =========================================================
# DOWNLOAD CAMPAIGN CONTACTS
# =========================================================
download_data = filtered_contacts.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    "⬇️ Download Filtered Campaign Contacts (CSV)",
    data=download_data,
    file_name="retentioniq_campaign_contacts.csv",
    mime="text/csv",
    use_container_width=False,
)


# =========================================================
# FOOTER
# =========================================================
st.divider()

st.caption(
    "RetentionIQ | Synthetic demonstration data | "
    "Fixed seed: 20261022. "
    "Treatment effects and revenue estimates are simulated."
)