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

## 4. Prompt Record

The entries below are summaries of AI-assisted tasks, not a complete verbatim transcript. Exact prompts should be added from the original conversation history wherever available.

| Date | AI tool | Prompt or task summary | Outcome and verification |
|---|---|---|---|
| October 2026 | ChatGPT | Help understand the RetentionIQ challenge and organize project implementation | Reviewed the project structure and requirements |
| October 2026 | ChatGPT | Help review database design, data generation, and business rules | Checked database integrity and validation output |
| October 2026 | ChatGPT | Help review churn-risk scoring and retention campaign logic | Inspected implementation and generated results |
| October 2026 | ChatGPT | Help verify data quality and automated tests | Confirmed a development run with 41 passing validation checks and 22 passing pytest tests |
| October 2026 | ChatGPT | Help verify reproducibility across independent data generations | Compared checksums from two independent runs |
| October 2026 | ChatGPT | Help update the project README with verified results and limitations | Updated the README and pushed the changes to GitHub |
| October 2026 | ChatGPT | Help document AI usage and prepare the final submission checklist | Created and committed this prompt-history document |

**Completeness note:** This table summarizes the tasks documented here. It does not establish that every prompt from every AI tool has been recovered. Additional prompts and tools must be recorded from the actual conversation history where available.

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

