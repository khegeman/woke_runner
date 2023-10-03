from .bank_flows import BankTest
from woke.testing.core import default_chain

from .runner import stateful_test


@default_chain.connect()
def test_fuzz():

    bt = BankTest()

    stateful_test(bt, sequences_count=10, flow_count=5)
