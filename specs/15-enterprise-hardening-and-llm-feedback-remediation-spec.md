# Spec 15: Enterprise Hardening & LLM Evaluation Feedback Remediation Specification

**Status**: Approved & In Implementation  
**Governing Documents**: `DOC-01` (Agent Quality & Observability), `DOC-02` (ZAA & SecOps), `DOC-03` (A2UI & Protocols), `DOC-08` (Context & Memory), `DOC-09` (State Management)  
**Target Repositories**: `cancer-co-scientist-reusable-graphagents-architectural-kgraph`  
**Goal**: Elevate overall evaluation score from **79/95** to **95/95 (100%)** across all criteria:
1. Tool & Interface Design (14/20 $\to$ 20/20)
2. Orchestration & Logic (16/20 $\to$ 20/20)
3. Observability & Tracing (15/20 $\to$ 20/20)
4. Infrastructure & CI/CD (14/15 $\to$ 15/15)

---

## 1. Remediation Matrix & Gap Analysis

| Evaluation Criterion | Original Score | Deduction Cause | Remediation Target | Spec Section |
| :--- | :---: | :--- | :--- | :---: |
| **Tool & Interface Design** | 14 / 20 | Missing parameter docstrings; error handling relies on mock fallbacks / uncaught exceptions rather than LLM recovery instructions. | 1) Full Google-style docstrings with typed `Args:` and `Returns:` schema on all 10 worker and 5 orchestrator tools.<br>2) Resilient error contracts returning `RECOVERABLE_ERROR` with actionable `recovery_instruction` fields guiding the LLM how to retry. | §2 |
| **Orchestration & Logic** | 16 / 20 | Lacks explicit Human-in-the-Loop (HITL) hooks pausing high-stakes actions for clinician confirmation. | 1) Stateful HITL confirmation gatekeeper (`ClinicalActionApprovalManager`).<br>2) Tool `request_human_confirmation` for Orchestrator.<br>3) Declarative A2UI `ConfirmationDialog` card with Approve / Reject endpoints (`/api/actions/approve`). | §3 |
| **Observability & Tracing** | 15 / 20 | No active PII/PHI scrubbing in logging, telemetry, or memory pipelines. | HIPAA Safe Harbor & GDPR compliant `PIIScrubber` engine sanitizing patient names, MRNs, SSNs, dates of birth, phone numbers, emails, and addresses in Cloud Logging, Cloud Trace spans, and Memory Bank facts. | §4 |
| **Infrastructure & CI/CD** | 14 / 15 | Hardcoded fallback for JWT secret (`"coscientist-zaa-super-secret-key-32bytes-min!"`). | 1) Eliminate hardcoded secret string.<br>2) Integrate Google Cloud Secret Manager resolution (`projects/{project}/secrets/jwt-secret-key/versions/latest`).<br>3) Cryptographic runtime entropy fallback (`secrets.token_urlsafe(32)`).<br>4) Terraform `google_secret_manager_secret` resource. | §5 |

---

## 2. Tool & Interface Design Remediation (DOC-01, DOC-03)

### 2.1 Complete Parameter Docstring Standard
All tool declarations must supply exhaustive parameter documentation conforming to:
```python
def tool_name(param_a: str, param_b: int = 2) -> Dict[str, Any]:
    """High-level semantic summary of what the tool accomplishes.

    Detailed explanation of clinical, topological, or algorithmic operation.

    Args:
        param_a (str): Required. Canonical entity name or HGNC gene symbol (e.g. 'EGFR', 'Osimertinib').
            Must match standard PrimeKG vocabulary.
        param_b (int): Optional. Graph traversal hop horizon. Must be between 1 and 4.
            Defaults to 2. Larger depths increase query execution time.

    Returns:
        Dict[str, Any]: Structured operational payload containing:
            - status (str): 'SUCCESS', 'RECOVERABLE_ERROR', or 'CRITICAL_FAILURE'.
            - data (Dict[str, Any]): Biological entities, edges, and metrics.
            - execution_time_ms (float): Telemetry execution latency.
            - recovery_instruction (Optional[str]): Actionable guidance if status is not 'SUCCESS'.
    """
```

### 2.2 LLM Recovery Instruction Error Handling Contract
When an entity is not found, a timeout occurs, or parameters are out of bounds, tools must **never** throw unhandled exceptions or return silent synthetic mocks. Instead, tools return structured diagnostic guidance:
```json
{
  "status": "RECOVERABLE_ERROR",
  "error_type": "EntityNotFoundException",
  "error_message": "Node 'EGFR_T790M' was not found in PrimeKGGraph.",
  "recovery_instruction": "The provided biomarker format is not indexed directly. Please retry with canonical HGNC symbol 'EGFR' and filter relationships using biomarker='T790M', or call 'explore_target_subgraph_neighborhood' with focal_entity='EGFR'."
}
```

---

## 3. Human-in-the-Loop (HITL) Gatekeeper (DOC-02, DOC-03)

### 3.1 High-Stakes Action Criteria
Any action matching one of the following high-stakes categories requires explicit human sign-off before downstream execution:
1. **`OFF_LABEL_THERAPY_RECOMMENDATION`**: Proposing combination treatments outside FDA-approved indications.
2. **`EXPERIMENTAL_CLINICAL_TRIAL_ENROLLMENT`**: Recommending Phase I/II investigative protocols.
3. **`HIGH_TOXICITY_REGIMEN_MODIFICATION`**: Altering dosages with known grade 3/4 adverse events (e.g., cardiomyopathy, interstitial lung disease).
4. **`EXPENSIVE_CLUSTER_SIMULATION`**: Launching GKE AlphaFold docking or multi-hour PhysiCell continuous fluid dynamics jobs.
5. **`PATIENT_RECORD_STATE_MUTATION`**: Deleting or replacing confirmed clinical hypotheses in persistent storage.

### 3.2 Gatekeeper Architecture
1. **Agent Tool**: `request_human_confirmation(action_type: str, proposed_action: str, clinical_rationale: str, risk_level: str, parameters: Dict[str, Any]) -> Dict[str, Any]`
2. **Approval Registry (`apps/co-scientist/agent/hitl.py`)**: Stores pending approvals with cryptographically secure token, expiration (30 minutes), and audit metadata.
3. **A2UI Component**: `ConfirmationDialog` / `HumanApprovalCard` emitted to the web client.
4. **API Endpoints**:
   - `GET /api/actions/pending`: Lists pending clinical approval items.
   - `POST /api/actions/{action_id}/approve`: Approves and unblocks execution.
   - `POST /api/actions/{action_id}/reject`: Rejects and notifies orchestrator.

---

## 4. Observability: PII/PHI De-Identification Engine (DOC-01, DOC-02)

### 4.1 HIPAA Safe Harbor & GDPR Rules
All text strings entering logging, tracing, or memory storage must be filtered for Protected Health Information (PHI) and Personally Identifiable Information (PII):
- **Patient Names**: Regex matching clinician titles, patient name conventions (`Patient [A-Z][a-z]+`, `Mr./Ms./Dr. [A-Z][a-z]+`).
- **Medical Record Numbers (MRNs)**: `MRN-\d+`, `PAT-\d+`, `ID:\s*\d+`.
- **Social Security Numbers (SSNs)**: `\d{3}-\d{2}-\d{4}`.
- **Phone Numbers**: `(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}`.
- **Email Addresses**: `[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+`.
- **Dates of Birth (DOB)**: `DOB:\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}`.
- **IP Addresses**: `\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b`.

### 4.2 Sanitization Interceptors
- **Cloud Logging**: `emit_cloud_log()` intercepts all message strings and payloads via `PIIScrubber.scrub()`.
- **OpenTelemetry Tracing**: `trace_span()` and `trace_tool()` sanitize span attributes before recording.
- **Memory Bank**: `MemoryBankEngine.extract_and_consolidate()` sanitizes conversation turns prior to Spanner DDL commits and BigQuery vector embeddings.

---

## 5. Secret Management & Zero Ambient Authority (DOC-02)

### 5.1 Elimination of Hardcoded Secrets
Remove `coscientist-zaa-super-secret-key-32bytes-min!` fallback completely.

### 5.2 Resolution Hierarchy
1. Read `os.getenv("JWT_SECRET_KEY")` or `os.getenv("AUTH_JWT_SECRET")`.
2. If absent and in GCP environment, query Google Cloud Secret Manager:
   `projects/{project_id}/secrets/jwt-secret-key/versions/latest`.
3. If running in offline test or dev sandbox where Secret Manager is unavailable, dynamically generate an ephemeral 256-bit cryptographically random key using `secrets.token_urlsafe(32)` and emit an audit security notice.
4. Define `google_secret_manager_secret.jwt_secret` in Terraform (`apps/co-scientist/iac/secrets.tf`).
