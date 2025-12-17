#!/usr/bin/env python3
"""
Detailed debugging of FTS5 search functionality
"""

import os
import sys
import tempfile
import shutil
import sqlite3

# Add project path to system path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_search_details():
    """Detailed debugging of search functionality"""
    
    # Create temporary test directory
    test_dir = tempfile.mkdtemp(prefix="teshi_search_debug_")
    
    try:
        print(f"Debugging FTS5 search in directory: {test_dir}")
        
        # Create test file
        test_md_file = os.path.join(test_dir, "test.md")
        test_content = """## Test Case Name

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
        index_manager.build_index()
        
        # Check database content
        db_path = index_manager.db_path
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # View all data
        cursor.execute("SELECT name, preconditions, steps, expected_results, notes FROM testcases_fts")
        rows = cursor.fetchall()
        
        print(f"Database content:")
        for i, row in enumerate(rows):
            print(f"\nTestcase {i+1}:")
            print(f"  Name: {row[0]}")
            print(f"  Preconditions: {row[1]}")
            print(f"  Steps: {row[2]}")
            print(f"  Expected Results: {row[3]}")
            print(f"  Notes: {row[4]}")
        
        # Test different FTS5 search syntax
        test_queries = [
            "登录",
            "用户",
            "页面",
            "系统",
            "正常运行",
            "login",  # English test
            "用户登录功能"
        ]
        
        print(f"\n=== Testing different search queries ===")
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            
            # Method 1: Direct MATCH query
            try:
                cursor.execute("""
                    SELECT name, snippet(testcases_fts, 1, '<mark>', '</mark>', '...', 32) as snippet
                    FROM testcases_fts 
                    WHERE testcases_fts MATCH ?
                    ORDER BY rank
                """, (query,))
                
                results = cursor.fetchall()
                print(f"  MATCH: {len(results)} results")
                for row in results:
                    print(f"    - {row[0]} (snippet: {row[1]})")
            except Exception as e:
                print(f"  MATCH error: {e}")
            
            # Method 2: Use NEAR query
            try:
                cursor.execute("""
                    SELECT name 
                    FROM testcases_fts 
                    WHERE testcases_fts MATCH ?
                    ORDER BY rank
                """, (f'"{query}"',))  # Exact match
                
                results = cursor.fetchall()
                print(f"  EXACT: {len(results)} results")
                for row in results:
                    print(f"    - {row[0]}")
            except Exception as e:
                print(f"  EXACT error: {e}")
            
            # Method 3: LIKE query for comparison
            cursor.execute("""
                SELECT name 
                FROM testcases_fts 
                WHERE name LIKE ? OR preconditions LIKE ? OR steps LIKE ? OR expected_results LIKE ?
            """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
            
            results = cursor.fetchall()
            print(f"  LIKE: {len(results)} results")
            for row in results:
                print(f"    - {row[0]}")
        
        # Check FTS5 tokenizer configuration
        print(f"\n=== FTS5 Configuration ===")
        cursor.execute("PRAGMA table_info(testcases_fts)")
        columns = cursor.fetchall()
        print(f"Table columns: {columns}")
        
        # Check FTS5 special commands
        try:
            cursor.execute("INSERT INTO testcases_fts(testcases_fts) VALUES('optimize')")
            conn.commit()
            print("Optimized FTS5 index")
        except Exception as e:
            print(f"Optimize error: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"Debug failed: {e}")
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
    debug_search_details()