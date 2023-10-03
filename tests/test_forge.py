from .bank_flows import BankTest, BankInput
from woke.testing.core import default_chain
from woke.development.core import Account

from .runner import fuzz_test, fuzz_generator, Flow


@default_chain.connect()
def test_deposit():

    bt = BankTest()

    fuzz_test(bt, sequences_count=10, flow_name="deposit")


@default_chain.connect()
def test_withdraw():

    bt = BankTest()

    fuzz_test(bt, sequences_count=10, flow_name=["deposit", "withdraw"])
