"""

Quick test of a different method for generating random data.  Could be integrated into woke proper

"""

from __future__ import annotations
from inspect import signature
import random
from collections import defaultdict
from typing import Callable, DefaultDict, List, Optional
from dataclasses import dataclass
from typing_extensions import get_type_hints
from woke.testing.fuzzing.generators import generate


from woke.testing.core import get_connected_chains
from woke.testing import fuzzing

from wokelib import JsonCollector

@dataclass 
class ForgeFlow:
    name : str 
    properties : List

class FuzzTest(fuzzing.FuzzTest):
    def get_flows(self):
        fflows: List[Callable] = self.__get_methods("flow")
        return fflows
    
    def __get_methods_dict(self, attr: str) -> Dict[Callable]:
        ret = {}
        for x in dir(self):
            if hasattr(self.__class__, x):
                m = getattr(self.__class__, x)
                if hasattr(m, attr) and getattr(m, attr):
                    ret[x] = m
        return ret
        
    def run(
        self,
        sequences_count: int,
        *,
        dry_run: bool = False,
        record: bool = True,
        unit_flows: List[UnitFlow],
        properties : List        
    ):
        chains = get_connected_chains()
        flows: Dict[Callable] = self.__get_methods_dict("flow")
        invariants: List[Callable] = self.__get_methods("invariant")

        for i in range(sequences_count):
            flows_counter: DefaultDict[Callable, int] = defaultdict(int)
            invariant_periods: DefaultDict[Callable[[None], None], int] = defaultdict(
                int
            )
            collector = JsonCollector(self.__class__.__name__) if record else None         

            snapshots = [chain.snapshot() for chain in chains]
            self._flow_num = 0
            self._sequence_num = i
            fp = {
                k: getattr(type(self), k, None)()
                if callable(getattr(type(self), k, None))
                else generate(v)
                for k, v in get_type_hints(getattr(type(self),"pre_sequence"), include_extras=True).items()
                if k != "return"
            }    
            pre_params = fp.values()                    
            self.pre_sequence(*pre_params)

            for j,uflow in enumerate(unit_flows):
                flow_name = uflow.name
                flow = flows.get(flow_name)

                fp = {}
                for k, v in get_type_hints(flow, include_extras=True).items():
                    if k != "return":
                        method = getattr(type(self), k, None)
                        if callable(method):
                            params_len = len(signature(method).parameters)
                            if params_len == 0:
                                fp[k] = method()
                            elif params_len == 1:
                                fp[k] = method(self)
                            else:
                                raise ValueError(
                                    f"Method {k} has an unsupported number of parameters.  Must take either no parameters or 1 parameter that is self"
                                )
                        else:
                            fp[k] = generate(v)

                flow_params = fp.values()

                self._flow_num = j
                self.pre_flow(flow)

                if collector is not None:
                    collector.collect(self, flow, **fp)

                if collector is not None:
                    collector.collect(self, flow, **fp)

                flow(self, *flow_params)
                flows_counter[flow] += 1
                self.post_flow(flow)
                for p in uflow.properties:
                    p(self)        
                if not dry_run:
                    self.pre_invariants()
                    for inv in invariants:
                        if invariant_periods[inv] == 0:
                            isnapshots = []
                            # if changes that occur during checking the invariant are not to be committed take a snapshot
                            if hasattr(inv, "commit_changes") == False:
                                isnapshots = [chain.snapshot() for chain in chains]
                            self.pre_invariant(inv)
                            inv(self)
                            self.post_invariant(inv)

                            # restore any snapshots saved before the invariant
                            for snapshot, chain in zip(isnapshots, chains):
                                chain.revert(snapshot)

                        invariant_periods[inv] += 1
                        if invariant_periods[inv] == getattr(inv, "period"):
                            invariant_periods[inv] = 0
                    self.post_invariants()

            self.post_sequence()

            for snapshot, chain in zip(snapshots, chains):
                chain.revert(snapshot)
