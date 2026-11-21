"""
Approval Manager Module
Handles the human-in-the-loop lifecycle for high-risk 'ASK CUSTOMER' transactions.
Ensures transactions are never executed automatically, verifies customer identity,
prevents double-resolution, and writes linked append-only audit events.
"""

import json
import os
from datetime import datetime
from modules import audit_logger

PENDING_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "pending_approvals.json")


def _load_pending_records() -> list:
    """Loads all approval records from data/pending_approvals.json."""
    if not os.path.exists(PENDING_FILE_PATH):
        return []
    try:
        with open(PENDING_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_pending_records(records: list) -> None:
    """Saves approval records to data/pending_approvals.json."""
    os.makedirs(os.path.dirname(PENDING_FILE_PATH), exist_ok=True)
    with open(PENDING_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def create_pending_approval(request_dict: dict) -> dict:
    """
    Enqueues a high-risk transaction requiring customer confirmation.
    Transaction remains strictly PENDING and is NOT executed.
    """
    records = _load_pending_records()
    
    # Avoid duplicate pending insertion for same request_id
    req_id = request_dict.get("request_id")
    for rec in records:
        if rec.get("request_id") == req_id:
            return rec
            
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "request_id": req_id,
        "enqueued_timestamp": now_str,
        "agent_id": request_dict.get("agent_id"),
        "agent_name": request_dict.get("agent_name", "Unknown Agent"),
        "customer_id": request_dict.get("customer_id"),
        "action": request_dict.get("action"),
        "amount": request_dict.get("amount"),
        "rule_triggered": request_dict.get("rule_triggered"),
        "reason": request_dict.get("reason"),
        "status": "PENDING",
        "resolution": None,
        "resolution_timestamp": None,
        "resolved_by_customer": None,
        "comments": ""
    }
    
    records.append(entry)
    _save_pending_records(records)
    return entry


def get_pending_approvals(customer_id: str | None = None) -> list:
    """
    Retrieves all pending approval requests.
    Optionally filters by the specific customer mapped to the request.
    """
    records = _load_pending_records()
    pending = [r for r in records if r.get("status") == "PENDING"]
    if customer_id:
        pending = [r for r in pending if r.get("customer_id") == customer_id]
    return pending


def get_all_approvals() -> list:
    """Retrieves all approvals (both pending and resolved)."""
    return _load_pending_records()


def resolve_approval(
    request_id: str,
    customer_id: str,
    resolution: str,
    comments: str = ""
) -> tuple[bool, str, dict | None]:
    """
    Resolves a pending customer approval.
    
    Security & Integrity Rules:
    1. Resolution must be 'APPROVE' or 'REJECT'.
    2. Only the customer mapped to the transaction can resolve it.
    3. A request can never be resolved more than once (idempotent / anti-replay).
    4. Genuinely append-only audit trail: logs a new linked event in audit_logs.csv.
    
    Returns:
        (success: bool, message: str, updated_record: dict | None)
    """
    resolution = resolution.strip().upper()
    if resolution not in ["APPROVE", "REJECT"]:
        return False, f"Invalid resolution '{resolution}'. Must be APPROVE or REJECT.", None
        
    records = _load_pending_records()
    target_record = None
    
    for rec in records:
        if rec.get("request_id") == request_id:
            target_record = rec
            break
            
    if not target_record:
        return False, f"Approval request with ID '{request_id}' not found.", None
        
    # Check 1: Must be in PENDING state (prevents duplicate resolution)
    if target_record.get("status") != "PENDING":
        prev_res = target_record.get("resolution", "RESOLVED")
        prev_ts = target_record.get("resolution_timestamp", "N/A")
        return False, f"Request '{request_id}' is already {prev_res} on {prev_ts}. Cannot resolve again.", target_record
        
    # Check 2: Customer authorization check (Only mapped customer can act)
    mapped_customer = target_record.get("customer_id")
    if mapped_customer != customer_id:
        return False, f"Unauthorized: Transaction belongs to customer '{mapped_customer}', but '{customer_id}' attempted resolution.", None
        
    # Update record state
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_label = "RESOLVED_APPROVED" if resolution == "APPROVE" else "RESOLVED_REJECTED"
    
    target_record["status"] = status_label
    target_record["resolution"] = resolution
    target_record["resolution_timestamp"] = now_str
    target_record["resolved_by_customer"] = customer_id
    target_record["comments"] = comments.strip()
    
    _save_pending_records(records)
    
    # Append-only audit log: Create new linked event linked by request_id
    event_type = "CUSTOMER_APPROVAL" if resolution == "APPROVE" else "CUSTOMER_REJECTION"
    decision_text = "APPROVED" if resolution == "APPROVE" else "REJECTED"
    reason_text = f"Customer {customer_id} explicitly {decision_text.lower()} the transaction."
    
    audit_logger.log_event(
        request_id=request_id,
        event_type=event_type,
        agent_id=target_record.get("agent_id", ""),
        customer_id=customer_id,
        action=target_record.get("action", ""),
        amount=target_record.get("amount"),
        decision=decision_text,
        rule_triggered=target_record.get("rule_triggered", "HITL"),
        reason=reason_text,
        actor=customer_id,
        details=f"Customer notes: '{comments}'. Action finalized: {status_label}."
    )
    
    return True, f"Transaction '{request_id}' successfully {decision_text} by customer.", target_record
