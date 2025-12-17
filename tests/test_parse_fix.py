#!/usr/bin/env python3
"""
Test Markdown parsing fix
"""

import os
import sys

# Add project path to system path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_parsing():
    """Test Markdown parsing functionality"""
    
    try:
        # Create index manager
        from teshi.utils.testcase_index_manager import TestCaseIndexManager
        index_manager = TestCaseIndexManager(".")
        
        # Parse test file
        test_file = "test_parsing.md"
        print(f"Parsing file: {test_file}")
        
        testcases = index_manager._parse_markdown_testcase(test_file)
        
        print(f"\nFound {len(testcases)} test cases:")
        
        for i, tc in enumerate(testcases, 1):
            print(f"\n--- Test Case {i} ---")
            print(f"Name: {tc.name}")
            print(f"Number: {tc.number}")
            print(f"Preconditions: {tc.preconditions}")
            print(f"Steps: {tc.steps}")
            print(f"Expected Results: {tc.expected_results}")
            print(f"Notes: {tc.notes}")
        
        # Test search functionality
        print("\n=== Testing Search ===")
        index_manager.build_index()
        
        # Search test
        search_terms = ["Internationalization", "Network", "Store"]
        for term in search_terms:
            results = index_manager.search_testcases(term)
            print(f"\nSearch for '{term}': {len(results)} results")
            for result in results:
                print(f"  - {result['name']}")
        
        print("\n=== All tests completed successfully! ===")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test files
        try:
            if os.path.exists("test_parsing.md"):
                os.remove("test_parsing.md")
            print("Cleaned up test files")
        except Exception as e:
            print(f"Cleanup error: {e}")

if __name__ == "__main__":
    test_parsing()