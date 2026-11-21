# AGENT GATEKEEPER – ICICI BANK
### AI Agent Authorization and Governance System (Academic Project)

---

## 📌 Executive Summary

With customers increasingly using external, autonomous AI agents to interact with financial services, banks must implement a **zero-trust gatekeeper** to evaluate and arbitrate agent requests.

**Agent Gatekeeper – ICICI Bank** inspects every inbound AI agent transaction and deterministically renders one of three decisions:
1. **`ALLOW`**: Low-risk, authorized autonomous execution.
2. **`ASK CUSTOMER`**: Elevated-risk operations placed in pending state requiring explicit human-in-the-loop (HITL) step-up confirmation.
3. **`BLOCK`**: Invalid, unauthenticated, out-of-scope, expired, or revoked requests.

> [!IMPORTANT]
> **Academic Prototype Notice**: This system is a simulated academic prototype for AI governance research. It contains **zero live banking APIs, real credentials, or live payment network connectivity**.

---

## 🛠️ Technology Stack

- **Language**: Python 3.10+
- **User Interface**: Streamlit (ICICI Corporate Themed Dashboard)
- **Data Analytics & Audit**: Pandas
- **Persistence**:
  - `JSON`: Agent credentials (hashed), metadata, scopes, and customer profiles.
  - `CSV`: Genuinely append-only, tamper-evident audit logs.

---

## 📁 Modular Project Architecture

```text
c:\Users\indra\Desktop\Agentic AI\
│
├── data/
│   ├── agents.json             # Persistent agent registry (SHA-256 hashed keys, expiry, revocation)
│   ├── customers.json          # Mock customer accounts (Balances, masked accounts)
│   ├── pending_approvals.json  # Queue of 'ASK CUSTOMER' requests awaiting customer action
│   └── audit_logs.csv          # Immutable, append-only historical audit trail
│
├── modules/
│   ├── __init__.py             # Module initialization
│   ├── agent_manager.py        # Registration, SHA-256 key hashing, expiry, revocation with timestamp
│   ├── decision_engine.py      # Rule pipeline (R1 -> R8), UUID Request ID, amount validation
│   ├── approval_manager.py     # Human-in-the-loop workflow, customer binding, anti-replay
│   ├── audit_logger.py         # Strictly append-only CSV logger & Pandas analytics provider
│   └── test_scenarios.py       # Dynamic test runner for the 6 compulsory academic scenarios
│
├── app.py                      # Multi-tab Streamlit Governance Application & Dashboard
├── verify_backend.py           # Automated backend verification test suite
├── PROMPTS.md                  # Comprehensive prompt engineering & system instructions
├── requirements.txt            # Project dependencies
└── README.md                   # Project documentation & viva presentation guide
```

---

## ⚖️ Business Rules & Priority Hierarchy

The gatekeeper processes incoming requests through a **strict short-circuit evaluation pipeline**:

| Priority | Rule ID | Evaluation Condition | Verdict | Justification & Rationale |
| :---: | :---: | :--- | :---: | :--- |
| **1** | **R1** | Missing fields, non-numeric amount, negative amount, or zero financial amount ($\le 0$) | **`BLOCK`** | Schema integrity & payload sanity check. |
| **2** | **R2** | Unknown agent ID or invalid simulated API key hash | **`BLOCK`** | Zero-trust authentication failure. |
| **3** | **R3** | Agent status is `REVOKED` or authorization has `EXPIRED` | **`BLOCK`** | **Revocation takes absolute precedence** over expiry. Records revocation timestamp. |
| **4** | **R4** | Customer ID mismatch, unsupported action, or action outside authorized scopes | **`BLOCK`** | Principle of Least Privilege (PoLP) and customer boundary enforcement. |
| **5** | **R5** | Authorized agent viewing account balance | **`ALLOW`** | Read-only inquiry with zero financial risk. |
| **6** | **R6** | Authorized bill payment with Amount $\le ₹5,000$ | **`ALLOW`** | Autonomous micro-transaction threshold. |
| **7** | **R7** | Authorized bill payment with Amount $> ₹5,000$ | **`ASK CUSTOMER`** | Elevated financial risk; mandates step-up customer confirmation. |
| **8** | **R8** | Authorized fund transfer (Amount $> 0$) | **`ASK CUSTOMER`** | Irreversible external fund movement; strict human-in-the-loop requirement. |

---

## 🔐 Core Security & Governance Invariants

1. **Genuinely Append-Only Audit Logging**:
   - `data/audit_logs.csv` is strictly append-only. Existing records are **never modified or overwritten**.
   - Customer approvals and rejections are logged as **new linked events** referencing the original `request_id`.
2. **Secure Credential Hashing**:
   - Simulated API keys are generated with cryptographic randomness and stored as **SHA-256 hashes** in `agents.json`. Plaintext keys are never persisted.
3. **No Speculative Execution**:
   - A decision of `ASK CUSTOMER` **never executes autonomously**. The transaction remains in a `PENDING` queue until explicitly approved by the mapped customer.
4. **Strict Customer Binding**:
   - Only the customer mapped to a pending request can approve or reject it. Cross-customer resolutions are blocked.
5. **Anti-Replay / Idempotency**:
   - A pending request can only be resolved once. Attempting duplicate resolutions is rejected.

---

## 🧪 Compulsory Academic Test Scenarios

The system includes automated dynamic verification (`modules/test_scenarios.py`) covering all required test scenarios:

1. **Scenario 1 (Schema & Amount Invalidity - R1)**: Missing `customer_id`, negative amount ($-₹750$), or zero-value transfer ($₹0$) $\rightarrow$ **`BLOCK`**.
2. **Scenario 2 (Unknown Agent & Credential Forgery - R2)**: Unregistered agent `AGT-UNKNOWN-999` or falsified API key $\rightarrow$ **`BLOCK`**.
3. **Scenario 3 (Revocation & Expiry - R3)**: Revoked agent (with valid OR invalid API credentials) or expired agent $\rightarrow$ **`BLOCK`** (Revocation precedence strictly enforced).
4. **Scenario 4 (Scope Violation & Customer Mismatch - R4)**: Customer mismatch (`CUST-1002`) or transfer attempt by balance-only bot $\rightarrow$ **`BLOCK`**.
5. **Scenario 5 (Autonomous Low-Risk Execution - R5/R6)**: `View Balance` or `Pay Bill` $\le ₹5,000$ $\rightarrow$ **`ALLOW`**.
6. **Scenario 6 (Human-in-the-Loop Lifecycle - R7/R8)**: `Pay Bill > ₹5,000` or `Transfer Money` placed in `PENDING` $\rightarrow$ Customer approval/rejection lifecycle verification.

---

## 🚀 How to Run the Application

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Module & Backend Verification
```bash
python verify_backend.py
```

### 3. Launch the Streamlit Governance Dashboard
```bash
streamlit run app.py
```

The application will launch in your browser at `http://localhost:8501`.

---

## 🎓 Academic Evaluation & Viva Guide

When explaining this project to examiners:
1. **Explain the Motivation**: Highlight that AI agents cannot have unfettered banking access; a policy gatekeeper is essential for safety, regulatory compliance, and non-repudiation.
2. **Walk Through the Priority Hierarchy**: Explain why R1 (Schema) and R2 (Authentication) are evaluated before R3 (Revocation) and R4 (Scopes), and why R5-R8 only execute after all security checks pass.
3. **Demonstrate the Human-in-the-Loop**: Show how an `ASK CUSTOMER` decision does not execute the transaction, but holds it safely in the customer approval portal until authorized.
4. **Showcase Audit Immutability**: Explain that the CSV audit log is append-only, ensuring non-repudiation and forensic traceability.
