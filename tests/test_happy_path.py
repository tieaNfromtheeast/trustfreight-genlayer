import json
import pytest

def test_happy_path_resolution(direct_vm, direct_deploy, direct_alice, direct_bob):
    # Deploy contracts
    registry = direct_deploy("contracts/reputation_registry.py")
    escrow = direct_deploy("contracts/escrow_treasury.py")
    
    # direct_alice is shipper, direct_bob is carrier
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
    
    # Authorize case on escrow
    escrow.authorize_case(case.address)
    
    # Bob deposits escrow
    direct_vm.sender = direct_bob
    direct_vm.value = 10000
    escrow.deposit(case.address)
    assert escrow.get_deposit(case.address) == 10000
    
    # Submit evidence (Bob)
    direct_vm.value = 0
    case.submit_evidence("https://track.com/123", "22.5,114.0", "Water damage", "https://img.com/123")
    assert case.get_details()["status"] == "DISPUTED"
    
    # Mock LLM & Web
    direct_vm.mock_web(r".*open-meteo\.com.*", {"status": 200, "body": '{"temperature": 25}'})
    direct_vm.mock_web(r".*track\.com.*", {"status": 200, "body": "Delivered with water damage"})
    
    # Mock LLM to return JSON indicating carrier fault
    # We must format it correctly
    mock_llm_response = json.dumps({
        "shipper_fault_percent": 0,
        "carrier_fault_percent": 100,
        "confidence": 90,
        "reason": "Carrier failed to protect goods from water"
    })
    direct_vm.mock_llm(r".*", mock_llm_response)
    
    # Resolve
    case.resolve()
    
    # Assert status and disbursements
    assert case.get_details()["status"] == "RESOLVED"
    assert escrow.get_deposit(case.address) == 0
    
    # In happy path (carrier fault = 100%), Shipper gets 100% of escrow
    # Escrow logic: shipper_share = (amount * shipper_percent) / 100
    # Wait, the resolve function passes carrier_fault to shipper_share and shipper_fault to carrier_share
    # Because shipper gets paid out of carrier's fault
    
    # Check reputation
    # Carrier gets 100 fault, score penalty = 50. Base is 100 -> 50.
    # Shipper gets 0 fault, reward = 50. Base is 100 -> 150.
    assert registry.get_score(direct_alice) == 150
    assert registry.get_score(direct_bob) == 50
