"""

Replacement for woke fuzz test that drives a corpus replay. 

The fundamental difference is that flows are not randomized but instead are run in sequence based on data loaded from json.

"""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Callable, DefaultDict, List, Optional, Type,Dict,get_type_hints

from typing_extensions import get_type_hints,get_args, get_origin
from dataclasses import fields,dataclass

from woke.testing.core import get_connected_chains
from woke.testing import fuzzing

import jsons
import copy

@dataclass 
class UnitFlow:
    name : str 
    params : Dict
    properties : List

class FuzzTest(fuzzing.FuzzTest):
    def __get_methods_dict(self, attr: str) -> Dict[Callable]:
        ret = {}
        for x in dir(self):
            if hasattr(self.__class__, x):
                m = getattr(self.__class__, x)
                if hasattr(m, attr) and getattr(m, attr):
                    ret[x] = m
        return ret

    def get_param(params : Dict, param: str, sequence_num: int, flow_num: int,t: Type):
        
        print(params)
        print(param)
        data = params
        value = data[param]
        if get_origin(t) is list:
            return [get_args(t)[0](v) for v in value]
        if type(value) is dict:
            #assuming this type is a dataclass that defines fields for now

            resolved_hints = get_type_hints(t)
            field_names = [field.name for field in fields(t)]
            resolved_field_types = {name: resolved_hints[name] for name in field_names}                
            args = {field.name:resolved_field_types[field.name](value[field.name])  for field in fields(t)}

            return t(**args)
        return t(value)


    def run(
        self,
        *,
        dry_run: bool = False,
        unit_flows: List[UnitFlow],
        properties : List
    ):
        chains = get_connected_chains()

        flows: Dict[Callable] = self.__get_methods_dict("flow")
        invariants: List[Callable] = self.__get_methods("invariant")


        flows_counter: DefaultDict[Callable, int] = defaultdict(int)
        invariant_periods: DefaultDict[Callable[[None], None], int] = defaultdict(
            int
        )

        snapshots = [chain.snapshot() for chain in chains]
        self._flow_num = 0
        self._sequence_num = 0
        self.pre_sequence()



        for j,uflow in enumerate(unit_flows):
            flow_name = uflow.name
            flow = flows.get(flow_name)
            
            fp = uflow.params
                            
            self._flow_num = j
            self.pre_flow(flow)
            flow(self, **fp)
            flows_counter[flow] += 1
            self.post_flow(flow)
            for p in uflow.properties:
                p(self)            

            if not dry_run:
                self.pre_invariants()
                for inv in invariants:
                    if invariant_periods[inv] == 0:
                        self.pre_invariant(inv)
                        inv(self)
                        self.post_invariant(inv)

                    invariant_periods[inv] += 1
                    if invariant_periods[inv] == getattr(inv, "period"):
                        invariant_periods[inv] = 0
                self.post_invariants()

        for p in properties:
            print(p)
            p(self)

        self.post_sequence()

        for snapshot, chain in zip(snapshots, chains):
            chain.revert(snapshot)
