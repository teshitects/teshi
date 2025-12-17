#!/usr/bin/env python3
"""
Test case index manager test script
"""

import os
import sys
import tempfile
import shutil

# Add project path to system path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from teshi.utils.testcase_index_manager import TestCaseIndexManager


def test_index_manager():
    """Test index manager"""
    
    # Create temporary test directory
    test_dir = tempfile.mkdtemp(prefix="teshi_test_")
    
    try:
        print(f"Testing in directory: {test_dir}")
        
        # Create test Markdown file
        test_md_file = os.path.join(test_dir, "test_case.md")
        test_content = """# Test Case 1

## Preconditions
System is running normally

## Operation Steps
1. Open application
2. Execute operation
3. Verify result

## Expected Results
Operation successful

## Notes
This is a test case

---

# Test Case 2

## Preconditions
User is logged in

## Operation Steps
1. Access function
2. Input data
3. Submit

## Expected Results
Data saved successfully
"""
        
        with open(test_md_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Create index manager
        index_manager = TestCaseIndexManager(test_dir)
        
        # Test first index build
        print("\n=== Testing first index build ===")
        count = index_manager.build_index()
        print(f"Processed {count} files")
        
        # Check statistics
        stats = index_manager.get_statistics()
        print(f"Statistics: {stats}")
        
        # Test search
        print("\n=== Testing search ===")
        results = index_manager.search_testcases("Operation Steps")
        print(f"Search results for 'Operation Steps': {len(results)} items")
        for result in results:
            print(f"  - {result['name']}")
        
        results = index_manager.search_testcases("Test Case 1")
        print(f"Search results for 'Test Case 1': {len(results)} items")
        for result in results:
            print(f"  - {result['name']}")
        
        # Get all test cases
        print("\n=== Getting all test cases ===")
        all_testcases = index_manager.get_all_testcases()
        print(f"Total test cases: {len(all_testcases)}")
        for tc in all_testcases:
            print(f"  - {tc['name']}")
        
        # Test file update
        print("\n=== Testing file update ===")
        updated_content = test_content + "\n\n# New Test Case\n\n## Preconditions\nNew condition\n\n## Operation Steps\nNew steps\n\n## Expected Results\nNew result\n"
        with open(test_md_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        count = index_manager.build_index()
        print(f"Updated {count} files")
        
        stats = index_manager.get_statistics()
        print(f"Updated statistics: {stats}")
        
        # Test search new content
        results = index_manager.search_testcases("New Test Case")
        print(f"Search results for 'New Test Case': {len(results)} items")
        for result in results:
            print(f"  - {result['name']}")
        
        print("\n=== All tests completed successfully! ===")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(test_dir)
            print(f"Cleaned up test directory: {test_dir}")
        except Exception as e:
            print(f"Error cleaning up: {e}")


if __name__ == "__main__":
    test_index_manager()