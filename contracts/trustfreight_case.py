# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import genlayer as gl
from genlayer.types import *
import json

class Contract(gl.Contract):
    shipper: str
    carrier: str
    goods_description: str
    contract_terms: str
    value: u256
    route: str
    eta: str
    
    status: str # OPEN, DISPUTED, ESCALATED, RESOLVED
    
    # Evidence
    tracking_url: str
    weather_location: str
    incident_description: str
    evidence_image_url: str
    
    # Dependencies
    escrow_address: str
    registry_address: str
    
    def __init__(self, shipper: str, carrier: str, goods: str, terms: str, value: u256, route: str, eta: str, escrow_addr: str, registry_addr: str):
        self.shipper = shipper
        self.carrier = carrier
        self.goods_description = goods
        self.contract_terms = terms
        self.value = value
        self.route = route
        self.eta = eta
        
        self.escrow_address = escrow_addr
        self.registry_address = registry_addr
        
        self.status = "OPEN"
        self.tracking_url = ""
        self.weather_location = ""
        self.incident_description = ""
        self.evidence_image_url = ""

    @gl.public.write
    def submit_evidence(self, tracking: str, weather_loc: str, incident: str, image: str) -> None:
        sender = str(gl.message.sender_address)
        if sender != self.shipper and sender != self.carrier:
            raise gl.vm.UserError("Only shipper or carrier can submit evidence")
        if self.status != "OPEN":
            raise gl.vm.UserError("Case is not open")
            
        self.tracking_url = tracking
        self.weather_location = weather_loc
        self.incident_description = incident
        self.evidence_image_url = image
        self.status = "DISPUTED"

    @gl.public.write
    def resolve(self) -> None:
        if self.status != "DISPUTED":
            raise gl.vm.UserError(f"Cannot resolve case in status {self.status}")

        def leader_fn() -> dict:
            # 1. Fetch weather from Open-Meteo (requires no key, just coords or geocoding).
            # We assume weather_location is lat,lon for simplicity in this MVP.
            weather_data = "No weather data"
            if self.weather_location:
                try:
                    resp = gl.nondet.web.get(f"https://api.open-meteo.com/v1/forecast?latitude={self.weather_location.split(',')[0]}&longitude={self.weather_location.split(',')[1]}&current_weather=true")
                    weather_data = resp.body
                except Exception as e:
                    weather_data = f"Failed to fetch weather: {e}"
            
            # 2. Fetch tracking info (simulated web page render)
            tracking_data = "No tracking data"
            if self.tracking_url:
                try:
                    # Using web render for tracking to capture page content/JS
                    resp2 = gl.nondet.web.render(self.tracking_url)
                    tracking_data = resp2.body[:2000] # truncate to save context
                except Exception as e:
                    tracking_data = f"Failed to fetch tracking: {e}"
                    
            # 3. If there is an image, we could pass it to exec_prompt. We'll include the URL in the text for now,
            # or if GenLayer SDK supports image objects, we use gl.nondet.Image
            
            prompt = f"""
            You are an expert logistics dispute arbitrator.
            
            --- CASE DETAILS ---
            Goods: {self.goods_description}
            Terms: {self.contract_terms}
            Route: {self.route}
            ETA: {self.eta}
            Incident Description: {self.incident_description}
            
            --- EVIDENCE ---
            Weather Data: {weather_data}
            Tracking Data: {tracking_data}
            Image URL: {self.evidence_image_url}
            
            Evaluate the fault of the Shipper and Carrier based on the terms and evidence.
            Percentages must sum to 100.
            Also provide a confidence score (0-100). If evidence is conflicting, give a low score (<60).
            
            Return JSON in EXACTLY this format:
            {{
                "shipper_fault_percent": <int>,
                "carrier_fault_percent": <int>,
                "confidence": <int>,
                "reason": "<detailed reasoning>"
            }}
            """
            
            try:
                result_str = gl.nondet.exec_prompt(prompt)
                # Cleanup potential markdown JSON wrapping
                clean_str = result_str.strip()
                if clean_str.startswith("```json"):
                    clean_str = clean_str[7:]
                if clean_str.startswith("```"):
                    clean_str = clean_str[3:]
                if clean_str.endswith("```"):
                    clean_str = clean_str[:-3]
                clean_str = clean_str.strip()
                return json.loads(clean_str)
            except Exception as e:
                return {
                    "shipper_fault_percent": 0,
                    "carrier_fault_percent": 0,
                    "confidence": 0,
                    "reason": f"Failed to parse LLM response: {e}"
                }

        def validator_fn(leader_res) -> bool:
            if not isinstance(leader_res, gl.vm.Return):
                return False
            
            leader_dict = leader_res.calldata
            
            if "shipper_fault_percent" not in leader_dict or "confidence" not in leader_dict:
                return False
                
            my_res = leader_fn()
            
            if "shipper_fault_percent" not in my_res or "confidence" not in my_res:
                return False
                
            # If leader says confidence < 60, we just agree on the ESCALATION if we also have confidence < 60
            if leader_dict["confidence"] < 60:
                return my_res["confidence"] < 60
                
            # If confidence >= 60, we agree if shipper_fault_percent is within 10%
            diff = abs(leader_dict["shipper_fault_percent"] - my_res["shipper_fault_percent"])
            return diff <= 10

        # Run non-deterministic consensus block
        resolution = gl.vm.run_nondet(leader_fn, validator_fn)
        
        confidence = resolution.get("confidence", 0)
        
        if confidence < 60:
            self.status = "ESCALATED"
        else:
            shipper_fault = u256(resolution.get("shipper_fault_percent", 0))
            carrier_fault = u256(resolution.get("carrier_fault_percent", 100))
            
            # Normalize to 100
            if shipper_fault + carrier_fault != u256(100):
                carrier_fault = u256(100) - shipper_fault
                
            self.status = "RESOLVED"
            
            # 1. Update Reputation
            registry = gl.get_at(Address(self.registry_address))
            registry.write.update_score(self.shipper, shipper_fault)
            registry.write.update_score(self.carrier, carrier_fault)
            
            # 2. Disburse funds
            # Shipper fault -> Carrier gets money (refund/compensation)
            # Carrier fault -> Shipper gets money
            escrow = gl.get_at(Address(self.escrow_address))
            escrow.write.disburse(
                self.shipper, 
                self.carrier, 
                carrier_fault, # shipper % of funds goes to shipper based on carrier fault
                shipper_fault  # carrier % of funds goes to carrier based on shipper fault
            )

    @gl.public.view
    def get_details(self) -> dict:
        return {
            "shipper": self.shipper,
            "carrier": self.carrier,
            "goods": self.goods_description,
            "terms": self.contract_terms,
            "value": str(self.value),
            "status": self.status,
            "escrow_address": self.escrow_address,
            "registry_address": self.registry_address
        }
