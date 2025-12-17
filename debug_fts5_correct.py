#!/usr/bin/env python3
"""
Test FTS5 search functionality with correct format
"""

import os
import sys
import tempfile
import shutil
import sqlite3

# Add project path to system path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_correct_format():
    """Test FTS5 with correct test case format"""
    
    # Create temporary test directory
    test_dir = tempfile.mkdtemp(prefix="teshi_fts_correct_")
    
    try:
        print(f"Testing FTS5 with correct format in directory: {test_dir}")
        
        # Create correct format test Markdown file
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
        
        print(f"Created test file: {test_md_file}")
        
        # Create index manager
        from teshi.utils.testcase_index_manager import TestCaseIndexManager
        index_manager = TestCaseIndexManager(test_dir)
        
        # Build index
        print("Building index...")
        count = index_manager.build_index()
        print(f"Processed {count} files")
        
        # Check database content
        db_path = index_manager.db_path
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM testcases_fts")
        fts_count = cursor.fetchone()[0]
        print(f"FTS5 table count: {fts_count}")
        
        if fts_count > 0:
            cursor.execute("SELECT uuid, name, preconditions, steps, expected_results, notes, file_path FROM testcases_fts")
            rows = cursor.fetchall()
            print(f"Found {len(rows)} testcases:")
            for row in rows:
                print(f"  - {row[1]} (UUID: {row[0]})")
        
        # Test search functionality
        test_queries = [
            "Store",
            "Internationalization",
            "Login",
            "WebView",
            "Username",
            "Network"
        ]
        
        for query in test_queries:
            print(f"\nTesting search for: '{query}'")
            try:
                results = index_manager.search_testcases(query)
                print(f"Found {len(results)} results:")
                for result in results:
                    print(f"  - {result['name']}")
                    
            except Exception as e:
                print(f"  Search error: {e}")
        
        conn.close()
        
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
    test_correct_format()