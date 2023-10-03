from typing import (
    Callable,
    DefaultDict,
    List,
    Optional,
    Type,
    Dict,
    Iterable,
    get_type_hints,
)

from woke.testing.fuzzing import FuzzTest

from .runner import run, BoundFlow


def unit_test(test: FuzzTest, flow_name: str, params: Dict, properties: List[Callable] = []):

    run(test, bound_flows=[BoundFlow(name=flow_name, params=params, properties=properties)])
