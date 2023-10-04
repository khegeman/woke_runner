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
from typing_extensions import get_type_hints, get_args, get_origin
from .runner import Flow, BoundFlow, get_methods_dict, run
from dataclasses import fields
import random
from inspect import signature
from woke.testing.fuzzing import FuzzTest
import jsons


def get_param(sequences: Dict, param: str, sequence_num: int, flow_num: int, t: Type):
    params = sequences[str(sequence_num)][str(flow_num)]
    data = params["params"]
    value = data[param]
    if get_origin(t) is list:
        return [get_args(t)[0](v) for v in value]
    if type(value) is dict:
        resolved_hints = get_type_hints(t)
        field_names = [field.name for field in fields(t)]
        resolved_field_types = {name: resolved_hints[name] for name in field_names}
        args = {
            field.name: resolved_field_types[field.name](value[field.name])
            for field in fields(t)
        }

        return t(**args)
    return t(value)


def replay_generator(cls: type, filename: str, sequence_number: int):

    sequence = str(sequence_number)
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

    print("sequences", sequences)
    count = 0
    all_flows: Dict[Callable] = get_methods_dict(cls, "flow")

    # sequence = sequences[sequence]
    flows_count = len(list(sequences.get(sequence, [])))

    for j in range(flows_count):
        print(sequence, j)
        flow_name = sequences.get(sequence).get(str(j)).get("name")
        flow = all_flows.get(flow_name)

        fp = {
            k: get_param(sequences, k, sequence, j, v)
            for k, v in get_type_hints(flow, include_extras=True).items()
            if k != "return"
        }
        print(flow_name, fp)

        yield BoundFlow(name=flow_name, properties=[], params=fp)


def replay_test(test: FuzzTest, filename: str, sequence_number: int = 0):

    run(
        test,
        bound_flows=replay_generator(test, filename, sequence_number),
        properties=[],
    )
