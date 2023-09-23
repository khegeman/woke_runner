from woke.testing.core import default_chain
from woke.development.core import Account
from woke.development.transactions import may_revert
from woke.development.primitive_types import uint
from wokelib import collector
from woke.testing.fuzzing import flow, invariant
from wokelib import get_address, MAX_UINT
from wokelib import Mirror
from wokelib.generators.random import st
from pytypes.contracts.bank import Bank
import os
from dataclasses import dataclass 

# Determine if we are replaying a test
try:
    Replay = True if int(os.getenv("WOKE_REPLAY", 0)) > 0 else False
except:
    Replay = False

Unit = True if int(os.getenv("WOKE_UNIT", 0)) > 0 else False

Forge = True if int(os.getenv("WOKE_FORGE", 0)) > 0 else False


# Load appropriate modules based on replay status
if Replay:
    from wokelib.generators.replay import fuzz_test
elif Unit:
    from .unit_runner import fuzz_test
elif Forge:
    from .forge_runner import fuzz_test    
else:
    from wokelib.generators.random import fuzz_test

print("BF", Replay)
@dataclass 
class BankInput:
    user : Account
    amount : int

class BankTest(fuzz_test.FuzzTest):
    """
    A fuzz test for the Bank contract.

    Attributes:
        account: A randomly chosen account.
        amount: A random integer amount.
    """
    def random_input(self) -> BankInput:
        return BankInput(
            user = st.choose(self.accounts)() ,
            amount = st.random_int(0,50,edge_values_prob=0.05)()
        )

    
    bank : Bank
    amount = st.random_int(max=50)

    def pre_sequence(self) -> None:
        """
        Set up the pre-sequence for the fuzz test.
        """
        self._bank = Bank.deploy(from_=default_chain.accounts[0])
        self.bank = self._bank

        # Create a mirror to track account balances
        self.bankMirror = Mirror[Account]()        
        self.bankMirror.bind(self._bank.accounts)

        self.accounts = list()                
        self.accounts.extend(default_chain.accounts[1:5])
        for account in self.accounts:
            self.bankMirror[account] = 0



    @flow()
    def deposit(self, random_input : BankInput) -> None:
        """
        Simulate a deposit flow.

        Args:
            account: The account to deposit to.
            amount: The amount to deposit.
        """
        print("deposit", random_input.amount)
        balance = self._bank.accounts(random_input.user)
        overflow = balance + random_input.amount > MAX_UINT
        with may_revert() as e:
            tx = self._bank.deposit(random_input.amount, from_=random_input.user)
            assert balance + random_input.amount == self._bank.accounts(random_input.user)
            assert tx.events[0] == Bank.Deposit(get_address(random_input.user), random_input.amount)
            assert not overflow
            self.bankMirror[random_input.user] += random_input.amount
        if e.value is not None:
            assert overflow

    @flow()
    def withdraw(self, random_input : BankInput) -> None:
        """
        Simulate a withdraw flow.

        Args:
            account: The account to withdraw from.
            amount: The amount to withdraw.
        """
        print("withdraw", random_input.amount)        
        balance = self._bank.accounts(random_input.user)
        underflow = balance < random_input.amount
        with may_revert() as e:
            tx = self._bank.withdraw(random_input.amount, from_=random_input.user)
            assert not underflow
            assert balance - random_input.amount == self._bank.accounts(random_input.user)
            assert tx.events[0] == Bank.Withdraw(get_address(random_input.user), random_input.amount)
            self.bankMirror[random_input.user] -= random_input.amount
        if e.value is not None:
            assert underflow

    @invariant()
    def balances_match(self) -> None:
        """
        Check if balances in the mirror match the bank contract.
        """
        self.bankMirror.assert_equals_remote()

