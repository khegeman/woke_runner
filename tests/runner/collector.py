"""

Fuzz test data collection classes and decorators
"""
from woke.development.core import Address, Account

from pathlib import Path
from typing import Dict, List
import time
import jsons
from dataclasses import dataclass, asdict, fields
from woke.development.transactions import TransactionAbc
from woke.development.call_trace import CallTrace, CallTraceKind

import traceback


def address_serializer(obj: Address | Account, **kwargs) -> str:
    from . import get_address

    return str(get_address(obj))


jsons.set_serializer(address_serializer, Address)
jsons.set_serializer(address_serializer, Account)


def set_serializer(t: type) -> None:
    jsons.set_serializer(address_serializer, t)


@dataclass
class FlowMetaData:
    name: str
    params: Dict


@dataclass
class TxData:
    tx_hash: str
    block_number: int
    from_: Account
    to: Account
    events: List[str]
    console_logs: List[str]
    error: str
    return_value: str
    tx_index: int
    #  debug_tracecall : Dict
    tx_params: Dict
    call_trace: Dict


@dataclass
class FlowTx:
    name: str
    tx: TxData


@dataclass
class FlowException:
    name: str
    e: str
    args: List
    class_name: str
    traceback: str


def _calltrace_to_dict(call: CallTrace) -> Dict:
    """
    woke has methods to read rich text, but we need a dict to export to json.
    recursive function to extract info from woke CallTrace data structure.
    """

    label = None
    if call.address is not None:
        label = Account(call.address, call.chain).label

    if label is not None:
        contract_name = label
    elif call.contract_name is not None:
        contract_name = call.contract_name
    else:
        contract_name = f"Unknown({call.address})"

    if call.function_name is not None:
        function_name = call.function_name
    else:
        function_name = "???"

    if call.function_is_special:
        pass
    else:
        function_name = call.function_name

    args = []
    if call.kind != CallTraceKind.INTERNAL:
        if call.arguments is not None:
            args = [repr(v) for i, v in enumerate(call.arguments)]

    status = True if call.status else False

    return {
        "contract_name": contract_name,
        "function": function_name,
        "status": status,
        "args": args,
        "kind": str(call.kind),
        "children": [_calltrace_to_dict(subtrace) for subtrace in call._subtraces],
    }


def _extract_tx_data(tx: TransactionAbc) -> TxData:
    if tx._debug_trace_transaction is None:
        tx._fetch_debug_trace_transaction()
    debug_trace = (
        "" if tx._debug_trace_transaction is None else tx._debug_trace_transaction
    )
    return TxData(
        tx_hash=tx.tx_hash,
        console_logs=tx.console_logs,
        block_number=tx.block_number,
        from_=tx.from_,
        to=tx.to,
        events=tx.events,
        error=tx.error,
        return_value=tx.return_value,
        tx_index=tx.tx_index,
        # debug_tracecall = debug_trace,
        call_trace=_calltrace_to_dict(tx.call_trace),
        tx_params=tx._tx_params,
    )


class JsonCollector:
    def __init__(self, testName: str):
        datapath = Path.cwd().resolve() / ".replay"
        datapath.mkdir(parents=True, exist_ok=True)

        self._filename = datapath / f"{testName}-{time.strftime('%Y%m%d-%H%M%S')}.json"

    def __repr__(self):
        return self._values.__repr__()

    @property
    def values(self):
        return self._values

    def tx(self, fuzz, fn, tx: TransactionAbc):
        name = fn.__name__
        save_row = {
            fuzz._sequence_num: {fuzz._flow_num: FlowTx(name, _extract_tx_data(tx))}
        }
        with open(self._filename, "a") as fp:
            j = jsons.dumps(save_row, strip_privates=True, strip_nulls=True)
            print(j, file=fp)

    def exception(self, fuzz, fn, e: Exception):
        name = fn.__name__
        save_row = {
            fuzz._sequence_num: {
                fuzz._flow_num: FlowException(
                    name=name,
                    e=str(e),
                    args=e.args,
                    class_name=e.__class__.__name__,
                    traceback="".join(traceback.format_tb(e.__traceback__)),
                )
            }
        }
        with open(self._filename, "a") as fp:
            j = jsons.dumps(save_row, strip_privates=True, strip_nulls=True)
            print(j, file=fp)

    def collect(self, fuzz, fn, **kwargs):

        save_row = {
            fuzz._sequence_num: {fuzz._flow_num: FlowMetaData(fn.__name__, kwargs)}
        }
        with open(self._filename, "a") as fp:
            j = jsons.dumps(save_row, strip_privates=True, strip_nulls=True)
            print(j, file=fp)
