#!/usr/bin/env python3
"""
Convenience script to run all tests for the EisenhowerTriageAgent project.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add backend to path
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

def run_test(test_file):
    """Run a single test file and return success status."""
    print(f"\n{'='*50}")
    print(f"Running {test_file}...")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=False, 
                              text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running {test_file}: {str(e)}")
        return False

def main():
    """Run all tests in the project."""
    print("🧪 Running EisenhowerTriageAgent Tests")
    print("=" * 60)
    
    # Get the tests directory
    tests_dir = Path(__file__).parent.parent / "tests"
    
    if not tests_dir.exists():
        print(f"❌ Tests directory not found: {tests_dir}")
        return 1
    
    # Find all test files
    test_files = list(tests_dir.glob("test_*.py"))
    
    if not test_files:
        print(f"❌ No test files found in {tests_dir}")
        return 1
    
    print(f"Found {len(test_files)} test files:")
    for test_file in test_files:
        print(f"  - {test_file.name}")
    
    # Run each test
    passed = 0
    failed = 0
    
    for test_file in test_files:
        if run_test(test_file):
            print(f"✅ {test_file.name} passed")
            passed += 1
        else:
            print(f"❌ {test_file.name} failed")
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Test Results Summary:")
    print(f"  Total tests: {len(test_files)}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Success rate: {passed/len(test_files)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit(main()) 