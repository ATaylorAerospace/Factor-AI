# Security Policy

## Our Commitment to Legal Data Integrity
Factor-AI is designed for high-stakes legal due diligence. We prioritize data isolation, the "Principle of Least Privilege," and the prevention of data leakage into public LLM training sets.

## Supported Versions
We only provide security updates for the current `main` branch.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability
**Do not open a public GitHub issue for security vulnerabilities.**

If you discover a potential security risk (e.g., credential exposure, prompt injection, or data leakage), please report it privately. 

1. **Email:** [Author Email/Contact]
2. **Response Time:** You will receive an acknowledgment within 24–48 hours.
3. **Disclosure:** we follow "Coordinated Disclosure." Please give us 30 days to patch the issue before sharing any details publicly.

## Critical Prohibitions
* **No Hardcoded Keys:** Any PR containing AWS Access Keys or Secret Keys will be immediately rejected and the history purged.
* **No Client Data:** Never upload real legal contracts to the `/tests` or `/data` directories. Use the provided `mock_contract_generator.py` for testing.
* **Encryption:** All S3 buckets used in this workflow must utilize AES-256 server-side encryption.
