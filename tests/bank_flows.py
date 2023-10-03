from woke.testing.core import default_chain
from woke.development.core import Account
from woke.development.transactions import may_revert, Panic,PanicCodeEnum
from woke.development.primitive_types import uint
from wokelib import collector
from woke.testing.fuzzing import flow, invariant, FuzzTest
from wokelib import get_address, MAX_UINT
from wokelib import Mirror
from wokelib.generators.random import st
from pytypes.contracts.bank import Bank
import os
from dataclasses import dataclass


@dataclass
class BankInput:
    user: Account
    amount: int

class BankTest(FuzzTest):

    def bank_input(self) -> BankInput:
        return BankInput(
            user=st.choose(self.accounts)(),
            amount=st.random_int(0, 50, edge_values_prob=0.05)(),
        )

    bank: Bank

    def pre_sequence(self) -> None:
        """
        Set up the pre-sequence for the fuzz test.
        """
        self._bank = Bank.deploy(from_=default_chain.accounts[0])
  
        self.accounts = list()
        self.accounts.extend(default_chain.accounts[1:5])

    @flow()
    def deposit(self, bank_input: BankInput) -> None:

        balance = self._bank.accounts(bank_input.user)
        overflow = balance + bank_input.amount > MAX_UINT
        try:
            tx = self._bank.deposit(bank_input.amount, from_=bank_input.user)
            assert balance + bank_input.amount == self._bank.accounts(
                bank_input.user
            )
            assert not overflow
        except Panic as e:
            assert e.code == PanicCodeEnum.UNDERFLOW_OVERFLOW
            assert overflow

    @flow()
    def withdraw(self, bank_input: BankInput) -> None:

        balance = self._bank.accounts(bank_input.user)
        underflow = balance < bank_input.amount
        try:
            tx = self._bank.withdraw(bank_input.amount, from_=bank_input.user)
            assert not underflow
            assert balance - bank_input.amount == self._bank.accounts(
                bank_input.user
            )
        except Panic as e:
            assert e.code == PanicCodeEnum.UNDERFLOW_OVERFLOW
            assert underflow