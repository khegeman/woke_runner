
from typing import Callable, DefaultDict, List, Optional, Type,Dict,Iterable,get_type_hints

from woke.testing.fuzzing import FuzzTest 

from .runner import run, BoundFlow

def unit_test(test:FuzzTest, name : str, params : Dict, properties : List[Callable] = []):
    
    run(test, bound_flows=[BoundFlow(name=name, params=params,properties=properties)])    