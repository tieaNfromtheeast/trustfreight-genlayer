# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import genlayer as gl
from genlayer.types import *

class Contract(gl.Contract):
    # Mapping of case contract address (str) to escrowed amount (u256)
    deposits: gl.storage.TreeMap[str, u256]
    # Mapping of case contract address to a boolean indicating if it's an authorized case
    authorized_cases: gl.storage.TreeMap[str, bool]
    
    def __init__(self):
        pass

    @gl.public.write
    def authorize_case(self, case_address: str) -> None:
        # Only the creator of the escrow treasury or some admin should ideally do this,
        # but for simplicity in this MVP, we allow any case to be authorized.
        self.authorized_cases[case_address] = True

    @gl.public.write
    def deposit(self, case_address: str) -> None:
        if not self.authorized_cases.get(case_address, False):
            raise gl.vm.UserError("Case not authorized")
        
        # gl.message.value is the amount of GEN sent with the transaction
        amount = u256(gl.message.value)
        if amount == u256(0):
            raise gl.vm.UserError("Deposit amount must be > 0")
            
        current = self.deposits.get(case_address, u256(0))
        self.deposits[case_address] = current + amount

    @gl.public.write
    def disburse(self, shipper_address: str, carrier_address: str, shipper_percent: u256, carrier_percent: u256) -> None:
        # Only the authorized case contract itself can call this
        case_address = str(gl.message.sender_address)
        if not self.authorized_cases.get(case_address, False):
            raise gl.vm.UserError("Caller is not an authorized case")
            
        amount = self.deposits.get(case_address, u256(0))
        if amount == u256(0):
            raise gl.vm.UserError("No funds to disburse")
            
        if shipper_percent + carrier_percent != u256(100):
            raise gl.vm.UserError("Percentages must sum to 100")
            
        shipper_share = (amount * shipper_percent) // u256(100)
        carrier_share = (amount * carrier_percent) // u256(100)
        
        # In case of rounding errors, the remainder goes to carrier
        carrier_share += (amount - shipper_share - carrier_share)

        self.deposits[case_address] = u256(0)
        self.authorized_cases[case_address] = False # Prevent double disbursement
        
        if shipper_share > u256(0):
            self.emit_transfer(Address(shipper_address), shipper_share)
        if carrier_share > u256(0):
            self.emit_transfer(Address(carrier_address), carrier_share)

    @gl.public.view
    def get_deposit(self, case_address: str) -> u256:
        return self.deposits.get(case_address, u256(0))
