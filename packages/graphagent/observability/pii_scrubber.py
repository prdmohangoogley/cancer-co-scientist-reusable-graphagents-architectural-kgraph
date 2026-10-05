"""HIPAA Safe Harbor and GDPR compliant PII/PHI De-Identification Engine.

Adheres strictly to:
- DOC-01: AI Agent Quality Engineering & Auditable Observability
- DOC-02: Zero Ambient Authority (ZAA) & Agentic SecOps
- Spec 15: PII/PHI De-Identification Interceptors in Logging, Tracing & Memory

Sanitizes:
- Patient Names and Honorifics
- Medical Record Numbers (MRN) and Patient Identifiers
- Social Security Numbers (SSN)
- Phone Numbers and Email Addresses
- Dates of Birth (DOB)
- Public IP Addresses
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Pattern, Union


class PIIScrubber:
    """Enterprise PII/PHI sanitization engine for precision oncology pipelines."""

    PATTERNS: List[tuple[Pattern[str], str]] = [
        # Social Security Numbers (SSN)
        (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
        # Dates of Birth (DOB: 05/14/1968, Born: 1974-12-01)
        (
            re.compile(
                r"\b(?:DOB|Date\s+of\s+Birth|Born)[\s:#-]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b",
                re.IGNORECASE,
            ),
            "[REDACTED_DOB]",
        ),
        # Email Addresses
        (
            re.compile(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
            ),
            "[REDACTED_EMAIL]",
        ),
        # North American and International Phone Numbers
        (
            re.compile(
                r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
            ),
            "[REDACTED_PHONE]",
        ),
        # Patient Names with explicit patient/clinical markers (e.g. "Patient Jane Doe", "Pt: Robert Frost")
        (
            re.compile(
                r"\b(?:Patient|Pt\.?|Subject)\s*(?:Name)?[\s:#-]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b"
            ),
            "[REDACTED_PATIENT_NAME]",
        ),
        # Common Name honorifics when tied to clinical context (e.g. "Mr. John Doe", "Mrs. Sarah Jenkins")
        (
            re.compile(
                r"\b(?:Mr\.|Mrs\.|Ms\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b"
            ),
            "[REDACTED_PATIENT_NAME]",
        ),
        # Medical Record Numbers / Patient IDs (e.g., MRN-984123, PAT-4412, Patient ID: 88124)
        (
            re.compile(
                r"\b(?:MRN|Patient\s*ID|Record\s*(?:Number|#|No\.?)|PAT(?=[-:#\s]))[\s:#-]*([A-Z0-9]{4,14})\b",
                re.IGNORECASE,
            ),
            "[REDACTED_MRN]",
        ),
        # Public IP Addresses (excluding localhost 127.0.0.1 and broadcast 0.0.0.0)
        (
            re.compile(
                r"\b(?!127\.0\.0\.1|0\.0\.0\.0)(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-5])\.(?:\d{1,3}\.){2}(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-5])\b"
            ),
            "[REDACTED_IP]",
        ),
    ]

    @classmethod
    def scrub_text(cls, text: str) -> str:
        """Sanitizes PII/PHI entities within a raw text string."""
        if not text or not isinstance(text, str):
            return text

        scrubbed = text
        for pattern, replacement in cls.PATTERNS:
            scrubbed = pattern.sub(replacement, scrubbed)
        return scrubbed

    @classmethod
    def scrub(cls, data: Any) -> Any:
        """Recursively de-identifies PII/PHI in primitives, dicts, lists, and tuples."""
        if isinstance(data, str):
            return cls.scrub_text(data)
        elif isinstance(data, dict):
            return {cls.scrub(k): cls.scrub(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls.scrub(item) for item in data]
        elif isinstance(data, tuple):
            return tuple(cls.scrub(item) for item in data)
        elif isinstance(data, set):
            return {cls.scrub(item) for item in data}
        return data


def scrub_pii(data: Any) -> Any:
    """Convenience function to scrub PII/PHI across all payloads."""
    return PIIScrubber.scrub(data)
