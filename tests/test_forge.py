from .bank_flows import BankTest,BankInput
from woke.testing.core import default_chain
from woke.development.core import Account

from .forge_runner.fuzz_test import ForgeFlow


@default_chain.connect()
def test_deposit():

    bt = BankTest()
    flows = [
        ForgeFlow(name="deposit", properties=[])
    ]
    
    bt.run(sequences_count=10,unit_flows=flows, properties=[])



@default_chain.connect()
def test_withdraw():

    bt = BankTest()
    flows = [
        ForgeFlow(name="deposit", properties=[]),
        ForgeFlow(name="deposit", properties=[]),        
        ForgeFlow(name="withdraw", properties=[])                
    ]
    
    bt.run(sequences_count=10,unit_flows=flows,properties=[])


