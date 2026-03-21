"""Legal domain classification tools."""

from __future__ import annotations

import re
import logging

from strands import tool

logger = logging.getLogger(__name__)

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "Contract Law & UCC Analysis": [
        "contract", "agreement", "ucc", "uniform commercial code", "consideration",
        "breach", "performance", "warranty", "merchantability", "offer", "acceptance",
    ],
    "Corporate/Commercial Law": [
        "corporation", "shareholder", "board of directors", "fiduciary",
        "merger", "acquisition", "bylaws", "articles of incorporation",
        "securities", "stock", "dividend", "corporate governance",
    ],
    "Tort Law": [
        "negligence", "duty of care", "proximate cause", "damages",
        "tortious", "liability", "personal injury", "defamation",
    ],
    "Constitutional Law": [
        "constitutional", "amendment", "due process", "equal protection",
        "first amendment", "commerce clause", "federalism",
    ],
    "Criminal Law & Procedure": [
        "criminal", "felony", "misdemeanor", "prosecution",
        "defendant", "plea", "sentencing", "probable cause",
    ],
    "Administrative Law": [
        "regulatory", "agency", "rulemaking", "administrative",
        "compliance", "permit", "license", "enforcement action",
    ],
    "Intellectual Property": [
        "patent", "trademark", "copyright", "trade secret",
        "intellectual property", "infringement", "licensing", "ip rights",
    ],
    "International Law": [
        "international", "treaty", "foreign", "jurisdiction",
        "cross-border", "arbitration", "convention",
    ],
    "Tax Law": [
        "tax", "irs", "deduction", "taxable", "revenue",
        "assessment", "withholding", "capital gains",
    ],
    "Civil Procedure": [
        "civil procedure", "discovery", "motion", "summary judgment",
        "complaint", "pleading", "jurisdiction", "standing",
    ],
    "Environmental Law": [
        "environmental", "epa", "pollution", "hazardous",
        "clean air", "clean water", "remediation", "emission",
    ],
    "Immigration Law": [
        "immigration", "visa", "citizenship", "deportation",
        "asylum", "naturalization", "work permit",
    ],
    "Family Law": [
        "family", "divorce", "custody", "child support",
        "alimony", "adoption", "prenuptial",
    ],
}

DD_DOMAINS = [
    "Contract Law & UCC Analysis",
    "Corporate/Commercial Law",
    "Intellectual Property",
    "Tax Law",
    "Environmental Law",
    "Administrative Law",
]


@tool
def classify_domain(provision_text: str) -> str:
    """Route a provision to one of 13 legal domains.

    Uses keyword matching to classify the provision text into the
    most relevant legal domain.

    Args:
        provision_text: Text of the provision to classify.

    Returns:
        The classified legal domain string.
    """
    if not provision_text.strip():
        return "Contract Law & UCC Analysis"

    text_lower = provision_text.lower()
    scores: dict[str, int] = {}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            matches = len(re.findall(re.escape(keyword), text_lower))
            score += matches
        if score > 0:
            scores[domain] = score

    if not scores:
        return "Contract Law & UCC Analysis"

    best_domain = max(scores, key=scores.get)  # type: ignore[arg-type]
    logger.info("Classified provision into domain: %s (score=%d)", best_domain, scores[best_domain])
    return best_domain
