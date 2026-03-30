# Contributing to Factor-AI

First, thank you for helping build the future of Agentic Legal Tech! ⚖️

To maintain the high standards required for legal-grade software, we ask all contributors to follow these guidelines.

## 🛠 Development Workflow
1. **Fork** the repository and create your branch from `main`.
2. **Environment:** Use the provided `.env.example`. Never commit your actual `.env` file.
3. **Testing:** Ensure all logic passes the `pytest` suite, specifically focusing on the **Hallucination-Loop Detection** logic.

## 🔐 Security & Privacy Rules
* **AWS Credentials:** Use IAM Roles or local profiles. We utilize `git-secrets` to scan for accidental credential commits.
* **LLM Settings:** Ensure all Bedrock calls have `opt-out` for model training where available to protect contract privacy.
* **Mock Data Only:** Only use the anonymized `.txt` or `.pdf` files in the `samples/` folder for pull request demonstrations.

## 🎨 Style Guidelines
* **Type Hinting:** We use strict Python type hinting to ensure the **Supervisor Agent** routes data deterministically.
* **Emojis:** Use emojis sparingly in logs and UI components to maintain a professional "Enterprise" aesthetic (e.g., 🔍 for Research, 🛡️ for Risk).
* **Documentation:** If you add a new Specialist Agent, you must update the architecture diagram or the Component Breakdown in the README.

## ⚖️ Legal Disclaimer
By contributing to Factor-AI, you agree that your contributions will be licensed under the project's MIT License.
