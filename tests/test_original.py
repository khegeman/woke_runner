from woke.testing.core import default_chain
from woke.development.core import Account
from wokelib import get_address
from pytypes.contracts.bank import Bank


@default_chain.connect()
def test_deposit():
    user_addr = "0x15d34aaf54267db7d7c367839aaf71a00a2c6a65"
    # setup
    bank = Bank.deploy(from_=default_chain.accounts[0])
    bank.deposit(amount=2, from_=Account(user_addr))

    assert bank.accounts(user_addr) == 2
