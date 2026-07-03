import os
import importlib.util
import inspect
from core.benchmark_base import BenchmarkTest

def load_tests_from_folder():
    """
    Scans the 'tests/' directory for subclasses of BenchmarkTest.
    Returns a list of Class types (not instances).
    """
    found_tests = []
    tests_dir = os.path.join(os.getcwd(), 'tests')
    
    if not os.path.exists(tests_dir):
        os.makedirs(tests_dir)
        return []

    for filename in os.listdir(tests_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            path = os.path.join(tests_dir, filename)
            spec = importlib.util.spec_from_file_location(filename[:-3], path)
            
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Inspect module for BenchmarkTest subclasses
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BenchmarkTest) and 
                        obj is not BenchmarkTest):
                        found_tests.append(obj)
                        
    return found_tests