from .bank_flows import BankTest
from woke.testing.core import default_chain

from .runner import replay_test


@default_chain.connect()
def test_replay():

    bt = BankTest()

    replay_test(bt, "replay.json")
