# RetentionIQ — Customer Churn & Retention Analytics

RetentionIQ is a customer retention analytics project designed to identify customers at risk of churn, evaluate retention offer eligibility, and compare retention outcomes between treatment and control groups.

The project uses synthetic subscription business data to demonstrate relational database design, reproducible data generation, rule-based churn-risk scoring, retention campaign simulation, data validation, and interactive analytics.

## Key Features

- **Synthetic Data Generation:** Generates customer, subscription, usage, billing, support, offer, campaign, churn, and retention records.
- **Relational Database:** Stores 10 related entities in SQLite with primary keys, foreign keys, uniqueness rules, and integrity constraints.
- **Churn-Risk Scoring:** Calculates customer risk scores using usage decline, recent billing issues, and support history.
- **Offer Eligibility:** Applies configurable rules based on risk score, offer cost, subscription price, and effective dates.
- **Treatment and Control Groups:** Simulates retention campaign assignments and records their outcomes.
- **Churn Outcome Tracking:** Records synthetic churn labels, churn dates, and voluntary or involuntary churn types.
- **Data Validation:** Checks identifiers, foreign-key integrity, churn labels, evaluation dates, risk scores, offer eligibility, and control-group costs.
- **CSV and JSON Exports:** Exports database tables for further analysis.
- **Interactive Dashboard:** Uses Streamlit and Plotly to explore churn, risk scores, campaign retention, offer performance, and campaign contacts.
- **Automated Testing:** Uses pytest to test database integrity and core business rules.
- **Reproducible Data Generation:** Uses a fixed random seed to support repeatable dataset generation.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Data generation and business logic |
| SQLite | Relational data storage |
| Pandas | Data processing and analysis |
| NumPy | Numerical operations and synthetic data generation |
| Streamlit | Interactive dashboard |
| Plotly | Charts and visualizations |
| pytest | Automated testing |
| Git and GitHub | Version control and project hosting |

## Project Structure

```text
RetentionIQ/
├── data/
│   ├── retentioniq.db
│   ├── retentioniq_backup.db
│   └── exports/
│       ├── csv/
│       └── json/
├── src/
│   ├── __init__.py
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

The database and export files are generated locally and are excluded from Git according to the current `.gitignore` configuration. They can be regenerated using the instructions below.

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/VishnuVardanReddy2004/RetentionIQ.git
cd RetentionIQ
```

### 2. Create a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
```

### 3. Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, use an alternative supported terminal or follow your environment's security guidance.

### 4. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

## Run the Project

Run the following commands from the project root directory.

> **Important:** Data generation can replace the existing generated database. Back up any data you need before running the schema initialization or generator commands.

### Step 1: Initialize the database

```powershell
python -m src.schema
```

This initializes the SQLite database and creates the required tables.

### Step 2: Generate synthetic data

```powershell
python -m src.generate_data
```

The generator creates customer and subscription records, usage snapshots, billing events, support cases, offers, eligibility rules, campaign contacts, churn outcomes, and retention outcomes.

The generator uses a fixed random seed (`20261022`) for reproducibility.

### Step 3: Validate the data

```powershell
python -m src.validate_data
```

This runs the implemented data-integrity and business-rule validation checks and prints a validation summary.

### Step 4: Export data to CSV and JSON

```powershell
python -m src.export_data
```

The exported tables are saved under `data/exports/csv/` and `data/exports/json/`.

### Step 5: Run automated tests

```powershell
python -m pytest -v
```

This executes the automated test suite in the `tests/` directory.

### Step 6: Inspect results

```powershell
python -m src.inspect_results
```

This displays summary statistics about churn outcomes and retention campaign performance.

### Step 7: Check database integrity

```powershell
python -m src.check_database
```

This runs the database inspection utility.

### Step 8: Check reproducibility

```powershell
python -m src.check_reproducibility
```

This calculates a SHA-256 checksum based on database contents. To verify reproducibility independently, generate the dataset in separate clean project copies using the same configuration and compare their checksums.

**Note:** Do not regenerate the database in your main project merely to check reproducibility. Use a backup or a separate copy.

### Step 9: Launch the dashboard

```powershell
python -m streamlit run src/dashboard.py
```

Streamlit displays a local URL in the terminal, usually:

```text
http://localhost:8501
```

Open that URL in your browser to explore the dashboard.

## Data Model

RetentionIQ contains the following 10 related entities:

| Entity | Description |
|---|---|
| `customers` | Customer information and acquisition details |
| `subscriptions` | Subscription plans, prices, and lifecycle status |
| `usage_snapshots` | Periodic customer usage measurements |
| `billing_events` | Invoice, payment, refund, and adjustment events |
| `support_cases` | Customer support issues and their status |
| `offers` | Retention offers, discounts, and costs |
| `eligibility_rules` | Rules that determine which offers can be assigned |
| `campaign_contacts` | Campaign assignments and treatment/control groups |
| `churn_outcomes` | Churn labels, dates, and churn types |
| `retention_outcomes` | Retention results and realized offer costs |

Primary keys, foreign keys, unique constraints, and other database constraints help maintain consistency between related records.

## Churn-Risk Scoring

The project calculates a rule-based churn-risk score using three categories of information:

1. **Usage decline:** A reduction in customer activity compared with earlier usage.
2. **Billing risk:** Recent overdue or failed payment activity.
3. **Support risk:** Recent support cases, including their severity and status.

The current scoring logic combines these signals using the following weights:

| Risk signal | Weight |
|---|---:|
| Usage decline | 50% |
| Billing risk | 30% |
| Support risk | 20% |

The score is normalized to a range from `0` to `1`, where higher values indicate greater estimated churn risk.

This is a rule-based score, not a probability produced by a trained machine-learning model.

## Offer Eligibility and Campaign Simulation

Customers are evaluated against configurable eligibility rules. The implemented logic considers:

- Minimum required risk score
- Maximum permitted offer cost
- Minimum subscription price
- Rule effective dates
- Offer validity dates

Eligible campaign contacts are assigned to treatment or control groups.

- **Treatment group:** Eligible contacts assigned to receive a retention offer.
- **Control group:** Eligible contacts used as a comparison group without a recorded offer cost.

Campaign outcomes are simulated and stored in the database for analysis.

The simulation demonstrates the workflow of eligibility checks, experiment assignment, cost tracking, and retention measurement. The results should not be interpreted as proof of real-world campaign effectiveness.

## Churn and Retention Outcomes

The `churn_outcomes` table stores generated ground-truth churn labels and related dates. The `retention_outcomes` table stores campaign outcome labels, realized offer costs, and associated outcome information.

These concepts should be distinguished:

- **Risk score:** A rule-based indicator of estimated churn risk.
- **Ground-truth churn label:** A synthetic outcome generated by the simulation.
- **Retention outcome:** A simulated result used to compare campaign groups.

The current implementation does not train a machine-learning churn prediction model. The campaign results are simulated and should not be interpreted as evidence of real-world causal impact.

## Data Validation and Testing

The project includes data validation checks and automated tests for the implemented database constraints and business rules.

The latest verified development run passed:

- **41 of 41 data validation checks**
- **22 of 22 automated pytest tests**
- **Independent reproducibility verification:** Two separate data generations produced matching database-content SHA-256 checksums.

The validation checks cover areas such as:

- Required database tables
- Unique identifiers
- Foreign-key integrity
- Churn dates and labels
- Risk-score bounds
- Offer eligibility conditions
- Valid retention values and nonnegative costs
- Zero recorded offer cost for the control group

These results describe the verified development run and implemented test suite. They do not establish that every possible input, edge case, or production scenario has been tested.

To rerun the tests:

```powershell
python -m src.validate_data
python -m pytest -q
```

## Interactive Dashboard

The Streamlit dashboard provides visual summaries and interactive analysis, including:

- Customer and churn summary metrics
- Voluntary and involuntary churn distribution
- Risk-score distribution for campaign contacts
- Treatment versus control retention comparison
- Offer performance summaries
- Filterable campaign contact details
- CSV download for filtered campaign contacts

The dashboard is designed to make the generated data and campaign simulation easier to inspect.

## Data Exports

The export utility writes database tables to CSV and JSON formats under:

```text
data/exports/
├── csv/
└── json/
```

These exports support inspection, downstream analysis, and use with other data-processing tools.

The current local project contains exports for the database tables. The database and export files are excluded from Git under the current `.gitignore` configuration.

The `churn_outcomes` table contains the generated churn labels. Separate standalone ground-truth export files are not documented as part of the current implementation.

## Reproducibility

The data generator uses a fixed random seed:

```text
20261022
```

Reproducibility was checked by generating the dataset twice in separate project copies with the same configuration and comparing database-content SHA-256 checksums. Both verified runs produced the same checksum:

```text
9b0ff6df0bac3dba116dd5fbd3d18bcface3a227e333231726157aab280b3a52
```

The verified dataset contained the following record counts:

| Table | Rows |
|---|---:|
| `billing_events` | 415,186 |
| `campaign_contacts` | 2,793 |
| `churn_outcomes` | 20,000 |
| `customers` | 20,000 |
| `eligibility_rules` | 3 |
| `offers` | 3 |
| `retention_outcomes` | 2,793 |
| `subscriptions` | 20,000 |
| `support_cases` | 16,088 |
| `usage_snapshots` | 187,593 |

The verified date ranges indicate historical data spanning approximately 18 months across the dataset's signup, usage, and billing records. This does not mean every individual customer has a full 18 months of history.

Reproducibility applies to the verified configuration and runs. Changes to the generator, schema, dependencies, or configuration may change the results.

## Limitations

- The dataset is synthetic and does not represent real customer records.
- Churn labels and campaign outcomes are generated by simulation.
- The risk score is rule-based and is not a trained machine-learning model.
- Campaign retention differences do not establish real-world causal impact.
- Financial impact estimates depend on the assumptions implemented in the simulation.
- Validation and testing cover the implemented checks and should not be treated as exhaustive production certification.
- Separate standalone ground-truth exports and a field-by-field data dictionary are not documented as existing project files.

## Future Improvements

Potential improvements include:

- Adding standalone ground-truth CSV and JSON exports, if required by the project specification
- Creating a field-by-field data dictionary covering each table and column
- Adding more edge-case validation and lifecycle checks
- Expanding experiment-balance and offer-assignment validation
- Improving financial impact and incremental revenue calculations
- Evaluating a trained churn model using a time-based validation strategy
- Adding model-performance metrics and risk-score calibration
- Improving dashboard filters and experiment reporting

These are possible extensions and are not claims about features already implemented.

## Author

**Vishnu Vardan Reddy**

GitHub: [VishnuVardanReddy2004](https://github.com/VishnuVardanReddy2004)

Project repository: [RetentionIQ](https://github.com/VishnuVardanReddy2004/RetentionIQ)

## Verification Summary

In the latest verified development run:

- **41 data validation checks passed.**
- **22 automated pytest tests passed.**
- **Two independent data generations produced matching database-content SHA-256 checksums.**
- **10 related database tables** were populated in the verified dataset.
- **20,000 customer records** were generated.

These results apply to the current synthetic dataset, configuration, and implemented test suite.
