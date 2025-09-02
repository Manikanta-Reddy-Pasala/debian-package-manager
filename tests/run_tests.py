"""Test runner and validation script."""

import pytest
import sys
import os
from pathlib import Path


def run_tests():
    """Run all tests and generate coverage report."""
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    
    if not tests_dir.exists():
        print(f"❌ Tests directory not found: {tests_dir}")
        return 1
    
    # Configure pytest arguments
    pytest_args = [
        str(tests_dir),
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Treat unknown markers as errors
        "--disable-warnings",  # Disable warnings for cleaner output
        "-x",  # Stop on first failure
    ]
    
    # Add coverage if available
    try:
        import pytest_cov
        pytest_args.extend([
            "--cov=src/debian_metapackage_manager",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-fail-under=80"
        ])
    except ImportError:
        print("ℹ️  pytest-cov not available, running without coverage")
    
    print("🧪 Running Debian Package Manager Test Suite")
    print("=" * 60)
    
    # Run the tests
    result = pytest.main(pytest_args)
    
    if result == 0:
        print("\n✅ All tests passed successfully!")
        print("🎉 Test suite validation complete!")
    else:
        print(f"\n❌ Tests failed with exit code: {result}")
        print("Please fix the failing tests before proceeding.")
    
    return result


def validate_test_structure():
    """Validate the test directory structure."""
    
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    
    print("🔍 Validating test structure...")
    
    # Required test files
    required_files = [
        "conftest.py",
        "test_models_package.py",
        "test_models_operations.py", 
        "test_config.py",
        "test_utils_network.py",
        "test_utils_validation.py",
        "test_utils_error.py",
        "test_utils_logging.py",
        "test_interfaces_apt.py",
        "test_interfaces_dpkg.py",
        "test_core_functionality.py",
        "test_cli_commands.py",
        "test_integration.py"
    ]
    
    missing_files = []
    existing_files = []
    
    for required_file in required_files:
        file_path = tests_dir / required_file
        if file_path.exists():
            existing_files.append(required_file)
            print(f"  ✅ {required_file}")
        else:
            missing_files.append(required_file)
            print(f"  ❌ {required_file} (missing)")
    
    print(f"\n📊 Test Structure Summary:")
    print(f"  - Total required files: {len(required_files)}")
    print(f"  - Existing files: {len(existing_files)}")
    print(f"  - Missing files: {len(missing_files)}")
    
    if missing_files:
        print(f"\n⚠️  Missing test files:")
        for missing_file in missing_files:
            print(f"    - {missing_file}")
        return False
    
    print(f"\n✅ Test structure validation passed!")
    return True


def count_test_functions():
    """Count the number of test functions in all test files."""
    
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    
    total_tests = 0
    test_files = {}
    
    for test_file in tests_dir.glob("test_*.py"):
        with open(test_file, 'r') as f:
            content = f.read()
            
        # Count test functions (def test_*)
        test_count = content.count("def test_")
        test_files[test_file.name] = test_count
        total_tests += test_count
    
    print("📈 Test Coverage Statistics:")
    print("-" * 40)
    
    for file_name, count in sorted(test_files.items()):
        print(f"  {file_name:<25} {count:>3} tests")
    
    print("-" * 40)
    print(f"  {'TOTAL':<25} {total_tests:>3} tests")
    
    return total_tests


def main():
    """Main entry point for test validation."""
    
    print("🚀 Debian Package Manager - Test Suite Validation")
    print("=" * 60)
    
    # Step 1: Validate test structure
    structure_valid = validate_test_structure()
    if not structure_valid:
        return 1
    
    # Step 2: Count test functions
    test_count = count_test_functions()
    print(f"\n📝 Found {test_count} test functions across all test files")
    
    # Step 3: Run the tests
    print(f"\n🏃 Executing test suite...")
    result = run_tests()
    
    if result == 0:
        print(f"\n🎊 SUCCESS: All {test_count} tests are working correctly!")
        print("✨ The Debian Package Manager test suite is comprehensive and complete.")
        print("\n📋 Test Coverage Summary:")
        print("  ✅ Data Models (Package, OperationResult, Conflict, etc.)")
        print("  ✅ Configuration Management")
        print("  ✅ Utility Functions (Network, Validation, Error Handling, Logging)")
        print("  ✅ System Interfaces (APT, DPKG)")
        print("  ✅ Core Functionality (Package Management, Classification, Mode Management)")
        print("  ✅ CLI Command Handlers")
        print("  ✅ Integration & End-to-End Workflows")
        print("\n🔧 To run tests manually:")
        print("  cd /Users/manip/Documents/codeRepo/poc/debian-apt-update")
        print("  python -m pytest tests/ -v")
        print("\n📊 For coverage report:")
        print("  python -m pytest tests/ --cov=src/debian_metapackage_manager --cov-report=html")
    else:
        print(f"\n💥 FAILURE: Some tests are not working properly.")
        print("Please review the test output above and fix any issues.")
    
    return result


if __name__ == "__main__":
    sys.exit(main())