#!/usr/bin/env python3

"""
Test Runner
----------
A utility script to run all tests and display results in a nice table format.
"""

import unittest
import sys
import os
import time
import importlib
import datetime
try:
    import coverage
    COVERAGE_AVAILABLE = True
except ImportError:
    COVERAGE_AVAILABLE = False
    print("Warning: coverage package not installed. Run 'pip install coverage' for test coverage reporting.")

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TableTestResult(unittest.TestResult):
    """Custom TestResult class that collects test results for table display."""
    
    def __init__(self):
        super().__init__()
        self.test_results = []
        self.start_times = {}
        self.total_start_time = time.time()
    
    def startTest(self, test):
        super().startTest(test)
        test_name = self._get_test_name(test)
        test_class = self._get_test_class(test)
        self.start_times[test_name] = time.time()
        print(f"Running {test_class}.{test_name}...", end="\r")
    
    def addSuccess(self, test):
        super().addSuccess(test)
        test_name = self._get_test_name(test)
        test_class = self._get_test_class(test)
        duration = time.time() - self.start_times[test_name]
        self.test_results.append({
            'name': test_name,
            'class': test_class,
            'status': 'PASS',
            'time': duration
        })
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        test_name = self._get_test_name(test)
        test_class = self._get_test_class(test)
        duration = time.time() - self.start_times[test_name]
        self.test_results.append({
            'name': test_name,
            'class': test_class,
            'status': 'FAIL',
            'time': duration,
            'error': err
        })
    
    def addError(self, test, err):
        super().addError(test, err)
        test_name = self._get_test_name(test)
        test_class = self._get_test_class(test)
        duration = time.time() - self.start_times.get(test_name, time.time())
        self.test_results.append({
            'name': test_name,
            'class': test_class,
            'status': 'ERROR',
            'time': duration,
            'error': err
        })
    
    def _get_test_name(self, test):
        """Extract test name from test object."""
        return test.id().split('.')[-1]
    
    def _get_test_class(self, test):
        """Extract test class from test object."""
        return test.id().split('.')[-2]
    
    def get_total_time(self):
        """Get total execution time."""
        return time.time() - self.total_start_time


def print_test_results_table(result):
    """Print test results in a nice table format."""
    if not result.test_results:
        print("No tests were run.")
        return
    
    # Print header
    print("\n" + "="*100)
    print("{:<20} {:<40} {:<10} {:<15}".format("Test Class", "Test Name", "Status", "Time (s)"))
    print("-"*100)
    
    # Group results by test class for better organization
    results_by_class = {}
    for test_result in result.test_results:
        class_name = test_result['class']
        if class_name not in results_by_class:
            results_by_class[class_name] = []
        results_by_class[class_name].append(test_result)
    
    # Print each test result organized by class
    for class_name, class_results in results_by_class.items():
        # Print class results
        for test_result in class_results:
            status = test_result['status']
            status_formatted = f"\033[92m{status}\033[0m" if status == 'PASS' else f"\033[91m{status}\033[0m"
            print("{:<20} {:<40} {:<25} {:.6f}".format(
                class_name,
                test_result['name'],
                status_formatted,
                test_result['time']
            ))
        
        # Add a separator between classes
        if len(results_by_class) > 1:
            print("-"*100)
    
    # Print summary
    total = len(result.test_results)
    passed = sum(1 for r in result.test_results if r['status'] == 'PASS')
    failed = sum(1 for r in result.test_results if r['status'] in ('FAIL', 'ERROR'))
    
    print("-"*100)
    print(f"Total: {total} | Passed: {passed} | Failed: {failed} | Time: {result.get_total_time():.2f}s")
    print("="*100 + "\n")


def get_all_modules(directory=None):
    """Discover all Python modules in a directory."""
    if directory is None:
        directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'stock_sim'))
    
    modules = []
    
    for root, dirs, files in os.walk(directory):
        # Skip __pycache__ and hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('__') and not d.startswith('.')]
        
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                file_path = os.path.join(root, file)
                # Convert file path to module name
                rel_path = os.path.relpath(file_path, os.path.abspath(os.path.join(directory, '..')))
                module_name = os.path.splitext(rel_path)[0].replace(os.path.sep, '.')
                modules.append(module_name)
    
    return modules


def analyze_method_coverage(cov, modules):
    """Analyze which methods are covered by tests."""
    # Get coverage data by module
    uncovered_methods = {}
    
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
            module_file = module.__file__
            
            # Get coverage data for this module
            file_data = cov.get_data().get_file_report(module_file)
            if not file_data:
                continue
            
            # Find methods in the module
            for name, obj in module.__dict__.items():
                if callable(obj) and not name.startswith('__'):
                    try:
                        if hasattr(obj, '__code__'):
                            # Get line numbers for the method
                            start_line = obj.__code__.co_firstlineno
                            if start_line not in file_data.lines:
                                uncovered_methods.setdefault(module_name, []).append(name)
                    except (AttributeError, TypeError):
                        pass
            
            # Check class methods
            for name, obj in module.__dict__.items():
                if isinstance(obj, type):  # This is a class
                    for method_name, method in obj.__dict__.items():
                        if callable(method) and not method_name.startswith('__'):
                            try:
                                if hasattr(method, '__code__'):
                                    # Get line numbers for the method
                                    start_line = method.__code__.co_firstlineno
                                    if start_line not in file_data.lines:
                                        uncovered_methods.setdefault(module_name, []).append(f"{name}.{method_name}")
                            except (AttributeError, TypeError):
                                pass
        except (ImportError, AttributeError) as e:
            print(f"Error analyzing module {module_name}: {e}")
    
    return uncovered_methods


def print_method_coverage_report(uncovered_methods):
    """Print a report of uncovered methods."""
    print("\n" + "="*100)
    print("UNCOVERED METHODS REPORT")
    print("-"*100)
    
    if not uncovered_methods:
        print("All methods appear to be covered by tests!")
        return
    
    total_uncovered = sum(len(methods) for methods in uncovered_methods.values())
    print(f"Found {total_uncovered} methods that don't appear to be covered by tests:\n")
    
    for module, methods in sorted(uncovered_methods.items()):
        print(f"Module: \033[1m{module}\033[0m")
        for method in sorted(methods):
            print(f"  - {method}")
        print()
    
    print("-"*100)
    print("Consider adding tests for these methods to improve coverage.")
    print("="*100 + "\n")


def discover_and_run_tests(test_directories=None, with_coverage=True):
    """Discover and run all tests from specified directories."""
    if test_directories is None:
        test_directories = ['UnitTest', 'tests']
    
    # Initialize coverage if available and requested
    cov = None
    if COVERAGE_AVAILABLE and with_coverage:
        cov = coverage.Coverage(
            source=['stock_sim'],
            omit=['*/__init__.py', '*/test_*.py', '*/*_test.py', '*_test.py']
        )
        cov.start()
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add tests from each directory
    for test_dir in test_directories:
        if os.path.exists(test_dir) and os.path.isdir(test_dir):
            print(f"Discovering tests in {test_dir}...")
            # Add the directory to sys.path to allow imports
            sys.path.insert(0, os.path.abspath(test_dir))
            discovered_tests = loader.discover(test_dir, pattern='test_*.py')
            suite.addTest(discovered_tests)
    
    # Create a test result collector
    result = TableTestResult()
    
    # Run the tests
    print(f"\nRunning tests at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...\n")
    suite.run(result)
    
    # Print the results
    print_test_results_table(result)
    
    # Handle coverage reporting if enabled
    if cov:
        cov.stop()
        
        print("\nGenerating coverage report...")
        # Generate HTML report
        cov.html_report(directory='coverage_html')
        print(f"HTML coverage report generated in coverage_html/index.html")
        
        # Generate console report
        print("\nCoverage Summary:")
        cov.report()
        
        # Analyze method coverage
        modules = get_all_modules()
        uncovered_methods = analyze_method_coverage(cov, modules)
        print_method_coverage_report(uncovered_methods)
    
    # Return the result for additional processing if needed
    return result


if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Run all tests with coverage reporting.')
    parser.add_argument('--no-coverage', action='store_true', help='Disable coverage reporting')
    parser.add_argument('test_dirs', nargs='*', help='Specific test directories to run')
    
    args = parser.parse_args()
    
    # Run the tests
    result = discover_and_run_tests(
        test_directories=args.test_dirs if args.test_dirs else None,
        with_coverage=not args.no_coverage
    )
    
    # Exit with appropriate code
    sys.exit(len(result.errors) + len(result.failures)) 