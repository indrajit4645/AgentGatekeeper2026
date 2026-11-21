"""
Backend Verification Script
Directly tests the decision engine, approval manager, and audit logger.
"""

from modules import test_scenarios, approval_manager, audit_logger, agent_manager

def main():
    print("=" * 60)
    print("AGENT GATEKEEPER - ICICI BANK: BACKEND MODULE VERIFICATION")
    print("=" * 60)
    
    # 1. Test Agent Manager
    agents = agent_manager.load_agents()
    print(f"[*] Agent Manager: Loaded {len(agents)} registered agents.")
    for a in agents:
        status = agent_manager.get_agent_effective_status(a)
        print(f"    - {a['agent_id']}: {a['agent_name']} | Effective Status: {status} | Expiry: {a['valid_until']}")

    # 2. Test Automated Decision Engine Scenarios
    print("\n[*] Executing Compulsory Test Scenarios (Dynamic Engine Assertions):")
    results = test_scenarios.run_all_test_scenarios()
    for r in results:
        status_sym = "[PASS]" if r["passed"] else "[FAIL]"
        print(f"    {status_sym} {r['scenario_id']} | {r['name']:<40} | Exp: {r['expected_decision']} ({r['expected_rule']}) -> Got: {r['actual_decision']} ({r['actual_rule']})")
        
    all_passed = all(r["passed"] for r in results)
    print(f"\n[*] Total Scenarios: {len(results)} | All Passed: {all_passed}")
    assert all_passed, "Not all test scenarios passed!"

    # 3. Test Security Regression Suite (SEC-01, SEC-02, SEC-03)
    print("\n[*] Executing Dedicated Security Regression Suite (SEC-01, SEC-02, SEC-03):")
    sec_results = test_scenarios.run_security_regression_tests()
    for s in sec_results:
        s_sym = "[PASS]" if s["passed"] else "[FAIL]"
        print(f"    {s_sym} {s['vulnerability_id']:<11} | {s['test_name']:<45} | Exp: {s['expected']} -> Got: {s['actual']}")
    all_sec_passed = all(s["passed"] for s in sec_results)
    print(f"\n[*] Total Security Regression Tests: {len(sec_results)} | All Passed: {all_sec_passed}")
    assert all_sec_passed, "Security regression test failed!"

    # 4. Test Human-in-the-Loop Approval Lifecycle
    print("\n[*] Executing Human-In-The-Loop Lifecycle Test:")
    hitl_res = test_scenarios.test_customer_approval_workflow()
    print(f"    - Enqueued in PENDING queue: {hitl_res['enqueued_properly']}")
    print(f"    - Unauthorized customer prevented: {hitl_res['unauthorized_resolution_prevented']}")
    print(f"    - Authorized customer approval successful: {hitl_res['authorized_approval_successful']}")
    print(f"    - Duplicate resolution prevented: {hitl_res['duplicate_resolution_prevented']}")
    print(f"    - Resolution Timestamp: {hitl_res['resolution_timestamp']}")
    print(f"    - Lifecycle Test Passed: {hitl_res['all_passed']}")
    assert hitl_res["all_passed"], "HITL approval lifecycle test failed!"

    # 5. Test Audit Trail Integrity
    print("\n[*] Testing Audit Trail Integrity (Append-Only):")
    df = audit_logger.load_audit_trail()
    print(f"    - Audit Log Rows: {len(df)}")
    print(f"    - Columns: {list(df.columns)}")
    metrics = audit_logger.get_audit_summary_metrics()
    print(f"    - Metrics: Total Evaluations: {metrics['total_evaluations']}, Allow: {metrics['allow_count']}, Block: {metrics['block_count']}, Ask: {metrics['ask_customer_count']}")
    print(f"    - Customer Approvals Recorded: {metrics['customer_approved']}")

    print("\n" + "=" * 60)
    print("ALL MODULE VERIFICATIONS COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()
