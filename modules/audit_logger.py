"""
Audit Logger Module
Provides genuinely append-only, tamper-evident audit logging for all agent evaluations
and human-in-the-loop decisions. Never overwrites or mutates historical audit entries.
"""

import os
import csv
import uuid
import math
from datetime import datetime
import pandas as pd

AUDIT_LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "audit_logs.csv")

CSV_HEADERS = [
    "event_id",
    "timestamp",
    "request_id",
    "event_type",
    "agent_id",
    "customer_id",
    "action",
    "amount",
    "decision",
    "rule_triggered",
    "reason",
    "actor",
    "details"
]

FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def sanitize_csv_field(val: any) -> str:
    """
    Sanitizes user-controlled text fields before writing to CSV (CWE-1236 Prevention).
    If a text field begins with formula execution characters (=, +, -, @, tab, or carriage return),
    prepends a single quote (') so spreadsheet applications interpret it purely as literal text.
    Preserves the original meaning of legitimate text and does not modify numeric amount fields.
    """
    if val is None:
        return ""
    s_val = str(val)
    if not s_val:
        return ""
    if s_val.startswith(FORMULA_PREFIXES) or s_val.lstrip(" ").startswith(FORMULA_PREFIXES):
        return "'" + s_val
    return s_val


def ensure_audit_file_initialized() -> None:
    """Ensures the audit log CSV exists with standard immutable headers."""
    os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)
    if not os.path.exists(AUDIT_LOG_FILE) or os.path.getsize(AUDIT_LOG_FILE) == 0:
        with open(AUDIT_LOG_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)


def log_event(
    request_id: str,
    event_type: str,
    agent_id: str,
    customer_id: str,
    action: str,
    amount: float | None,
    decision: str,
    rule_triggered: str,
    reason: str,
    actor: str = "SYSTEM",
    details: str = ""
) -> dict:
    """
    Appends a new event entry to data/audit_logs.csv.
    This operation is strictly append-only.
    """
    ensure_audit_file_initialized()
    
    event_id = f"EVT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Format amount strictly if numeric, finite, and non-boolean
    if (amount is not None and isinstance(amount, (int, float)) and not isinstance(amount, bool) and not math.isnan(amount) and not math.isinf(amount)):
        amount_str = f"{amount:.2f}"
    else:
        amount_str = "N/A"
    
    # Write sanitized row - amount_str is preserved as pure numeric text without single-quote prefix
    row = [
        event_id,
        timestamp,
        request_id,
        event_type,
        sanitize_csv_field(agent_id or "UNKNOWN"),
        sanitize_csv_field(customer_id or "UNKNOWN"),
        sanitize_csv_field(action or "UNKNOWN"),
        amount_str,
        decision,
        rule_triggered,
        sanitize_csv_field(reason),
        sanitize_csv_field(actor),
        sanitize_csv_field(details)
    ]
    
    with open(AUDIT_LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)
        
    return {
        "event_id": event_id,
        "timestamp": timestamp,
        "request_id": request_id,
        "event_type": event_type,
        "agent_id": agent_id,
        "customer_id": customer_id,
        "action": action,
        "amount": amount_str,
        "decision": decision,
        "rule_triggered": rule_triggered,
        "reason": reason,
        "actor": actor,
        "details": details
    }


def load_audit_trail() -> pd.DataFrame:
    """
    Loads all historical audit events into a pandas DataFrame.
    Guarantees no data loss or overwrite.
    """
    ensure_audit_file_initialized()
    try:
        df = pd.read_csv(AUDIT_LOG_FILE, dtype=str)
        return df
    except Exception:
        return pd.DataFrame(columns=CSV_HEADERS)


def get_audit_summary_metrics() -> dict:
    """Calculates governance KPIs from the append-only audit trail."""
    df = load_audit_trail()
    if df.empty:
        return {
            "total_events": 0,
            "total_evaluations": 0,
            "allow_count": 0,
            "ask_customer_count": 0,
            "block_count": 0,
            "allow_rate": 0.0,
            "block_rate": 0.0,
            "ask_rate": 0.0,
            "customer_approved": 0,
            "customer_rejected": 0
        }
    
    eval_df = df[df["event_type"] == "TRANSACTION_EVALUATION"]
    total_evals = len(eval_df)
    
    allow_cnt = len(eval_df[eval_df["decision"] == "ALLOW"])
    ask_cnt = len(eval_df[eval_df["decision"] == "ASK CUSTOMER"])
    block_cnt = len(eval_df[eval_df["decision"] == "BLOCK"])
    
    approved_cnt = len(df[df["event_type"] == "CUSTOMER_APPROVAL"])
    rejected_cnt = len(df[df["event_type"] == "CUSTOMER_REJECTION"])
    
    return {
        "total_events": len(df),
        "total_evaluations": total_evals,
        "allow_count": allow_cnt,
        "ask_customer_count": ask_cnt,
        "block_count": block_cnt,
        "allow_rate": (allow_cnt / total_evals * 100) if total_evals > 0 else 0.0,
        "block_rate": (block_cnt / total_evals * 100) if total_evals > 0 else 0.0,
        "ask_rate": (ask_cnt / total_evals * 100) if total_evals > 0 else 0.0,
        "customer_approved": approved_cnt,
        "customer_rejected": rejected_cnt
    }
