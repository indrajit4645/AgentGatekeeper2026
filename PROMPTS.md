# Agent Gatekeeper – ICICI Bank
## Academic Specification, System Prompts & Governance Architecture

---

## 1. Project Overview & Academic Objective

- **Project Title**: AGENT GATEKEEPER – ICICI BANK
- **Domain**: AI Agent Authorization, Governance & Human-in-the-Loop (HITL) Controls for Autonomous Banking Systems
- **Type**: Simulated Academic Security Prototype (Zero Live Banking APIs)
- **Primary Objective**: Determine whether an external autonomous AI agent requesting banking actions on behalf of a customer should be **ALLOWED**, **ASK CUSTOMER** (Human-in-the-Loop), or **BLOCKED**.

---

## 2. Business Problem & Context

With customers increasingly utilizing autonomous external AI agents (e.g., automated bill managers, personal finance planners, shopping assistants), banks face a critical security boundary problem:

1. **Identity & Delegation Risk**: How does the bank verify that an external agent is authentic, has not been tampered with, and is legitimately delegated by the account owner?
2. **Scope Overreach**: An agent authorized only for account balance monitoring must never be allowed to execute fund transfers.
3. **Financial Limit & Non-Repudiation**: Automated low-risk actions (e.g., small utility payments) may execute autonomously, whereas high-value payments and irreversible money transfers require explicit step-up authentication.
4. **Lifecycle Control & Instant Kill-Switch**: The customer must be able to immediately revoke an agent's privileges, with immediate effect and verifiable timestamp recording.

---

## 3. Supported Banking Actions & Data Models

| Action Name | Type | Amount Required? | Autonomous Limit | Governance Category |
| :--- | :--- | :--- | :--- | :--- |
| **`View Balance`** | Read-Only | No | N/A | Low Risk (Rule R5) |
| **`Pay Bill`** | Financial / Settlement | Yes ($> 0$) | $\le ₹5,000$ | Autonomous if $\le ₹5,000$ (R6); Escalated if $> ₹5,000$ (R7) |
| **`Transfer Money`** | Financial / Fund Movement | Yes ($> 0$) | None | High Risk / Strict Customer Approval (R8) |

---

## 4. Rule-Based Decision Engine (R1 – R8 Priority Order)

The Gatekeeper enforces a **deterministic short-circuit evaluation pipeline**. The earliest matched rule determines the terminal decision:

```text
Incoming Request Payload
        │
        ▼
   [Rule R1] ─── Missing fields, non-numeric or amount <= 0 ? ──────► BLOCK
        │ (Valid Schema)
        ▼
   [Rule R2] ─── Unknown agent ID (not registered) ? ───────────────► BLOCK
        │ (Registered Agent Identified)
        ▼
   [Rule R3] ─── Agent status is REVOKED ? ──────────────────────────► BLOCK (Precedence 1)
        │       (Evaluated before credential check; guarantees
        │        revoked agents trigger R3 even with invalid keys)
        ▼
   [Rule R2] ─── Non-revoked agent with invalid API key hash ? ─────► BLOCK (Authentication)
        │ (Authenticated Active Agent)
        ▼
   [Rule R3] ─── Authorization expired (current > valid_until) ? ───► BLOCK (Precedence 2)
        │ (Active & Valid Date)
        ▼
   [Rule R4] ─── Customer mismatch, unsupported action, or scope ? ─► BLOCK
        │ (Authorized)
        ▼
   [Rule R5] ─── Action == "View Balance" ? ─────────────────────────► ALLOW
        │ (No)
        ▼
   [Rule R6] ─── Action == "Pay Bill" and Amount <= ₹5,000 ? ────────► ALLOW
        │ (No)
        ▼
   [Rule R7] ─── Action == "Pay Bill" and Amount > ₹5,000 ? ─────────► ASK CUSTOMER (PENDING)
        │ (No)
        ▼
   [Rule R8] ─── Action == "Transfer Money" (Amount > 0) ? ──────────► ASK CUSTOMER (PENDING)
```

### Rule Definitions:
- **`R1`**: **Missing or Invalid Request Information $\rightarrow$ `BLOCK`**.
  - Enforces mandatory fields (`agent_id`, `customer_id`, `action`, `api_key`).
  - Enforces positive amount ($> 0$) for financial transactions (`Pay Bill`, `Transfer Money`).
  - Flags non-numeric, zero, or negative amounts.
- **`R2`**: **Unknown Agent or Invalid Credentials $\rightarrow$ `BLOCK`**.
  - Validates agent presence in `agents.json`.
  - Verifies simulated API key using SHA-256 constant-time hash comparison (`hmac.compare_digest`).
- **`R3`**: **Revoked or Expired Agent $\rightarrow$ `BLOCK`**.
  - **Revocation takes absolute precedence**: A revoked agent is blocked immediately with the recorded revocation timestamp and reason.
  - An agent is valid through the end of their `valid_until` date; if current date surpasses it, requests are blocked as expired.
- **`R4`**: **Customer Mismatch, Unsupported Action, or Scope Violation $\rightarrow$ `BLOCK`**.
  - Enforces customer binding: An agent cannot act on behalf of a customer other than its registered owner.
  - Enforces action whitelist (`allowed_actions`).
- **`R5`**: **Authorized Balance View $\rightarrow$ `ALLOW`**.
  - Read-only action with zero financial loss risk.
- **`R6`**: **Authorized Bill Payment Up to ₹5,000 $\rightarrow$ `ALLOW`**.
  - Standard recurring micro-payment allowance.
- **`R7`**: **Authorized Bill Payment Above ₹5,000 $\rightarrow$ `ASK CUSTOMER`**.
  - Exceeds autonomous threshold; enqueues request as `PENDING` in `approval_manager.py`.
- **`R8`**: **Authorized Fund Transfer $\rightarrow$ `ASK CUSTOMER`**.
  - External fund movements always mandate customer human-in-the-loop sign-off.

---

## 5. Security Invariants & Governance Principles

1. **Simulated Zero-Trust Environment**:
   - Zero live banking connectivity.
   - All API keys, accounts, and transactions are simulated mock entities.
2. **Credential Hashing**:
   - Plaintext API keys are never persisted. Only salted/SHA-256 hashes are stored in `agents.json`.
3. **Genuinely Append-Only Audit Trail**:
   - Historical records in `audit_logs.csv` are immutable and never modified or deleted.
   - Subsequent customer actions (`APPROVE` or `REJECT`) are recorded as **new events** linked by the original `request_id`.
4. **Idempotent Human-In-The-Loop**:
   - Only the mapped customer can approve or reject a transaction.
   - Double-resolution / replay attacks are strictly prohibited.
5. **No Speculative Execution**:
   - An `ASK CUSTOMER` decision **never** executes automatically. It remains paused until customer resolution is recorded.

---

## 6. Prompt Engineering Templates for Autonomous AI Agents

When external agents interact with the Gatekeeper API, they must structure their intent according to the following system instructions:

### System Prompt for Banking Assistant Agent:
```text
You are an autonomous AI banking assistant acting on behalf of an ICICI Bank customer.
When requesting banking actions:
1. Always authenticate using your registered agent_id and secret simulated api_key.
2. Ensure you specify the target customer_id matching your authorized delegation.
3. For financial transactions (Pay Bill, Transfer Money), always provide a valid, positive, non-zero amount.
4. For read-only balance checks, omit the amount field or pass null.
5. If the Gatekeeper responds with 'ASK CUSTOMER', inform the customer that their confirmation is required in the ICICI Gatekeeper Approval Portal before any money can be moved.
6. If the Gatekeeper responds with 'BLOCK', terminate the action immediately and report the security reason to the user.
```

---

## 7. Compulsory Test Scenarios Traceability Matrix

| Scenario ID | Test Name | Injected Fault / Condition | Expected Outcome | Triggered Rule |
| :--- | :--- | :--- | :--- | :--- |
| **TS-1** | Invalid Payload / Zero Amount | Missing `customer_id`, Negative amount, or ₹0 transfer | **`BLOCK`** | **`R1`** |
| **TS-2** | Unknown / Forged Agent | Unregistered ID `AGT-UNKNOWN-999` or falsified API key | **`BLOCK`** | **`R2`** |
| **TS-3** | Revoked / Expired Agent | Revoked agent (with valid or invalid credentials) or Expired agent | **`BLOCK`** | **`R3`** |
| **TS-4** | Scope / Customer Mismatch | Customer mismatch (`CUST-1002`) or out-of-scope transfer | **`BLOCK`** | **`R4`** |
| **TS-5** | Low-Risk Autonomous Execution | `View Balance` or `Pay Bill` of ₹3,450 ($\le ₹5,000$) | **`ALLOW`** | **`R5` / `R6`** |
| **TS-6** | High-Risk Human-in-the-Loop | `Pay Bill` of ₹18,000 or `Transfer Money` $\rightarrow$ Customer Approval | **`ASK CUSTOMER`** | **`R7` / `R8`** |
