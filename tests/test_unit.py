from .bank_flows import BankTest,BankInput
from woke.testing.core import default_chain
from woke.development.core import Account
from wokelib import get_address
    
user_addr = "0x15d34aaf54267db7d7c367839aaf71a00a2c6a65"

from .unit_runner.fuzz_test import UnitFlow
def check_balance(bt : BankTest, amount : int):
    def f(bt: BankTest):
        print(default_chain.accounts[1])
        assert bt.bank.accounts(get_address(user_addr)) == amount
    return f




@default_chain.connect()
def test_deposit():

    bt = BankTest()
    flows = [
        UnitFlow(name="deposit", params = {"random_input" : BankInput(user=Account(user_addr), amount=2)}, properties=[check_balance(bt,2)])
    ]
    
    bt.run(unit_flows=flows, properties=[check_balance(bt,2)])



@default_chain.connect()
def test_withdraw():

    bt = BankTest()
    flows = [
        UnitFlow(name="deposit", params = {"random_input" : BankInput(user=Account(user_addr), amount=2)}, properties=[check_balance(bt,2)]),
        UnitFlow(name="withdraw", params = {"random_input" : BankInput(user=Account(user_addr), amount=2)}, properties=[check_balance(bt,0)])                
    ]
    
    bt.run(unit_flows=flows,properties=[])



@default_chain.connect()
def test_withdraw_fail():

    bt = BankTest()
    flows = [
        UnitFlow(name="deposit", params = {"random_input" : BankInput(user=Account(user_addr), amount=2)}, properties=[check_balance(bt,2)]),        
        UnitFlow(name="withdraw", params = {"random_input" : BankInput(user=Account(user_addr), amount=4)}, properties=[check_balance(bt,2)])                
    ]
    
    bt.run(unit_flows=flows,properties=[])

