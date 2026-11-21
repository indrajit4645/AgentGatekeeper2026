"""
Decision Engine Module
Evaluates external AI agent transaction requests against strict, prioritized governance rules (R1 to R8).
Produces deterministic decisions: ALLOW, ASK CUSTOMER, or BLOCK.
Integrates with agent_manager, approval_manager, and audit_logger.
"""

import uuid
import math
from datetime import datetime
from modules import agent_manager
from modules import audit_logger
from modules import approval_manager

SUPPORTED_ACTIONS = ["View Balance", "Pay Bill", "Transfer Money"]


def generate_request_id() -> str:
    """Generates a unique, traceable Request ID."""
    return f"REQ-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


def evaluate_transaction(payload: dict) -> dict:
    """
    Evaluates an incoming AI agent request through the prioritized rule pipeline R1 -> R8.
    
    Priority Order:
    - R1: Schema & Payload Validity (Missing fields, negative or zero financial amounts)
    - R2: Agent Identity & Credential Auth (Unknown agent or invalid simulated API key)
    - R3: Agent Lifecycle Status (Revoked agent or expired authorization date)
          [Note: Revocation ALWAYS takes precedence over expiry]
    - R4: Customer Binding & Action Scope (Customer mismatch, unsupported or unauthorized action)
    - R5: Authorized View Balance (ALLOW)
    - R6: Authorized Pay Bill <= 5,000 (ALLOW)
    - R7: Authorized Pay Bill > 5,000 (ASK CUSTOMER)
    - R8: Authorized Transfer Money (ASK CUSTOMER)
    """
    request_id = generate_request_id()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # -------------------------------------------------------------
    # RULE R1: Missing or invalid request information
    # -------------------------------------------------------------
    if not isinstance(payload, dict):
        decision = "BLOCK"
        rule = "R1"
        reason = "Request payload must be a valid JSON dictionary."
        audit_logger.log_event(request_id, "TRANSACTION_EVALUATION", "", "", "", None, decision, rule, reason)
        return _build_response(request_id, now_str, decision, rule, reason, payload, "REJECTED")
    
    agent_id = str(payload.get("agent_id") or "").strip()
    customer_id = str(payload.get("customer_id") or "").strip()
    action = str(payload.get("action") or "").strip()
    api_key = str(payload.get("api_key") or "").strip()
    raw_amount = payload.get("amount")
    
    # Check mandatory string fields
    if not agent_id or not customer_id or not action or not api_key:
        missing = []
        if not agent_id: missing.append("agent_id")
        if not customer_id: missing.append("customer_id")
        if not action: missing.append("action")
        if not api_key: missing.append("api_key")
        
        decision = "BLOCK"
        rule = "R1"
        reason = f"Missing mandatory field(s): {', '.join(missing)}."
        audit_logger.log_event(request_id, "TRANSACTION_EVALUATION", agent_id, customer_id, action, None, decision, rule, reason)
        return _build_response(request_id, now_str, decision, rule, reason, payload, "REJECTED")

    # Financial action amount validation
    amount = None
    if action in ["Pay Bill", "Transfer Money"]:
        if raw_amount is None or raw_amount == "":
            decision = "BLOCK"
            rule = "R1"
            reason = f"Financial action '{action}' requires a valid transaction amount."
            audit_logger.log_event(request_id, "TRANSACTION_EVALUATION", agent_id, customer_id, action, None, decision, rule, reason)
            return _build_response(request_id, now_str, decision, rule, reason, payload, "REJECTED")

        # SEC-03: Explicitly reject boolean amounts before float conversion
        if isinstance(raw_amount, bool):
            decision = "BLOCK"
            rule = "R1"
            reason = f"Boolean value '{raw_amount}' is not a valid transaction amount for '{action}'."
            audit_logger.log_event(request_id, "TRANSACTION_EVALUATION", agent_id, customer_id, action, None, decision, rule, reason)
            return _build_response(request_id, now_str, decision, rule, reason, payload, "REJECTED")

        try:
            amount = float(raw_amount)
        except (ValueError, TypeError):
            decision = "BLOCK"
            rule = "R1"
            reason = f"Invalid amount format: '{raw_amount}'. Must be a positive numeric value."
            audit_logger.log_event(request_id, "TRANSACTION_EVALUATION", agent_id, customer_id, action, None, decision, rule, reason)
            return _build_response(request_id, now_str, decision, rule, reason, payload, "REJECTED")

        # SEC-02: Reject NaN, positive Infinity, and negative Infinity
        if math.isnan(amount) or math.isinf(amount):
            decision = "BLOCK"
            rule = "R1"
            reason = f"Non-finite amount '{raw_amount}' (NaN or Infinity) is not a permitted transaction amount."
            audit_logger.log_event(request_id, "TRANSACTION_EVALUATION", agent_id, customer_id, action, None, decision, rule, reason)
            return _build_response(request_id, now_str, decision, rule, reason, payload, "REJECTED")

        if amount <= 0:
            decision = "BLOCK"
            rule = "R1"
            reason = f"Transaction amount must be strictly greater than zero (received: {amount})."
            audit_logger.log_event(request_id, "TRANSACTION_EVALUATION", agent_id, customer_id, action, amount, decision, rule, reason)
            return _build_response(request_id, now_str, decision, rule, reason, payload, "REJECTED", amount)
    elif action == "View Balance":
        # Amount not required for View Balance; if provided, validate type and sanity
        if raw_amount is not None and raw_amount != "":
            if isinstance(raw_amount, bool):
                decision = "BLOCK"
                rule = "R1"
                reason = f"Boolean value '{raw_amount}' is not a valid amount."
                audit_logger.log_event(request_id, "TRANSACTION_EVALUATION", agent_id, customer_id, action, None, decision, rule, reason)
                return _build_response(request_id, now_str, decision, rule, reason, payload, "REJECTED")
            try:
                amt_val = float(raw_amount)
                if math.isnan(amt_val) or math.isinf(amt_val) or amt_val < 0:
                    decision = "BLOCK"
                    rule = "R1"
                    reason = f"Invalid amount '{raw_amount}' provided in read-only request."
                    audit_logger.log_event(request_id, "TRANSACTION_EVALUATION", agent_id, customer_id, action, None, decision, rule, reason)
                    return _build_response(request_id, now_str, decision, rule, reason, payload, "REJECTED")
            except (ValueError, TypeError):
                pass
        amount = None

    # -------------------------------------------------------------
    # RULE R2 (Agent Identification): Unknown agent check
    # -------------------------------------------------------------
    agent_record = agent_manager.get_agent_by_id(agent_id)
    if not agent_record:
        decision = "BLOCK"
        rule = "R2"
        reason = f"Unknown agent ID '{agent_id}'. Agent is not registered in the Gatekeeper registry."
        audit_logger.log_event(request_id, "TRANSACTION_EVALUATION", agent_id, customer_id, action, amount, decision, rule, reason)
        return _build_response(request_id, now_str, decision, rule, reason, payload, "REJECTED", amount)

    # -------------------------------------------------------------
    # RULE R3 (Lifecycle Precedence): Revoked agent check
    # Revocation takes absolute priority: A revoked agent is always blocked
    # under R3 regardless of whether provided API credentials are valid or invalid.
    # -------------------------------------------------------------
    if agent_record.get("status") == "REVOKED":
        rev_ts = agent_record.get("revocation_timestamp", "N/A")
        rev_reason = agent_record.get("revocation_reason", "Unspecified")
        decision = "BLOCK"
        rule = "R3"
        reason = f"Agent '{agent_id}' has been REVOKED on {rev_ts} (Reason: {rev_reason})."
        audit_logger.log_event(request_id, "TRANSACTION_EVALUATION", agent_id, customer_id, action, amount, decision, rule, reason)
        return _build_response(request_id, now_str, decision, rule, reason, payload, "REJECTED", amount)

    # -------------------------------------------------------------
    # RULE R2 (Credential Authentication): Active agent credential verification
    # Verifies simulated API key hash for non-revoked agents.
    # -------------------------------------------------------------
    stored_key_hash = agent_record.get("api_key_hash", "")
    if not agent_manager.verify_api_key(api_key, stored_key_hash):
        decision = "BLOCK"
        rule = "R2"
        reason = f"Authentication failed for agent '{agent_id}'. Invalid simulated API credentials."
        audit_logger.log_event(request_id, "TRANSACTION_EVALUATION", agent_id, customer_id, action, amount, decision, rule, reason)
        return _build_response(request_id, now_str, decision, rule, reason, payload, "REJECTED", amount)

    # -------------------------------------------------------------
    # RULE R3 (Expiry): Expired authorization date check
    # -------------------------------------------------------------
    if agent_manager.is_agent_expired(agent_record):
        valid_until = agent_record.get("valid_until", "N/A")
        decision = "BLOCK"
        rule = "R3"
        reason = f"Agent '{agent_id}' authorization expired on {valid_until}. Current requests are blocked."
        audit_logger.log_event(request_id, "TRANSACTION_EVALUATION", agent_id, customer_id, action, amount, decision, rule, reason)
        return _build_response(request_id, now_str, decision, rule, reason, payload, "REJECTED", amount)

    # -------------------------------------------------------------
    # RULE R4: Customer mismatch, unsupported action, or unauthorized action
    # -------------------------------------------------------------
    bound_customer = agent_record.get("customer_id")
    if customer_id != bound_customer:
        decision = "BLOCK"
        rule = "R4"
        reason = f"Customer ID mismatch. Agent '{agent_id}' is authorized for '{bound_customer}', but request targeted '{customer_id}'."
        audit_logger.log_event(request_id, "TRANSACTION_EVALUATION", agent_id, customer_id, action, amount, decision, rule, reason)
        return _build_response(request_id, now_str, decision, rule, reason, payload, "REJECTED", amount)

    if action not in SUPPORTED_ACTIONS:
        decision = "BLOCK"
        rule = "R4"
        reason = f"Unsupported banking action '{action}'. Supported actions are: {', '.join(SUPPORTED_ACTIONS)}."
        audit_logger.log_event(request_id, "TRANSACTION_EVALUATION", agent_id, customer_id, action, amount, decision, rule, reason)
        return _build_response(request_id, now_str, decision, rule, reason, payload, "REJECTED", amount)

    allowed_actions = agent_record.get("allowed_actions", [])
    if action not in allowed_actions:
        decision = "BLOCK"
        rule = "R4"
        reason = f"Action '{action}' is not in agent '{agent_id}' authorized scopes ({allowed_actions})."
        audit_logger.log_event(request_id, "TRANSACTION_EVALUATION", agent_id, customer_id, action, amount, decision, rule, reason)
        return _build_response(request_id, now_str, decision, rule, reason, payload, "REJECTED", amount)

    # -------------------------------------------------------------
    # RULE R5: Authorized agent viewing account balance – ALLOW
    # -------------------------------------------------------------
    if action == "View Balance":
        decision = "ALLOW"
        rule = "R5"
        reason = "Authorized agent viewing account balance (read-only low risk)."
        audit_logger.log_event(request_id, "TRANSACTION_EVALUATION", agent_id, customer_id, action, None, decision, rule, reason)
        return _build_response(request_id, now_str, decision, rule, reason, payload, "EXECUTED")

    # -------------------------------------------------------------
    # RULE R6: Authorized bill payment up to ₹5,000 – ALLOW
    # -------------------------------------------------------------
    if action == "Pay Bill" and amount <= 5000.0:
        decision = "ALLOW"
        rule = "R6"
        reason = f"Authorized bill payment of ₹{amount:,.2f} is within the autonomous threshold of ₹5,000."
        audit_logger.log_event(request_id, "TRANSACTION_EVALUATION", agent_id, customer_id, action, amount, decision, rule, reason)
        return _build_response(request_id, now_str, decision, rule, reason, payload, "EXECUTED", amount)

    # -------------------------------------------------------------
    # RULE R7: Authorized bill payment above ₹5,000 – ASK CUSTOMER
    # -------------------------------------------------------------
    if action == "Pay Bill" and amount > 5000.0:
        decision = "ASK CUSTOMER"
        rule = "R7"
        reason = f"Authorized bill payment of ₹{amount:,.2f} exceeds ₹5,000 threshold. Placed in pending customer approval."
        
        # Enqueue in approval manager (never auto-execute)
        approval_manager.create_pending_approval({
            "request_id": request_id,
            "timestamp": now_str,
            "agent_id": agent_id,
            "agent_name": agent_record.get("agent_name"),
            "customer_id": customer_id,
            "action": action,
            "amount": amount,
            "rule_triggered": rule,
            "reason": reason
        })
        
        audit_logger.log_event(request_id, "TRANSACTION_EVALUATION", agent_id, customer_id, action, amount, decision, rule, reason, details="Pending Customer Approval")
        return _build_response(request_id, now_str, decision, rule, reason, payload, "HELD_FOR_CUSTOMER_APPROVAL", amount, requires_approval=True)

    # -------------------------------------------------------------
    # RULE R8: Authorized fund transfer – ASK CUSTOMER
    # -------------------------------------------------------------
    if action == "Transfer Money":
        decision = "ASK CUSTOMER"
        rule = "R8"
        reason = f"Authorized money transfer of ₹{amount:,.2f} requires explicit customer sign-off (irreversible fund movement)."
        
        # Enqueue in approval manager (never auto-execute)
        approval_manager.create_pending_approval({
            "request_id": request_id,
            "timestamp": now_str,
            "agent_id": agent_id,
            "agent_name": agent_record.get("agent_name"),
            "customer_id": customer_id,
            "action": action,
            "amount": amount,
            "rule_triggered": rule,
            "reason": reason
        })
        
        audit_logger.log_event(request_id, "TRANSACTION_EVALUATION", agent_id, customer_id, action, amount, decision, rule, reason, details="Pending Customer Approval")
        return _build_response(request_id, now_str, decision, rule, reason, payload, "HELD_FOR_CUSTOMER_APPROVAL", amount, requires_approval=True)

    # Fallback safety block
    decision = "BLOCK"
    rule = "R1"
    reason = "Request could not be resolved by any rule."
    audit_logger.log_event(request_id, "TRANSACTION_EVALUATION", agent_id, customer_id, action, amount, decision, rule, reason)
    return _build_response(request_id, now_str, decision, rule, reason, payload, "REJECTED", amount)


def _build_response(
    request_id: str,
    timestamp: str,
    decision: str,
    rule_triggered: str,
    reason: str,
    payload: dict,
    execution_status: str,
    amount: float | None = None,
    requires_approval: bool = False
) -> dict:
    """Standardizes decision engine output structure."""
    return {
        "request_id": request_id,
        "timestamp": timestamp,
        "decision": decision,
        "rule_triggered": rule_triggered,
        "reason": reason,
        "agent_id": payload.get("agent_id") if isinstance(payload, dict) else "",
        "customer_id": payload.get("customer_id") if isinstance(payload, dict) else "",
        "action": payload.get("action") if isinstance(payload, dict) else "",
        "amount": amount,
        "requires_approval": requires_approval,
        "execution_status": execution_status
    }
