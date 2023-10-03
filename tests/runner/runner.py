"""

Generic Sequence Runner , replacement for woke FuzzTest.run 

This runner extends functionality beyond fuzz testing.  
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, DefaultDict, List, Optional, Type, Dict, get_type_hints

from typing_extensions import get_type_hints, get_args, get_origin
from dataclasses import fields, dataclass

from woke.testing.core import get_connected_chains
from woke.testing import fuzzing

import copy


def get_methods_dict(test: fuzzing.FuzzTest, attr: str) -> Dict[Callable]:
    ret = {}
    for x in dir(test):
        if hasattr(test.__class__, x):
            m = getattr(test.__class__, x)
            if hasattr(m, attr) and getattr(m, attr):
                ret[x] = m
    return ret


def get_methods(test: fuzzing.FuzzTest, attr: str) -> List[Callable]:
    ret = []
    for x in dir(test):
        if hasattr(test.__class__, x):
            m = getattr(test.__class__, x)
            if hasattr(m, attr) and getattr(m, attr):
                ret.append(m)
    return ret

from typing import TypeVar, NewType, List

T = TypeVar('T', bound='FuzzTest')
PropertyTest = NewType('PropertyTest', Callable[[T], bool])

@dataclass
class Flow:
    """
    Represents a flow with its name and associated property tests.

    Attributes:
    -----------
    name : str
        The name or identifier of the flow.

    properties : List[PropertyTest]
        A list of property tests, each intended to validate a specific property
        or invariant associated with the flow.
    """
    name: str
    properties: List[PropertyTest]

@dataclass
class BoundFlow(Flow):
    """
    A specialized flow that binds specific parameters values to a method.

    Attributes:
    -----------
    params : Dict
        A dictionary of parameter names to their bound values which will be
        passed to the method when called.
    """
    params: Dict

from typing import Iterable


def run(
    test: fuzzing.FuzzTest,
    bound_flows: Iterable[BoundFlow],
    properties: List[PropertyTest] = [],
):

    """
    Execute the test flows with bound parameters and validate using property tests.

    This method runs through the provided `bound_flows`, executing each flow
    with the specified parameters and then validating the results by running
    the property tests associated with each flow. Additionally, global
    property tests provided in the `properties` parameter are run after all
    flows are executed. Invariants are also checked at defined periods.

    This is a replacement for the run method on the woke class FuzzTest.

    Parameters:
    -----------
    test : fuzzing.FuzzTest
        The fuzz test instance on which flows and invariants are to be executed.

    bound_flows : Iterable[BoundFlow]
        An iterable of flows with their bound parameters. Each flow will be executed
        and then its associated property tests will be run.

    properties : List[Callable], optional
        A list of global property tests that are executed after all flows are run.
        These are used to validate global properties or invariants that are not
        specific to any individual flow.

    Notes:
    ------
    The method maintains counters for flows and invariants to keep track of
    their execution frequencies. It also handles the pre and post sequence, flow,
    and invariant logic by invoking the respective methods on the `test` instance.
    """

    chains = get_connected_chains()
    flows: Dict[Callable] = get_methods_dict(test, "flow")
    invariants: List[Callable] = get_methods(test, "invariant")

    flows_counter: DefaultDict[Callable, int] = defaultdict(int)
    invariant_periods: DefaultDict[Callable[[None], None], int] = defaultdict(int)

    snapshots = [chain.snapshot() for chain in chains]
    test._flow_num = 0
    test.pre_sequence()

    for j, uflow in enumerate(bound_flows):
        flow_name = uflow.name
        flow = flows.get(flow_name)

        fp = uflow.params

        test._flow_num = j
        test.pre_flow(flow)
        flow(test, **fp)
        flows_counter[flow] += 1
        test.post_flow(flow)
        for p in uflow.properties:
            p(test)

        test.pre_invariants()
        for inv in invariants:
            if invariant_periods[inv] == 0:
                test.pre_invariant(inv)
                inv(test)
                test.post_invariant(inv)

            invariant_periods[inv] += 1
            if invariant_periods[inv] == getattr(inv, "period"):
                invariant_periods[inv] = 0
        test.post_invariants()

    for p in properties:
        p(test)

    test.post_sequence()

    for snapshot, chain in zip(snapshots, chains):
        chain.revert(snapshot)
