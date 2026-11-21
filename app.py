"""
AGENT GATEKEEPER - ICICI BANK
AI Agent Authorization and Governance System
Academic Project Prototype
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import json
import os
import importlib

# Ensure fresh, non-cached module loading on every live Streamlit execution
import modules.agent_manager
import modules.decision_engine
import modules.approval_manager
import modules.audit_logger
import modules.test_scenarios

importlib.reload(modules.agent_manager)
importlib.reload(modules.decision_engine)
importlib.reload(modules.approval_manager)
importlib.reload(modules.audit_logger)
importlib.reload(modules.test_scenarios)

from modules import agent_manager
from modules import decision_engine
from modules import approval_manager
from modules import audit_logger
from modules import test_scenarios

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION & ICICI BRANDING THEME
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Agent Gatekeeper - ICICI Bank",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for ICICI Bank aesthetic and academic display
st.markdown("""
<style>
    .icici-header {
        background: linear-gradient(90deg, #9b111e 0%, #b8252a 60%, #e65100 100%);
        color: white;
        padding: 24px 30px;
        border-radius: 12px;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
    }
    .icici-header h1 {
        color: #ffffff;
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: 0.5px;
    }
    .icici-header p {
        color: #fce4ec;
        font-size: 1.05rem;
        margin-top: 6px;
        margin-bottom: 0;
    }
    .academic-badge {
        display: inline-block;
        background-color: rgba(255, 255, 255, 0.2);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        margin-top: 8px;
        font-weight: 600;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-left: 5px solid #9b111e;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .verdict-allow {
        background-color: #e8f5e9;
        border: 2px solid #2e7d32;
        color: #1b5e20;
        padding: 15px;
        border-radius: 10px;
        font-weight: bold;
    }
    .verdict-ask {
        background-color: #fff3e0;
        border: 2px solid #ef6c00;
        color: #e65100;
        padding: 15px;
        border-radius: 10px;
        font-weight: bold;
    }
    .verdict-block {
        background-color: #ffebee;
        border: 2px solid #c62828;
        color: #b71c1c;
        padding: 15px;
        border-radius: 10px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SIDEBAR CONFIGURATION & ACADEMIC CREDENTIALS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/shield.png", width=64)
    st.markdown("### 🏦 ICICI Bank Gatekeeper")
    st.markdown("**AI Agent Governance & Authorization Engine**")
    st.markdown("---")
    
    # Enrolment Number Configuration
    if "enrolment_no" not in st.session_state:
        st.session_state.enrolment_no = "ENR-2024-AI-GATEKEEPER"
        
    enrolment_input = st.text_input(
        "🎓 Candidate Enrolment No:",
        value=st.session_state.enrolment_no,
        help="Update with your institutional academic enrolment number for viva evaluation."
    )
    st.session_state.enrolment_no = enrolment_input
    
    st.markdown("---")
    st.markdown("#### 🔒 Security Parameters")
    st.info("⚠️ **Simulated Environment**\nNo real banking APIs or payment rails are accessed. All accounts, keys, and balances are mock entities.")
    
    st.markdown("#### 📜 Core Governance Rules")
    with st.expander("View Rule Priority (R1 → R8)"):
        st.markdown("""
        - **R1**: Schema/Amount Invalid $\\rightarrow$ **BLOCK**
        - **R2**: Unknown/Invalid Agent $\\rightarrow$ **BLOCK**
        - **R3**: Revoked / Expired Agent $\\rightarrow$ **BLOCK**
        - **R4**: Scope / Customer Mismatch $\\rightarrow$ **BLOCK**
        - **R5**: View Balance $\\rightarrow$ **ALLOW**
        - **R6**: Pay Bill $\\le ₹5,000$ $\\rightarrow$ **ALLOW**
        - **R7**: Pay Bill $> ₹5,000$ $\\rightarrow$ **ASK CUSTOMER**
        - **R8**: Fund Transfer $\\rightarrow$ **ASK CUSTOMER**
        """)
        
    st.caption("Agent Gatekeeper v1.0 • Academic Edition")

# -----------------------------------------------------------------------------
# MAIN HEADER BANNER
# -----------------------------------------------------------------------------
st.markdown(f"""
<div class="icici-header">
    <h1>🛡️ AGENT GATEKEEPER – ICICI BANK</h1>
    <p>Zero-Trust AI Agent Authorization, Governance & Human-in-the-Loop Arbitration System</p>
    <div class="academic-badge">🎓 Academic Enrolment No: <strong>{st.session_state.enrolment_no}</strong></div>
    <div class="academic-badge" style="margin-left: 10px; background-color: rgba(0,0,0,0.25);">🔒 Simulated Prototype (Zero Live Access)</div>
</div>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# TAB NAVIGATION
# -----------------------------------------------------------------------------
tabs = st.tabs([
    "📊 Executive Dashboard",
    "⚡ Transaction Gateway",
    "👤 Customer Approval Portal",
    "🤖 Agent Management",
    "🧪 Compulsory Test Suite",
    "📜 Persistent Audit Trail"
])


# =============================================================================
# TAB 1: EXECUTIVE DASHBOARD & METRICS
# =============================================================================
with tabs[0]:
    st.subheader("System Governance Overview & Telemetry")
    
    metrics = audit_logger.get_audit_summary_metrics()
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Agent Requests", metrics["total_evaluations"])
    with c2:
        st.metric("ALLOW Decisions", metrics["allow_count"], delta=f"{metrics['allow_rate']:.1f}%")
    with c3:
        st.metric("ASK CUSTOMER (Escalated)", metrics["ask_customer_count"], delta=f"{metrics['ask_rate']:.1f}%", delta_color="off")
    with c4:
        st.metric("BLOCK Decisions", metrics["block_count"], delta=f"{metrics['block_rate']:.1f}%", delta_color="inverse")
        
    st.markdown("---")
    
    col_left, col_right = st.columns([1, 1])
    
    audit_df = audit_logger.load_audit_trail()
    eval_df = audit_df[audit_df["event_type"] == "TRANSACTION_EVALUATION"] if not audit_df.empty else pd.DataFrame()
    
    with col_left:
        st.markdown("#### 🎯 Decision Distribution")
        if not eval_df.empty and "decision" in eval_df.columns:
            decision_counts = eval_df["decision"].value_counts().reset_index()
            decision_counts.columns = ["Decision", "Count"]
            st.bar_chart(data=decision_counts.set_index("Decision"))
        else:
            st.info("No transaction evaluations logged yet.")
            
    with col_right:
        st.markdown("#### ⚖️ Governance Rules Triggered Frequency")
        if not eval_df.empty and "rule_triggered" in eval_df.columns:
            rule_counts = eval_df["rule_triggered"].value_counts().reset_index()
            rule_counts.columns = ["Rule Triggered", "Frequency"]
            st.bar_chart(data=rule_counts.set_index("Rule Triggered"))
        else:
            st.info("No rule execution data logged yet.")
            
    st.markdown("---")
    st.markdown("#### 📋 Recent Real-Time Evaluations")
    if not eval_df.empty:
        display_cols = ["timestamp", "request_id", "agent_id", "customer_id", "action", "amount", "decision", "rule_triggered", "reason"]
        valid_cols = [c for c in display_cols if c in eval_df.columns]
        st.dataframe(eval_df[valid_cols].tail(8).iloc[::-1], use_container_width=True)
    else:
        st.info("Audit log is currently waiting for incoming agent requests.")


# =============================================================================
# TAB 2: TRANSACTION GATEWAY (SIMULATED EXTERNAL AGENT REQUEST)
# =============================================================================
with tabs[1]:
    st.subheader("Simulate External AI Agent Banking Request")
    st.markdown("Submit a live structured request payload as an external AI bot. The gatekeeper evaluates it against rules **R1 through R8** in strict priority.")
    
    agents = agent_manager.load_agents()
    
    # Load mock customers
    customers_path = os.path.join(os.path.dirname(__file__), "data", "customers.json")
    customers = []
    if os.path.exists(customers_path):
        with open(customers_path, "r", encoding="utf-8") as f:
            customers = json.load(f)
            
    agent_options = {f"{a['agent_id']} - {a['agent_name']} ({agent_manager.get_agent_effective_status(a)})": a for a in agents}
    agent_options["[Test Custom / Unknown Agent]"] = None
    
    c_agent, c_cust = st.columns(2)
    with c_agent:
        selected_agent_label = st.selectbox("Select Calling AI Agent:", list(agent_options.keys()), key="gw_agent_select")
        selected_agent = agent_options[selected_agent_label]
        
    # Autofill defaults for convenience
    default_agent_id = selected_agent["agent_id"] if selected_agent else "AGT-UNKNOWN-999"
    default_api_key = test_scenarios.TEST_API_KEYS.get(default_agent_id, "icici_sim_custom_test_key_xyz") if selected_agent else "invalid_unregistered_key"

    with c_cust:
        default_cust_index = 0
        if selected_agent and "customer_id" in selected_agent:
            for idx, c in enumerate(customers):
                if c["customer_id"] == selected_agent["customer_id"]:
                    default_cust_index = idx
                    break
        cust_options = [c["customer_id"] + " - " + c["name"] for c in customers] + ["CUST-9999 (Rogue Customer)"]
        selected_cust = st.selectbox("Target Customer Account:", cust_options, index=default_cust_index, key=f"gw_cust_{default_agent_id}")
        target_cust_id = selected_cust.split(" ")[0]
        
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        input_agent_id = st.text_input("Agent ID:", value=default_agent_id, key=f"gw_agent_id_{default_agent_id}")
        input_api_key = st.text_input("Simulated API Key (Secret Credential):", value=default_api_key, type="password", key=f"gw_api_key_{default_agent_id}", help="Simulated credential checked against secure SHA-256 hash.")
        
    with col_input2:
        action = st.selectbox("Banking Action:", ["View Balance", "Pay Bill", "Transfer Money", "Apply For Loan (Unsupported)"])
        
        amount_disabled = (action == "View Balance")
        default_amt = 0.0 if amount_disabled else 3500.0
        amount = st.number_input(
            "Transaction Amount (₹):",
            min_value=-10000.0,
            max_value=1000000.0,
            value=default_amt,
            step=500.0,
            disabled=amount_disabled,
            help="Mandatory and strictly > 0 for Pay Bill and Transfer Money. Not required for View Balance."
        )

    submit_btn = st.button("🚀 Ingest & Arbitrate Agent Request", type="primary", use_container_width=True)
    
    if submit_btn:
        payload = {
            "agent_id": input_agent_id,
            "api_key": input_api_key,
            "customer_id": target_cust_id,
            "action": action,
            "amount": None if action == "View Balance" else amount
        }
        
        st.markdown("#### 🔍 Gatekeeper Evaluation Result")
        with st.spinner("Processing zero-trust policy engine..."):
            result = decision_engine.evaluate_transaction(payload)
            
        verdict = result["decision"]
        rule = result["rule_triggered"]
        reason = result["reason"]
        req_id = result["request_id"]
        
        if verdict == "ALLOW":
            st.markdown(f"""
            <div class="verdict-allow">
                <h3>✅ DECISION: ALLOW</h3>
                <p><strong>Request ID:</strong> {req_id} &nbsp;|&nbsp; <strong>Rule Triggered:</strong> {rule}</p>
                <p><strong>Governance Rationale:</strong> {reason}</p>
                <p><strong>Execution Status:</strong> Transaction autonomously executed.</p>
            </div>
            """, unsafe_allow_html=True)
        elif verdict == "ASK CUSTOMER":
            st.markdown(f"""
            <div class="verdict-ask">
                <h3>⚠️ DECISION: ASK CUSTOMER (Human-In-The-Loop Required)</h3>
                <p><strong>Request ID:</strong> {req_id} &nbsp;|&nbsp; <strong>Rule Triggered:</strong> {rule}</p>
                <p><strong>Governance Rationale:</strong> {reason}</p>
                <p><strong>Execution Status:</strong> HELD IN PENDING STATE. Never executed automatically. Please navigate to the <strong>Customer Approval Portal</strong> tab to review.</p>
            </div>
            """, unsafe_allow_html=True)
        else: # BLOCK
            st.markdown(f"""
            <div class="verdict-block">
                <h3>🛑 DECISION: BLOCK</h3>
                <p><strong>Request ID:</strong> {req_id} &nbsp;|&nbsp; <strong>Rule Triggered:</strong> {rule}</p>
                <p><strong>Governance Rationale:</strong> {reason}</p>
                <p><strong>Execution Status:</strong> Request rejected immediately. Event recorded in audit log.</p>
            </div>
            """, unsafe_allow_html=True)
            
        with st.expander("Inspect Raw Evaluation Details (JSON)"):
            st.json(result)


# =============================================================================
# TAB 3: CUSTOMER APPROVAL PORTAL (HUMAN-IN-THE-LOOP)
# =============================================================================
with tabs[2]:
    st.subheader("Customer Approval Portal (Human-in-the-Loop Resolution)")
    st.markdown("""
    **Zero-Trust Human Oversight**: High-risk actions (`Pay Bill > ₹5,000` or `Transfer Money`) are placed in a **`PENDING`** queue.
    - Transactions are **never** executed automatically.
    - Only the **mapped customer** can approve or reject the request.
    - Once resolved, the resolution timestamp is permanently logged and duplicate resolution is rejected.
    """)
    
    # Customer Selector
    active_customer_id = st.selectbox(
        "Simulate Customer Login As:",
        ["CUST-1001", "CUST-1002", "CUST-1003"],
        help="Simulate the customer currently authenticated in ICICI Internet Banking / iMobile app."
    )
    
    pending_items = approval_manager.get_pending_approvals(active_customer_id)
    
    st.markdown(f"#### 📬 Pending Requests for **{active_customer_id}** ({len(pending_items)} awaiting confirmation)")
    
    if not pending_items:
        st.success(f"🎉 No pending transactions awaiting review for Customer {active_customer_id}.")
    else:
        for item in pending_items:
            req_id = item["request_id"]
            with st.container():
                st.markdown(f"""
                <div style="background-color: #ffffff; border: 1px solid #ffcc80; padding: 18px; border-radius: 8px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <h4 style="margin:0 0 8px 0; color: #e65100;">⚠️ Step-Up Confirmation Required: {item['action']} of ₹{item['amount']:,.2f}</h4>
                    <p style="margin: 2px 0;"><strong>Request ID:</strong> <code>{req_id}</code> &nbsp;|&nbsp; <strong>Enqueued:</strong> {item['enqueued_timestamp']}</p>
                    <p style="margin: 2px 0;"><strong>Requesting Agent:</strong> {item['agent_name']} (<code>{item['agent_id']}</code>)</p>
                    <p style="margin: 2px 0;"><strong>Policy Reason:</strong> {item['reason']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col_c1, col_c2, col_c3 = st.columns([2, 1, 1])
                with col_c1:
                    notes = st.text_input("Customer Authorization Notes (Optional):", key=f"notes_{req_id}", placeholder="e.g., Verified utility invoice")
                with col_c2:
                    if st.button("✅ Approve Transaction", key=f"appr_{req_id}", type="primary", use_container_width=True):
                        ok, msg, rec = approval_manager.resolve_approval(req_id, active_customer_id, "APPROVE", comments=notes)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                with col_c3:
                    if st.button("❌ Reject Transaction", key=f"rej_{req_id}", use_container_width=True):
                        ok, msg, rec = approval_manager.resolve_approval(req_id, active_customer_id, "REJECT", comments=notes)
                        if ok:
                            st.warning(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                            
    st.markdown("---")
    st.markdown("#### 📜 Historical Human-in-the-Loop Audit Resolutions")
    all_approvals = approval_manager.get_all_approvals()
    resolved = [a for a in all_approvals if a.get("status") != "PENDING"]
    if resolved:
        resolved_df = pd.DataFrame(resolved)[["request_id", "agent_id", "customer_id", "action", "amount", "status", "resolution", "resolution_timestamp", "comments"]]
        st.dataframe(resolved_df.iloc[::-1], use_container_width=True)
    else:
        st.info("No resolved approvals yet.")


# =============================================================================
# TAB 4: AGENT MANAGEMENT & REGISTRATION
# =============================================================================
with tabs[3]:
    st.subheader("Agent Registration & Lifecycle Governance")
    
    col_reg, col_revoke = st.columns([1, 1])
    
    with col_reg:
        st.markdown("#### 📝 Register New AI Agent")
        with st.form("register_agent_form"):
            new_name = st.text_input("Agent Name:", placeholder="e.g., Autonomous Utility Assistant")
            new_type = st.selectbox("Agent Classification:", ["Personal Financial Bot", "Bill Management Bot", "Tax & Investment Bot", "Shopping & Order Bot"])
            new_cust = st.selectbox("Map to Customer ID:", ["CUST-1001", "CUST-1002", "CUST-1003"])
            new_actions = st.multiselect("Authorized Banking Scopes:", ["View Balance", "Pay Bill", "Transfer Money"], default=["View Balance", "Pay Bill"])
            
            # Expiry date: Default to 1 year ahead
            default_expiry = date.today() + timedelta(days=365)
            new_valid_until = st.date_input("Authorization Expiry Date:", value=default_expiry, min_value=date.today())
            
            reg_submit = st.form_submit_button("🛡️ Register & Generate Simulated Credentials", type="primary")
            
            if reg_submit:
                if not new_name.strip():
                    st.error("Agent name cannot be empty.")
                elif not new_actions:
                    st.error("Agent must be granted at least one authorized banking scope.")
                else:
                    new_agent, raw_key = agent_manager.register_agent(
                        agent_name=new_name,
                        agent_type=new_type,
                        customer_id=new_cust,
                        allowed_actions=new_actions,
                        valid_until=new_valid_until.strftime("%Y-%m-%d")
                    )
                    st.success(f"Agent **{new_agent['agent_id']}** registered successfully!")
                    st.warning(f"🔑 **Simulated API Key (One-Time Display):**\n`{raw_key}`\n\n*Note: For security, only the SHA-256 hash is stored in agents.json. Copy this key now.*")
                    st.rerun()

    with col_revoke:
        st.markdown("#### 🔑 Secure API Key Rotation (Active Agents)")
        st.markdown("Generates a new random simulated API key, stores only its SHA-256 hash, and invalidates the previous credential while preserving all agent permissions and ACTIVE status.")
        
        active_agents_rot = [a for a in agents if a.get("status") != "REVOKED"]
        if active_agents_rot:
            agent_to_rotate = st.selectbox("Select Active Agent to Rotate:", [f"{a['agent_id']} - {a['agent_name']}" for a in active_agents_rot], key="sel_rot_agent")
            rot_id = agent_to_rotate.split(" ")[0]
            
            if st.button("🔄 Rotate Simulated API Key Now", key=f"btn_rot_{rot_id}"):
                ok, msg, new_key, updated_rec = agent_manager.rotate_api_key(rot_id, actor="ADMINISTRATOR")
                if ok:
                    st.session_state["just_rotated_id"] = rot_id
                    st.session_state["just_rotated_key"] = new_key
                    st.rerun()
                else:
                    st.error(msg)
                    
            if st.session_state.get("just_rotated_id"):
                j_id = st.session_state["just_rotated_id"]
                j_key = st.session_state["just_rotated_key"]
                st.success(f"Simulated API credentials for **{j_id}** rotated successfully!")
                st.warning(f"🔑 **New Simulated API Key (One-Time Display):**\n\n`{j_key}`\n\n*Copy this key immediately. For security, only its SHA-256 hash is stored in agents.json and it cannot be retrieved again.*")
                if st.button("✅ I have copied this key safely", key="dismiss_rot_key"):
                    del st.session_state["just_rotated_id"]
                    del st.session_state["just_rotated_key"]
                    st.rerun()
        else:
            st.info("No active agents available for rotation.")

        st.markdown("---")
        st.markdown("#### 🚨 Immediate Agent Revocation (Kill-Switch)")
        st.markdown("Revoking an agent immediately invalidates all future requests. **Revocation takes absolute precedence over active or expired states.**")
        
        active_agents = [a for a in agents if a.get("status") != "REVOKED"]
        if active_agents:
            agent_to_revoke = st.selectbox("Select Agent to Revoke:", [f"{a['agent_id']} - {a['agent_name']}" for a in active_agents], key="sel_revoke_agent")
            revoke_reason = st.text_input("Revocation Reason:", value="Customer initiated revocation due to security concerns", key="input_revoke_reason")
            
            if st.button("⛔ REVOKE AGENT IMMEDIATELY", type="primary", key="btn_revoke_agent"):
                rev_id = agent_to_revoke.split(" ")[0]
                revoked_rec = agent_manager.revoke_agent(rev_id, revoke_reason)
                if revoked_rec:
                    st.error(f"Agent {rev_id} has been permanently REVOKED on {revoked_rec['revocation_timestamp']}.")
                    st.rerun()
        else:
            st.info("No active agents available to revoke.")
            
    st.markdown("---")
    st.markdown("#### 📋 Current Registered Agent Inventory")
    agent_records = agent_manager.load_agents()
    
    agent_display = []
    for a in agent_records:
        effective_st = agent_manager.get_agent_effective_status(a)
        agent_display.append({
            "Agent ID": a["agent_id"],
            "Agent Name": a["agent_name"],
            "Type": a["agent_type"],
            "Mapped Customer": a["customer_id"],
            "Authorized Scopes": ", ".join(a["allowed_actions"]),
            "Valid Until": a["valid_until"],
            "Status": effective_st,
            "Revocation Timestamp": a.get("revocation_timestamp") or "N/A",
            "Revocation Reason": a.get("revocation_reason") or "N/A"
        })
    st.dataframe(pd.DataFrame(agent_display), use_container_width=True)


# =============================================================================
# TAB 5: COMPULSORY ACADEMIC TEST SUITE
# =============================================================================
with tabs[4]:
    st.subheader("Compulsory Academic Test Scenarios (Dynamic Engine Verification)")
    st.markdown("""
    This test suite executes the **live decision engine** against all compulsory academic requirements.
    Results are verified dynamically via runtime assertions comparing expected vs actual verdicts and rules. **Outcomes are NEVER hardcoded.**
    """)
    
    if st.button("▶ Run All Compulsory Test Scenarios Now", type="primary"):
        with st.spinner("Executing live decision engine verification..."):
            test_results = test_scenarios.run_all_test_scenarios()
            hitl_result = test_scenarios.test_customer_approval_workflow()
            
        total_scenarios = len(test_results)
        passed_scenarios = sum(1 for r in test_results if r["passed"])
        
        if passed_scenarios == total_scenarios and hitl_result["all_passed"]:
            st.success(f"🎯 **ALL {total_scenarios} SCENARIOS + HITL LIFECYCLE PASSED!** (100% Academic Compliance)")
        else:
            st.error(f"⚠️ {passed_scenarios}/{total_scenarios} scenarios passed.")
            
        test_rows = []
        for r in test_results:
            test_rows.append({
                "Test ID": r["scenario_id"],
                "Scenario Name": r["name"],
                "Expected Decision": f"{r['expected_decision']} ({r['expected_rule']})",
                "Actual Decision": f"{r['actual_decision']} ({r['actual_rule']})",
                "Rule Explanation": r["rule_reason"],
                "Status": "✅ PASS" if r["passed"] else "❌ FAIL"
            })
            
        st.dataframe(pd.DataFrame(test_rows), use_container_width=True)
        
        st.markdown("#### 👤 Human-in-the-Loop Lifecycle Verification")
        st.json(hitl_result)

        st.markdown("#### 🛡️ Security Vulnerability Regression Suite (SEC-01, SEC-02, SEC-03)")
        sec_results = test_scenarios.run_security_regression_tests()
        sec_rows = []
        for s in sec_results:
            sec_rows.append({
                "Vulnerability": s["vulnerability_id"],
                "Test Description": s["test_name"],
                "Injected Input": s["input"],
                "Expected": s["expected"],
                "Actual": s["actual"],
                "Status": "✅ PASS" if s["passed"] else "❌ FAIL"
            })
        st.dataframe(pd.DataFrame(sec_rows), use_container_width=True)


# =============================================================================
# TAB 6: PERSISTENT AUDIT TRAIL
# =============================================================================
with tabs[5]:
    st.subheader("Immutable, Append-Only Audit Trail")
    st.markdown("""
    **Audit Integrity Guarantee**:
    - `data/audit_logs.csv` is strictly **append-only**.
    - Existing records are **never** modified or overwritten.
    - Customer approval and rejection decisions are logged as **new linked events** referencing the original `request_id`.
    """)
    
    audit_data = audit_logger.load_audit_trail()
    
    if audit_data.empty:
        st.info("No audit events recorded yet.")
    else:
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filter_decision = st.multiselect("Filter Decision:", options=audit_data["decision"].unique(), default=audit_data["decision"].unique())
        with col_f2:
            filter_event = st.multiselect("Filter Event Type:", options=audit_data["event_type"].unique(), default=audit_data["event_type"].unique())
        with col_f3:
            filter_agent = st.selectbox("Filter Agent ID:", options=["ALL"] + list(audit_data["agent_id"].unique()))
            
        filtered_df = audit_data.copy()
        if filter_decision:
            filtered_df = filtered_df[filtered_df["decision"].isin(filter_decision)]
        if filter_event:
            filtered_df = filtered_df[filtered_df["event_type"].isin(filter_event)]
        if filter_agent != "ALL":
            filtered_df = filtered_df[filtered_df["agent_id"] == filter_agent]
            
        st.dataframe(filtered_df.iloc[::-1], use_container_width=True)
        
        csv_data = audit_data.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Persistent Audit Trail (CSV)",
            data=csv_data,
            file_name=f"icici_gatekeeper_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
