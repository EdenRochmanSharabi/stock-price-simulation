#!/usr/bin/env python3

"""
Test Method Coverage
------------------
Tests to ensure all public methods in models are explicitly tested somewhere.
"""

import unittest
import sys
import os
import importlib
import inspect

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the model classes
from stock_sim.models.base_model import StockModel
from stock_sim.models.gbm_model import GBMModel
from stock_sim.models.jump_diffusion_model import JumpDiffusionModel
from stock_sim.models.hybrid_model import HybridModel
from stock_sim.models.factory import ModelFactory


class TestMethodCoverage(unittest.TestCase):
    """Tests to ensure all methods are covered by tests."""
    
    def get_all_methods(self, cls):
        """Get all public methods from a class."""
        methods = []
        for name, member in inspect.getmembers(cls):
            if (not name.startswith('_') and  # Exclude private/special methods
                inspect.isfunction(member) or inspect.ismethod(member)):
                methods.append(name)
        return methods
    
    def get_all_subclasses(self, cls):
        """Get all subclasses of a class."""
        all_subclasses = []
        for subclass in cls.__subclasses__():
            all_subclasses.append(subclass)
            all_subclasses.extend(self.get_all_subclasses(subclass))
        return all_subclasses
    
    def find_test_method(self, method_name, test_dir=None):
        """Find if a method is mentioned in any test file."""
        if test_dir is None:
            test_dirs = [
                os.path.join(os.path.dirname(__file__), '..', 'UnitTest'),
                os.path.join(os.path.dirname(__file__), '..', 'tests')
            ]
        else:
            test_dirs = [test_dir]
        
        # Normalize method name for search
        search_terms = [
            method_name,
            f"model.{method_name}",
            f".{method_name}("
        ]
        
        for test_dir in test_dirs:
            for root, dirs, files in os.walk(test_dir):
                for file in files:
                    if file.startswith('test_') and file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()
                                if any(term in content for term in search_terms):
                                    return True
                        except Exception as e:
                            print(f"Error reading {file_path}: {e}")
        
        return False
    
    def test_base_model_methods_coverage(self):
        """Test that all methods in StockModel are covered by tests."""
        methods = self.get_all_methods(StockModel)
        
        uncovered_methods = []
        for method in methods:
            if not self.find_test_method(method):
                uncovered_methods.append(method)
        
        self.assertEqual(uncovered_methods, [], f"These methods in StockModel are not covered by tests: {uncovered_methods}")
    
    def test_gbm_model_methods_coverage(self):
        """Test that all methods in GBMModel are covered by tests."""
        methods = self.get_all_methods(GBMModel)
        
        uncovered_methods = []
        for method in methods:
            if not self.find_test_method(method):
                uncovered_methods.append(method)
        
        self.assertEqual(uncovered_methods, [], f"These methods in GBMModel are not covered by tests: {uncovered_methods}")
    
    def test_jump_diffusion_model_methods_coverage(self):
        """Test that all methods in JumpDiffusionModel are covered by tests."""
        methods = self.get_all_methods(JumpDiffusionModel)
        
        uncovered_methods = []
        for method in methods:
            if not self.find_test_method(method):
                uncovered_methods.append(method)
        
        self.assertEqual(uncovered_methods, [], f"These methods in JumpDiffusionModel are not covered by tests: {uncovered_methods}")
    
    def test_hybrid_model_methods_coverage(self):
        """Test that all methods in HybridModel are covered by tests."""
        methods = self.get_all_methods(HybridModel)
        
        uncovered_methods = []
        for method in methods:
            if not self.find_test_method(method):
                uncovered_methods.append(method)
        
        self.assertEqual(uncovered_methods, [], f"These methods in HybridModel are not covered by tests: {uncovered_methods}")
    
    def test_model_factory_methods_coverage(self):
        """Test that all methods in ModelFactory are covered by tests."""
        methods = self.get_all_methods(ModelFactory)
        
        uncovered_methods = []
        for method in methods:
            if not self.find_test_method(method):
                uncovered_methods.append(method)
        
        self.assertEqual(uncovered_methods, [], f"These methods in ModelFactory are not covered by tests: {uncovered_methods}")
    
    def test_all_stock_models_subclasses_coverage(self):
        """Test that all StockModel subclasses are covered by tests."""
        subclasses = self.get_all_subclasses(StockModel)
        
        # Check if each subclass name appears in test files
        uncovered_classes = []
        for cls in subclasses:
            class_name = cls.__name__
            if not self.find_test_method(class_name):
                uncovered_classes.append(class_name)
        
        self.assertEqual(uncovered_classes, [], f"These StockModel subclasses are not covered by tests: {uncovered_classes}")


class TableTestResult(unittest.TestResult):
    """Custom TestResult class that collects test results for table display."""
    
    def __init__(self):
        super().__init__()
        self.test_results = []
        self.start_times = {}
        self.method_coverage = {}
    
    def startTest(self, test):
        super().startTest(test)
        import time
        test_name = self._get_test_name(test)
        self.start_times[test_name] = time.time()
    
    def addSuccess(self, test):
        super().addSuccess(test)
        import time
        test_name = self._get_test_name(test)
        duration = time.time() - self.start_times[test_name]
        self.test_results.append({
            'name': test_name,
            'status': 'PASS',
            'time': duration
        })
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        import time
        test_name = self._get_test_name(test)
        duration = time.time() - self.start_times[test_name]
        
        # Extract uncovered methods from the error
        import re
        error_str = str(err[1])
        methods_match = re.search(r"not covered by tests: \[(.*)\]", error_str)
        if methods_match:
            methods_str = methods_match.group(1)
            methods = [m.strip().strip("'") for m in methods_str.split(",")]
            
            # Extract the class name from the test name
            class_match = re.search(r"test_(.*?)_methods_coverage", test_name)
            if class_match:
                class_name = class_match.group(1).replace('_', '')
                self.method_coverage[class_name] = methods
        
        self.test_results.append({
            'name': test_name,
            'status': 'FAIL',
            'time': duration,
            'error': err
        })
    
    def addError(self, test, err):
        super().addError(test, err)
        import time
        test_name = self._get_test_name(test)
        duration = time.time() - self.start_times.get(test_name, time.time())
        self.test_results.append({
            'name': test_name,
            'status': 'ERROR',
            'time': duration,
            'error': err
        })
    
    def _get_test_name(self, test):
        """Extract test name from test object."""
        return test.id().split('.')[-1]


def print_test_results_table(result):
    """Print test results in a nice table format."""
    if not result.test_results:
        print("No tests were run.")
        return
    
    # Print header
    print("\n" + "="*80)
    print("{:<40} {:<10} {:<15}".format("Test Name", "Status", "Time (s)"))
    print("-"*80)
    
    # Print each test result
    for test_result in result.test_results:
        status = test_result['status']
        status_formatted = f"\033[92m{status}\033[0m" if status == 'PASS' else f"\033[91m{status}\033[0m"
        print("{:<40} {:<25} {:.6f}".format(
            test_result['name'],
            status_formatted,
            test_result['time']
        ))
    
    # Print summary
    total = len(result.test_results)
    passed = sum(1 for r in result.test_results if r['status'] == 'PASS')
    failed = sum(1 for r in result.test_results if r['status'] in ('FAIL', 'ERROR'))
    
    print("-"*80)
    print(f"Total: {total} | Passed: {passed} | Failed: {failed}")
    
    # If there are uncovered methods, print a detailed report
    if hasattr(result, 'method_coverage') and result.method_coverage:
        print("\n" + "="*80)
        print("UNCOVERED METHODS REPORT")
        print("-"*80)
        
        for class_name, methods in result.method_coverage.items():
            print(f"Class: \033[1m{class_name}\033[0m")
            for method in methods:
                print(f"  - {method}")
            print()
        
        print("-"*80)
        print("Consider adding tests for these methods to improve coverage.")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    # Create a test suite with all tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMethodCoverage)
    
    # Run the tests and collect results
    result = TableTestResult()
    suite.run(result)
    
    # Print the results table
    print_test_results_table(result) 