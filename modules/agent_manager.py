"""
Agent Manager Module
Manages AI agent registration, simulated API credentials, lifecycle statuses,
expiry dates, and revocation with persistent JSON storage.
"""

import json
import os
import secrets
import hashlib
import hmac
import uuid
from datetime import datetime, date

AGENTS_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "agents.json")

# Default seeds for academic evaluation and reproducible test scenarios
DEFAULT_SEEDS = [
    {
        "agent_id": "AGT-ICICI-001",
        "agent_name": "ICICI Primary Autonomous Bot",
        "agent_type": "Full-Service Banking Bot",
        "customer_id": "CUST-1001",
        "allowed_actions": ["View Balance", "Pay Bill", "Transfer Money"],
        "valid_until": "2028-12-31",
        "raw_key": "icici_sim_agt001_live_a1b2c3d4",
        "status": "ACTIVE",
        "registration_timestamp": "2026-01-10 10:00:00",
        "revocation_timestamp": None,
        "revocation_reason": None
    },
    {
        "agent_id": "AGT-ICICI-002",
        "agent_name": "Balance & Statement Bot",
        "agent_type": "Read-Only Assistant",
        "customer_id": "CUST-1001",
        "allowed_actions": ["View Balance"],
        "valid_until": "2028-12-31",
        "raw_key": "icici_sim_agt002_live_e5f6g7h8",
        "status": "ACTIVE",
        "registration_timestamp": "2026-02-15 11:30:00",
        "revocation_timestamp": None,
        "revocation_reason": None
    },
    {
        "agent_id": "AGT-ICICI-003",
        "agent_name": "Compromised Third-Party Bot",
        "agent_type": "Payment Bot",
        "customer_id": "CUST-1001",
        "allowed_actions": ["View Balance", "Pay Bill"],
        "valid_until": "2028-12-31",
        "raw_key": "icici_sim_agt003_live_i9j0k1l2",
        "status": "REVOKED",
        "registration_timestamp": "2026-01-05 09:15:00",
        "revocation_timestamp": "2026-11-20 14:30:00",
        "revocation_reason": "Security Alert: Suspicious bot activity reported by customer"
    },
    {
        "agent_id": "AGT-ICICI-004",
        "agent_name": "Expired FY23 Financial Assistant",
        "agent_type": "Seasonal Tax Bot",
        "customer_id": "CUST-1001",
        "allowed_actions": ["View Balance", "Pay Bill"],
        "valid_until": "2024-01-01",
        "raw_key": "icici_sim_agt004_live_m3n4o5p6",
        "status": "ACTIVE",
        "registration_timestamp": "2023-01-01 08:00:00",
        "revocation_timestamp": None,
        "revocation_reason": None
    }
]


def hash_api_key(raw_api_key: str) -> str:
    """Hashes a simulated API key using SHA-256 for secure storage."""
    return hashlib.sha256(raw_api_key.strip().encode("utf-8")).hexdigest()


def verify_api_key(raw_api_key: str, stored_hash: str) -> bool:
    """
    Constant-time comparison between hashed raw key and stored hash.
    Prevents timing attack vulnerabilities.
    """
    if not raw_api_key or not stored_hash:
        return False
    computed_hash = hash_api_key(raw_api_key)
    return hmac.compare_digest(computed_hash, stored_hash)


def seed_default_agents_if_empty() -> list:
    """Seeds initial demonstration agents with securely hashed keys if data/agents.json is empty."""
    records = []
    for s in DEFAULT_SEEDS:
        record = {
            "agent_id": s["agent_id"],
            "agent_name": s["agent_name"],
            "agent_type": s["agent_type"],
            "customer_id": s["customer_id"],
            "allowed_actions": s["allowed_actions"],
            "valid_until": s["valid_until"],
            "api_key_hash": hash_api_key(s["raw_key"]),
            "status": s["status"],
            "registration_timestamp": s["registration_timestamp"],
            "revocation_timestamp": s["revocation_timestamp"],
            "revocation_reason": s["revocation_reason"]
        }
        records.append(record)
    save_agents(records)
    return records


def load_agents() -> list:
    """Loads all agent records from data/agents.json, initializing seeds if empty."""
    if not os.path.exists(AGENTS_FILE_PATH):
        return seed_default_agents_if_empty()
    try:
        with open(AGENTS_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not data:
                return seed_default_agents_if_empty()
            return data
    except (json.JSONDecodeError, OSError):
        return seed_default_agents_if_empty()


def save_agents(agents: list) -> None:
    """Persists all agent records to data/agents.json."""
    os.makedirs(os.path.dirname(AGENTS_FILE_PATH), exist_ok=True)
    with open(AGENTS_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(agents, f, indent=2, ensure_ascii=False)


def get_agent_by_id(agent_id: str) -> dict | None:
    """Retrieves an agent record by unique agent_id."""
    agents = load_agents()
    for agent in agents:
        if agent.get("agent_id") == agent_id:
            return agent
    return None


def is_agent_expired(agent_record: dict) -> bool:
    """
    Determines if an agent's authorization has expired.
    Agents remain valid through the end of their expiry date (23:59:59)
    and become expired strictly afterward.
    """
    expiry_str = agent_record.get("valid_until")
    if not expiry_str:
        return False
    
    try:
        if len(expiry_str) == 10:
            expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
            return date.today() > expiry_date
        else:
            expiry_dt = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
            return datetime.now() > expiry_dt
    except ValueError:
        return True


def get_agent_effective_status(agent_record: dict) -> str:
    """
    Calculates the effective runtime status of an agent.
    Revocation ALWAYS takes precedence over expiry.
    """
    if not agent_record:
        return "UNKNOWN"
    
    # Precedence 1: Revocation takes absolute priority
    if agent_record.get("status") == "REVOKED":
        return "REVOKED"
    
    # Precedence 2: Expiry check
    if is_agent_expired(agent_record):
        return "EXPIRED"
        
    return "ACTIVE"


def register_agent(
    agent_name: str,
    agent_type: str,
    customer_id: str,
    allowed_actions: list,
    valid_until: str
) -> tuple[dict, str]:
    """
    Registers a new AI agent, generates simulated API credentials,
    hashes the key for storage, and persists the record.
    
    Returns:
        (new_agent_record, raw_simulated_api_key)
    """
    agents = load_agents()
    
    # Generate unique ID: AGT-ICICI-<NUM>
    new_num = len(agents) + 1
    agent_id = f"AGT-ICICI-{new_num:03d}"
    while any(a.get("agent_id") == agent_id for a in agents):
        new_num += 1
        agent_id = f"AGT-ICICI-{new_num:03d}"
    
    # Generate secure simulated API key (simulated prototype credential)
    raw_api_key = f"icici_sim_{agent_id.lower()}_{secrets.token_hex(12)}"
    key_hash = hash_api_key(raw_api_key)
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    agent_record = {
        "agent_id": agent_id,
        "agent_name": agent_name.strip(),
        "agent_type": agent_type.strip(),
        "customer_id": customer_id.strip(),
        "allowed_actions": allowed_actions,
        "valid_until": valid_until.strip(),
        "api_key_hash": key_hash,
        "status": "ACTIVE",
        "registration_timestamp": now_str,
        "revocation_timestamp": None,
        "revocation_reason": None
    }
    
    agents.append(agent_record)
    save_agents(agents)
    
    return agent_record, raw_api_key


def revoke_agent(agent_id: str, reason: str = "Customer initiated revocation") -> dict | None:
    """
    Revokes an agent's access immediately, recording the exact revocation timestamp.
    Revocation status takes permanent precedence over active or expired states.
    """
    agents = load_agents()
    updated_agent = None
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for agent in agents:
        if agent.get("agent_id") == agent_id:
            agent["status"] = "REVOKED"
            agent["revocation_timestamp"] = now_str
            agent["revocation_reason"] = reason
            updated_agent = agent
            break
            
    if updated_agent:
        save_agents(agents)
        
    return updated_agent


def rotate_api_key(agent_id: str, actor: str = "ADMINISTRATOR") -> tuple[bool, str, str | None, dict | None]:
    """
    Securely rotates the simulated API key for an active agent.
    Generates a cryptographically random new simulated API key,
    computes and stores only its SHA-256 hash in agents.json,
    preserves customer mapping, permissions, valid_until, and ACTIVE status,
    and logs an immutable append-only event to audit_logs.csv.
    
    Returns:
        (success: bool, message: str, raw_new_key: str | None, updated_agent: dict | None)
    """
    from modules import audit_logger
    agents = load_agents()
    target_agent = None
    
    for agent in agents:
        if agent.get("agent_id") == agent_id:
            target_agent = agent
            break
            
    if not target_agent:
        return False, f"Agent '{agent_id}' not found.", None, None
        
    if target_agent.get("status") == "REVOKED":
        return False, f"Cannot rotate API key: Agent '{agent_id}' is REVOKED.", None, None

    # Generate new cryptographically secure simulated API key
    raw_new_key = f"icici_sim_{agent_id.lower()}_{secrets.token_hex(12)}"
    new_hash = hash_api_key(raw_new_key)
    
    # Preserve existing customer mapping, permissions, expiry, and status
    target_agent["api_key_hash"] = new_hash
    target_agent["last_key_rotation"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    save_agents(agents)
    
    # Record rotation event in append-only audit trail
    rot_req_id = f"ROT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    audit_logger.log_event(
        request_id=rot_req_id,
        event_type="API_KEY_ROTATION",
        agent_id=agent_id,
        customer_id=target_agent.get("customer_id", ""),
        action="ROTATE_CREDENTIALS",
        amount=None,
        decision="ROTATED",
        rule_triggered="GOV_ROTATE",
        reason=f"Simulated API credentials successfully rotated for active agent {agent_id}.",
        actor=actor,
        details="New SHA-256 hash stored. Previous key invalidated."
    )
    
    # Update test fixture in test_scenarios if available
    try:
        from modules import test_scenarios
        test_scenarios.TEST_API_KEYS[agent_id] = raw_new_key
    except Exception:
        pass

    return True, f"API key for agent '{agent_id}' rotated successfully.", raw_new_key, target_agent
