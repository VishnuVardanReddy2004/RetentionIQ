# AI Prompt History — RetentionIQ

## 1. Purpose

This document records the use of AI assistance during the planning, development, debugging, testing, documentation, and verification of the RetentionIQ project.

The purpose of this record is to make AI usage transparent and explain how suggestions were reviewed and verified.

AI was used as a development aid. Responsibility for understanding the implementation, reviewing changes, running tests, validating results, and submitting the project remains mine.

## 2. AI Tool Used

- **AI tool:** ChatGPT
- **Purpose:** Technical guidance, debugging assistance, project review, test verification, documentation improvement, and submission preparation.

This record identifies the AI tool used in the work documented here. Any other AI tools used during development should also be listed.

## 3. AI-Assisted Development Activities

The following table summarizes the main categories of AI assistance used during RetentionIQ development. These entries are task summaries, not verbatim copies of every prompt.

| No. | Development area | Purpose of AI assistance | My verification |
|---:|---|---|---|
| 1 | Project planning | Understand the challenge requirements and organize implementation tasks | Compared project features with the challenge instructions |
| 2 | Database design | Review relational tables, relationships, primary keys, foreign keys, and integrity constraints | Inspected the schema and checked database integrity |
| 3 | Synthetic data generation | Review deterministic data generation and business-rule implementation | Generated datasets independently and compared database-content checksums |
| 4 | Churn-risk scoring | Review the rule-based approach using usage decline, billing risk, and support risk | Inspected the implementation and generated results |
| 5 | Offer eligibility | Review offer eligibility conditions and campaign assignment logic | Ran data validation and automated tests |
| 6 | Churn and retention outcomes | Review how generated churn labels and retention outcomes are stored and analyzed | Inspected the data model and validation results |
| 7 | Data validation | Identify and verify database-integrity and business-rule checks | Ran `python -m src.validate_data` |
| 8 | Automated testing | Review test execution and investigate potential issues | Ran `python -m pytest -q` |
| 9 | Reproducibility | Verify repeatability using separate data-generation runs | Compared SHA-256 database-content checksums |
| 10 | Dashboard | Review how the Streamlit dashboard presents churn and campaign metrics | Launched the dashboard locally and inspected its output |
| 11 | Documentation | Improve README structure, setup instructions, limitations, and verification details | Reviewed the README and checked the repository |
| 12 | Final verification | Organize the submission checklist and AI-use documentation | Checked Git status, validation results, test results, and repository updates |
## 4. Key AI Prompts

**AI tool used:** ChatGPT

The following entries capture the main AI-assisted tasks during RetentionIQ development. Telugu prompts are translated into English where applicable. Entries marked as task summaries are not verbatim prompts.

| No. | Date | Key Prompt or Task | Outcome and Verification |
|---:|---|---|---|
| 1 | October 2026 | **Original prompt** Explain the challenge problem statement line by line and help me understand the requirements before starting implementation. | Clarified the project scope, business workflow, and expected deliverables. |
| 2 | October 2026 | **Original prompt:** "Both VS Code and Python are installed. Start building RetentionIQ step by step." | Started the project setup and implementation. |
| 3 | October 2026 | **Task summary:** Help design a relational database schema and generate reproducible synthetic data for customer churn and retention analytics. | Developed the SQLite data model and synthetic data-generation workflow. |
| 4 | October 2026 | **Task summary:** Help implement churn-risk scoring, retention-offer eligibility, campaign costs, and treatment/control outcome tracking. | Developed the core business logic and campaign simulation. |
| 5 | October 2026 | **Task summary:** Help implement data validation and automated tests for database integrity and business rules. | Latest recorded results: 41 validation checks passed and 22 pytest tests passed. |
| 6 | October 2026 | **Task summary:** Help verify reproducibility by comparing independently generated datasets. | Development notes recorded matching database-content checksums from two independent runs. |
| 7 | October 2026 | **Task summary:** Help build and refine the Streamlit dashboard to present churn risk, retention outcomes, and campaign metrics clearly. | Ran the dashboard locally and reviewed its rendered output. |
| 8 | October 2026 | **Task summary:** Help prepare the README and final project documentation, including setup instructions, validation results, and limitations. | Updated project documentation and pushed changes to GitHub. |

### Prompt Record Limitations

This is a concise record of the main AI-assisted tasks, not a complete transcript of every prompt. Original wording is included only where available. Task summaries must not be interpreted as verbatim prompts. Additional original prompts should be recovered where available to meet the challenge's prompt-disclosure requirements.

### Human Review and Responsibility

I am responsible for understanding the implementation, reviewing AI-assisted suggestions, verifying the project outputs, and explaining the design decisions and limitations during the technical review.

## 5. Verification Evidence

The following results were observed during the documented development session:

- **Data validation:** 41 checks passed, with 0 failures.
- **Automated tests:** 22 tests passed.
- **Reproducibility:** Two independent data generations produced matching database-content SHA-256 checksums.
- **Version control:** The project changes were committed and pushed to the public GitHub repository.
- **Repository status:** The latest reported Git status showed the local branch up to date with `origin/main` and a clean working tree.

These results apply to the tested version and configuration. They should not be interpreted as proof that every possible edge case has been tested.

## 6. Limitations

- The dataset and campaign outcomes are synthetic.
- Churn-risk scoring is rule-based rather than the output of a trained machine-learning model.
- Campaign retention differences do not establish real-world causal impact.
- The recorded verification results cover the checks and tests that were actually executed.
- The task summaries in this document are not a substitute for a complete transcript of AI prompts.
- Exact prompts that cannot be recovered should not be invented or presented as verbatim records.

## 7. Responsibility and Ownership

I am responsible for the final submitted implementation and for being able to explain its design, assumptions, business rules, testing approach, limitations, and results.

AI suggestions were used as assistance and should be evaluated against the actual code, requirements, and test results. Any proposed change must be reviewed and verified before it is accepted into the project.

## 8. Project Repository

**Project:** RetentionIQ — Customer Churn & Retention Analytics

**GitHub repository:**  
https://github.com/VishnuVardanReddy2004/RetentionIQ

