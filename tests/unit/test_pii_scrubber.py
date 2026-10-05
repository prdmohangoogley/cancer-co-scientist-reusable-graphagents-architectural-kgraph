"""Unit tests for HIPAA Safe Harbor and GDPR PII/PHI De-Identification Engine."""

import pytest
from packages.graphagent.observability.pii_scrubber import PIIScrubber, scrub_pii


def test_scrub_patient_name():
    raw = "Patient Jane Doe presented with adenocarcinoma. Pt: Robert Frost scheduled for CT."
    scrubbed = scrub_pii(raw)
    assert "Jane Doe" not in scrubbed
    assert "Robert Frost" not in scrubbed
    assert "[REDACTED_PATIENT_NAME]" in scrubbed


def test_scrub_mrn_and_patient_id():
    raw = "Review lab results for MRN-984123 and Patient ID: 44129."
    scrubbed = scrub_pii(raw)
    assert "984123" not in scrubbed
    assert "44129" not in scrubbed
    assert "[REDACTED_MRN]" in scrubbed


def test_scrub_ssn_and_dob():
    raw = "Primary patient SSN 123-45-6789, Born: 05/14/1968, DOB: 1974-12-01."
    scrubbed = scrub_pii(raw)
    assert "123-45-6789" not in scrubbed
    assert "05/14/1968" not in scrubbed
    assert "1974-12-01" not in scrubbed
    assert "[REDACTED_SSN]" in scrubbed
    assert "[REDACTED_DOB]" in scrubbed


def test_scrub_contact_info():
    raw = "Contact oncologist at oncologist@cancercenter.org or call 555-123-4567."
    scrubbed = scrub_pii(raw)
    assert "oncologist@cancercenter.org" not in scrubbed
    assert "555-123-4567" not in scrubbed
    assert "[REDACTED_EMAIL]" in scrubbed
    assert "[REDACTED_PHONE]" in scrubbed


def test_scrub_nested_dict_and_list():
    nested = {
        "user_query": "Patient Alice Walker MRN-112233 needs Osimertinib",
        "metadata": {
            "clinician_email": "dr.smith@hospital.org",
            "logs": ["Session started from IP 192.168.1.100 for Pt: Bob Jones"],
        },
    }
    scrubbed = scrub_pii(nested)
    assert "Alice Walker" not in scrubbed["user_query"]
    assert "112233" not in scrubbed["user_query"]
    assert "dr.smith@hospital.org" not in scrubbed["metadata"]["clinician_email"]
    assert "Bob Jones" not in scrubbed["metadata"]["logs"][0]
    assert "[REDACTED_PATIENT_NAME]" in scrubbed["user_query"]
    assert "[REDACTED_MRN]" in scrubbed["user_query"]
    assert "[REDACTED_EMAIL]" in scrubbed["metadata"]["clinician_email"]
