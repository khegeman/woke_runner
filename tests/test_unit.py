from .bank_flows import BankTest, BankInput
from woke.testing.core import default_chain
from woke.development.core import Account
from wokelib import get_address

user_addr = "0x15d34aaf54267db7d7c367839aaf71a00a2c6a65"

from .runner import run, BoundFlow, unit_test


def check_balance(bt: BankTest, amount: int):
    def f(bt: BankTest):
        print(default_chain.accounts[1])
        assert bt._bank.accounts(get_address(user_addr)) == amount

    return f


@default_chain.connect()
def test_deposit():
    bt = BankTest()
    unit_test(
        bt,
        flow_name="deposit",
        params={"bank_input": BankInput(user=Account(user_addr), amount=2)},
    )


@default_chain.connect()
def test_withdraw():

    bt = BankTest()
    flows = [
        BoundFlow(
            name="deposit",
            params={"bank_input": BankInput(user=Account(user_addr), amount=2)},
            properties=[check_balance(bt, 2)],
        ),
        BoundFlow(
            name="withdraw",
            params={"bank_input": BankInput(user=Account(user_addr), amount=2)},
            properties=[check_balance(bt, 0)],
        ),
    ]

    run(bt, bound_flows=flows, properties=[])


@default_chain.connect()
def test_withdraw_fail():

    bt = BankTest()
    flows = [
        BoundFlow(
            name="deposit",
            params={"bank_input": BankInput(user=Account(user_addr), amount=2)},
            properties=[check_balance(bt, 2)],
        ),
        BoundFlow(
            name="withdraw",
            params={"bank_input": BankInput(user=Account(user_addr), amount=4)},
            properties=[check_balance(bt, 2)],
        ),
    ]

    run(bt, bound_flows=flows, properties=[])
