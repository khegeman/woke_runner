from .bank_flows import BankTest,Replay
from woke.testing.core import default_chain
import os

@default_chain.connect()
def test_default():
    """
    Run the BankTest under the default connection.
    """
    print("Replay", Replay)
    bt = BankTest()
    if Replay:
        BankTest.load("replay.json")
    fuzz=os.getenv("WOKE_FUZZ", None)
    if fuzz is not None:
        flows: List[Callable] = bt.get_flows()
        for flow in flows:
            if flow.__name__ != fuzz:
                flow.weight=0
            else:
                flow.weight = 100
        

            
        print("fuzzing only", fuzz)

    bt.run(sequences_count=1, flows_count=10,record=True)
