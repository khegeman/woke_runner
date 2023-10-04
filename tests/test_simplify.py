from .bank_flows import BankTest
from woke.testing.core import default_chain

from .runner import simplify_test


@default_chain.connect()
def test_replay():

    bt = BankTest()

    simplify_test(bt, "replay.json", 0, "simplified.json")
