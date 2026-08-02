import json
import pytest

def setup_contracts(direct_vm, direct_deploy, direct_alice, direct_bob):
    registry = direct_deploy("contracts/reputation_registry.py")
    escrow = direct_deploy("contracts/escrow_treasury.py")
    
    case = direct_deploy(
        "contracts/trustfreight_case.py", 
        direct_alice, 
        direct_bob, 
        "Electronics", 
        "FOB Shenzhen", 
        10000, 
        "Shenzhen -> LA", 
        "2023-12-01", 
        escrow.address, 
        registry.address
    )
    
    escrow.authorize_case(case.address)
    
    direct_vm.sender = direct_bob
    direct_vm.value = 10000
    escrow.deposit(case.address)
    
    direct_vm.value = 0
    direct_vm.sender = direct_alice
    case.submit_evidence("https://track.com/123", "22.5,114.0", "Water damage", "https://img.com/123")
    
    return registry, escrow, case

def test_escalation_on_low_confidence(direct_vm, direct_deploy, direct_alice, direct_bob):
    registry, escrow, case = setup_contracts(direct_vm, direct_deploy, direct_alice, direct_bob)
    
    direct_vm.mock_web(r".*open-meteo\.com.*", {"status": 200, "body": '{"temperature": 25}'})
    direct_vm.mock_web(r".*track\.com.*", {"status": 200, "body": "Delivered with water damage"})
    
    # Mock LLM to return low confidence
    mock_llm_response = json.dumps({
        "shipper_fault_percent": 50,
        "carrier_fault_percent": 50,
        "confidence": 40,
        "reason": "Evidence is highly conflicting, cannot determine fault clearly."
    })
    direct_vm.mock_llm(r".*", mock_llm_response)
    
    case.resolve()
    
    assert case.get_details()["status"] == "ESCALATED"
    # Escrow should not be disbursed
    assert escrow.get_deposit(case.address) == 10000

def test_bad_json_parsing(direct_vm, direct_deploy, direct_alice, direct_bob):
    registry, escrow, case = setup_contracts(direct_vm, direct_deploy, direct_alice, direct_bob)
    
    direct_vm.mock_web(r".*", {"status": 200, "body": "Ok"})
    
    # Mock LLM returns bad JSON
    direct_vm.mock_llm(r".*", "I am an AI and I think shipper is at fault.")
    
    case.resolve()
    
    # Our fallback logic in contract returns confidence 0 for bad parsing, which triggers ESCALATED
    assert case.get_details()["status"] == "ESCALATED"

def test_web_timeout(direct_vm, direct_deploy, direct_alice, direct_bob):
    registry, escrow, case = setup_contracts(direct_vm, direct_deploy, direct_alice, direct_bob)
    
    # Direct mode web mocks will return whatever we tell it to.
    # To simulate failure, we return 404 or just use empty body that LLM will see as "Failed"
    direct_vm.mock_web(r".*", {"status": 404, "body": "Not Found"})
    
    mock_llm_response = json.dumps({
        "shipper_fault_percent": 100,
        "carrier_fault_percent": 0,
        "confidence": 80,
        "reason": "Without tracking info, Shipper bears burden of proof per terms."
    })
    direct_vm.mock_llm(r".*", mock_llm_response)
    
    case.resolve()
    
    assert case.get_details()["status"] == "RESOLVED"
    assert escrow.get_deposit(case.address) == 0
    # Shipper fault = 100, carrier gets all
    assert registry.get_score(direct_alice) == 50
    assert registry.get_score(direct_bob) == 150
