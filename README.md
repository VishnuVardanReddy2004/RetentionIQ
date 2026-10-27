# RetentionIQ — Customer Churn & Retention Analytics

RetentionIQ is a data-driven customer retention analytics project designed to identify customers at risk of churn, evaluate retention offer eligibility, and compare retention outcomes between treatment and control groups.

The project uses synthetic subscription business data to demonstrate data generation, relational database design, churn-risk scoring, campaign simulation, data validation, and interactive analytics.

## Key Features

- **Synthetic data generation:** Generates customer, subscription, usage, billing, support, offer, campaign, churn, and retention records.
- **Relational database:** Stores 10 related entities in SQLite with primary keys, foreign keys, and integrity constraints.
- **Churn-risk scoring:** Calculates risk scores from usage decline, billing issues, and support history.
- **Offer eligibility:** Applies configurable risk, offer-cost, subscription-price, and effective-date rules.
- **Treatment and control groups:** Simulates retention campaign assignments and outcomes.
- **Data validation:** Checks identifier uniqueness, foreign-key integrity, churn labels, evaluation dates, risk scores, eligibility, and control-group offer costs.
- **Data exports:** Exports database tables to CSV and JSON.
- **Interactive dashboard:** Uses Streamlit and Plotly to explore churn, risk scores, campaign retention, offer performance, and campaign contacts.
- **Automated tests:** Uses pytest to check database integrity and core business rules.

## Technology Stack

- Python
- SQLite
- Pandas and NumPy
- Streamlit
- Plotly
- pytest

## Project Structure

```text
RetentionIQ/
├── data/
│   └── Generated database and exports
├── src/
│   ├── schema.py
│   ├── generate_data.py
│   ├── validate_data.py
│   ├── export_data.py
│   ├── inspect_results.py
│   ├── check_database.py
│   ├── check_reproducibility.py
│   └── dashboard.py
├── tests/
│   └── test_retentioniq.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/VishnuVardanReddy2004/RetentionIQ.git
cd RetentionIQ
```

### 2. Create and activate a virtual environment

Windows PowerShell:


python -m venv .venv
.\.venv\Scripts\Activate.ps1

### 3. Install dependencies


python -m pip install -r requirements.txt


## Run the Project

Run these commands from the project root.

### 1. Initialize the database

python -m src.schema


### 2. Generate synthetic data


python -m src.generate_data


### 3. Validate the data


python -m src.validate_data


### 4. Export CSV and JSON files


python -m src.export_data


### 5. Run automated tests


python -m pytest -v


### 6. Launch the dashboard


python -m streamlit run src/dashboard.py
```

Streamlit will display a local URL, normally `http://localhost:8501`.

## Data Model

The SQLite database contains 10 entities:

1. `customers`
2. `subscriptions`
3. `usage_snapshots`
4. `billing_events`
5. `support_cases`
6. `offers`
7. `eligibility_rules`
8. `campaign_contacts`
9. `churn_outcomes`
10. `retention_outcomes`

The entities are connected through identifiers and foreign-key relationships to preserve data integrity.

## Churn Risk and Retention Simulation

The risk score uses three categories of behavioral information:

- Changes in customer usage
- Recent billing issues
- Support case history

Customers are evaluated against offer eligibility rules. Eligible campaign contacts are assigned to treatment or control groups, and simulated outcomes are recorded for analysis.

The churn outcomes represent generated ground-truth labels. They should be distinguished from predictions produced by a trained machine-learning model.

## Validation and Tests

The current development run passed:

- **18 of 18 database validation checks**
- **18 of 18 automated pytest tests**

These results describe the current generated dataset and test suite. They do not imply that every possible input or production scenario has been tested.

## Dashboard

The dashboard provides:

- Customer and churn summary metrics
- Voluntary versus involuntary churn distribution
- Campaign-eligible customer risk distribution
- Treatment versus control retention comparison
- Offer performance summaries
- Filterable campaign contact details
- CSV download for filtered campaign contacts

## Limitations

- Data is synthetic and does not represent actual customer records.
- Campaign outcomes are simulated and do not establish real-world causal impact.
- The risk score is a rule-based score; it is not itself a trained churn prediction model.
- Financial impact analysis depends on the assumptions used to generate offer costs and outcomes.

## Reproducibility

The data generator uses a fixed random seed. Reproducibility should be verified by regenerating the data and comparing outputs using the same configuration.

## Author

Vishnu Vardan Reddy

GitHub: https://github.com/VishnuVardanReddy2004
