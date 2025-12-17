#!/usr/bin/env python3
"""
Test fixed FTS5 search functionality
"""

import os
import sys
import tempfile
import shutil

# Add project path to system path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_search_fix():
    """Test fixed search functionality"""
    
    # Create temporary test directory
    test_dir = tempfile.mkdtemp(prefix="teshi_search_fix_")
    
    try:
        print(f"Testing fixed FTS5 search in directory: {test_dir}")
        
        # Create test file (using correct format)
        test_md_file = os.path.join(test_dir, "test.md")
        test_content = """## Test Case Name

Store_HomePage_Internationalization

## Number

Store_FirstPage_i18n

## Preconditions

1. Device is connected to network
2. Software is opened

## Operation Steps

1. Enhook software set to Chinese, click "Store" interface
2. Enhook software set to English, click "Store" interface

## Expected Results

1. Embedded WebView displays in Chinese
2. Embedded WebView displays in English

## Notes

---

## Test Case Name

User Login Function

## Number

User_Login_001

## Preconditions

System is running normally
Test user account exists in database

## Operation Steps

1. Open login page
2. Enter correct username
3. Enter correct password
4. Click login button

## Expected Results

Login successful, page redirects to main page

## Notes

Basic login test case
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
        
        # Test various search queries
        test_queries = [
            "Store",
            "Internationalization", 
            "Login",
            "User",
            "Network",
            "WebView",
            "Page",
            "System",
            "Running normally",
            "Button"
        ]
        
        print(f"\n=== Testing Fixed Search Function ===")
        for query in test_queries:
            print(f"\nSearching for: '{query}'")
            try:
                results = index_manager.search_testcases(query)
                print(f"Found {len(results)} results:")
                for result in results:
                    print(f"  - {result['name']}")
                    if result.get('name_snippet') and result['name_snippet'] != result['name']:
                        print(f"    Name snippet: {result['name_snippet']}")
                    
            except Exception as e:
                print(f"  Search error: {e}")
        
        # Test statistics functionality
        print(f"\n=== Testing Statistics ===")
        stats = index_manager.get_statistics()
        print(f"Statistics: {stats}")
        
        print(f"\n✅ Search functionality test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
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
    test_search_fix()