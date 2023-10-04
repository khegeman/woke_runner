from typing import (
    Callable,
    DefaultDict,
    List,
    Optional,
    Type,
    Dict,
    Iterable,
    get_type_hints,
    Union,
)

from .runner import Flow, BoundFlow, get_methods_dict, run
from .replay import get_param
import jsons
from inspect import signature
from woke.testing.fuzzing import FuzzTest


def simplify_generator(
    cls: type, sequences: Dict, sequence_number: int, flow_numbers: List[int]
):

    sequence = str(sequence_number)

    all_flows: Dict[Callable] = get_methods_dict(cls, "flow")

    for j in flow_numbers:
        flow_name = sequences.get(sequence).get(str(j)).get("name")
        flow = all_flows.get(flow_name)

        fp = {
            k: get_param(sequences, k, sequence, j, v)
            for k, v in get_type_hints(flow, include_extras=True).items()
            if k != "return"
        }
        print("flow", flow_name, fp)

        yield BoundFlow(name=flow_name, properties=[], params=fp)


def simplify_test(
    test: FuzzTest, filename: str, sequence_number: int, output_filename: str
):

    sequences = {}
    # load json lines recorded file to a dict for now
    with open(filename, "r") as f:
        for line in f.readlines():
            try:
                flow = jsons.loads(line)
                seqnum = list(flow)[0]
                s = sequences.get(seqnum, {})
                s.update(flow[seqnum])
                sequences[seqnum] = s
            except Exception as e:
                print(line, e)

    # first pass , we run all flows and record the exception
    baseline = None

    flows_count = len(list(sequences.get(str(sequence_number))))
    try:
        run(
            test,
            bound_flows=simplify_generator(
                test,
                sequences,
                sequence_number,
                flow_numbers=list(range(0, flows_count)),
            ),
            properties=[],
        )
    except Exception as e:
        baseline = e

    if baseline is not None:
        removed = []
        for r in range(flows_count - 1, -1, -1):

            flow_numbers = [
                j for j in range(0, flows_count) if (j != r) and (j not in removed)
            ]

            try:
                run(
                    test,
                    bound_flows=simplify_generator(
                        test, sequences, sequence_number, flow_numbers=flow_numbers
                    ),
                    properties=[],
                )
            except Exception as e:
                print("exception ", e, test._flow_num, " r ", r)
                if test._flow_num == len(flow_numbers) - 1:
                    if type(e) is type(baseline) and e.args == baseline.args:
                        removed.append(r)

        next = 0
        with open(output_filename, "w") as fp:
            for r in range(flows_count):
                if r not in removed:
                    save_row = {0: {next: sequences[str(sequence_number)][str(r)]}}
                    jr = jsons.dumps(save_row, strip_privates=True, strip_nulls=True)
                    print(jr, file=fp)
                    next = next + 1
