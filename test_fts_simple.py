#!/usr/bin/env python3
"""
Simple test FTS5 index functionality
"""

import os
import sys
import tempfile
import shutil

# Add project path to system path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_simple_fts():
    """Simple test FTS5 functionality"""
    
    # Create temporary test directory
    test_dir = tempfile.mkdtemp(prefix="teshi_fts_test_")
    
    try:
        print(f"Testing FTS5 in directory: {test_dir}")
        
        # Create test Markdown file
        test_md_file = os.path.join(test_dir, "test.md")
        test_content = """# Login Test

## Preconditions
System is running normally

## Operation Steps
1. Open login page
2. Enter username and password
3. Click login button

## Expected Results
Login successful

---

# Registration Test

## Preconditions
System is running normally

## Operation Steps
1. Open registration page
2. Fill registration information
3. Submit registration

## Expected Results
Registration successful
"""
        
        with open(test_md_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Create index manager
        from teshi.utils.testcase_index_manager import TestCaseIndexManager
        index_manager = TestCaseIndexManager(test_dir)
        
        # Build index
        print("Building index...")
        count = index_manager.build_index()
        print(f"Processed {count} files")
        
        # Test search
        print("Testing search for 'Login'...")
        results = index_manager.search_testcases("Login")
        print(f"Found {len(results)} results")
        for result in results:
            print(f"  - {result['name']}")
        
        print("Testing search for 'Registration'...")
        results = index_manager.search_testcases("Registration")
        print(f"Found {len(results)} results")
        for result in results:
            print(f"  - {result['name']}")
        
        print("All tests passed!")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(test_dir)
            print(f"Cleaned up: {test_dir}")
        except Exception as e:
            print(f"Cleanup error: {e}")

if __name__ == "__main__":
    test_simple_fts()