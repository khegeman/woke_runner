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
import random
from inspect import signature
from woke.testing.fuzzing import FuzzTest


def fuzz_generator(cls: type, flows: Iterable[Flow]):
    """generate a sequence of flows with parameters bound with randomized values - in a given order"""
    count = 0
    all_flows: Dict[Callable] = get_methods_dict(cls, "flow")

    for flow in flows:
        flow_fn = all_flows.get(flow.name)
        fp = {}
        for k, v in get_type_hints(flow_fn, include_extras=True).items():
            if k != "return":
                #look for a callable method either global or on the FuzzTest instance
                method = getattr(type(cls), k, None)
                if callable(method):
                    params_len = len(signature(method).parameters)
                    if params_len == 0:
                        fp[k] = method()
                    elif params_len == 1:
                        fp[k] = method(cls)
                    else:
                        raise ValueError(
                            f"Method {k} has an unsupported number of parameters.  Must take either no parameters or 1 parameter that is self"
                        )
                else:
                    #default woke behavior
                    fp[k] = generate(v)

        yield BoundFlow(name=flow.name, properties=flow.properties, params=fp)


def stateful_generator(cls: type, flow_count: int):

    all_flows: Dict[Callable] = get_methods_dict(cls, "flow")
    flow_names = list(all_flows.keys())

    flows = [
        Flow(name=random.choice(flow_names), properties=[])
        for i in range(0, flow_count)
    ]

    return fuzz_generator(cls, flows)


def fuzz_test(
    test: FuzzTest,
    sequences_count: int = 1,
    flow_name: Union[str, Iterable[str]] = "",
    flows: Iterable[Flow] = None,
):
    if flows is None:
        flows = (
            [Flow(name=flow_name, properties=[])]
            if type(flow_name) is str
            else [Flow(name=name, properties=[]) for name in flow_name]
        )
    for i in range(0, sequences_count):
        test._sequence_num = i
        run(test, bound_flows=fuzz_generator(test, flows=flows), properties=[])


def stateful_test(test: FuzzTest, sequences_count: int, flow_count: int):
    for i in range(0, sequences_count):
        test._sequence_num = i
        run(
            test,
            bound_flows=stateful_generator(test, flow_count=flow_count),
            properties=[],
        )
