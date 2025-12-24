#!/usr/bin/env python3
"""
Detailed test for space-separated keyword search functionality
"""

import os
import tempfile
from teshi.utils.testcase_index_manager import TestCaseIndexManager

def test_detailed_space_search():
    """Test detailed functionality of space-separated search"""
    print("=== Detailed Space-Separated Search Test ===")
    
    # Create temporary directory for testing
    test_dir = tempfile.mkdtemp(prefix="teshi_detailed_space_search_")
    
    try:
        # Create test file with specific content to test space separation
        test_md_file = os.path.join(test_dir, "test.md")
        with open(test_md_file, 'w', encoding='utf-8') as f:
            f.write("""# Test Cases

## Test Case Name
用户登录功能

### Number
TC001

### Preconditions
用户已注册

### Operation Steps
登录操作

### Expected Results
登录成功

---

## Test Case Name
注册功能测试

### Number
TC002

### Preconditions
新用户

### Operation Steps
注册流程

### Expected Results
注册成功

---

## Test Case Name
系统管理功能

### Number
TC003

### Preconditions
管理员权限

### Operation Steps
系统管理操作

### Expected Results
管理功能正常
""")
        
        # Initialize index manager
        index_manager = TestCaseIndexManager(test_dir)
        index_manager.build_index()
        
        print("\n=== Testing Search Terms Preparation ===")
        # Test the search terms preparation function directly
        test_queries = [
            "用户 登录",
            "注册 功能", 
            "系统 管理",
            "用户 注册",
            "登录 功能 系统",
        ]
        
        for query in test_queries:
            terms = index_manager._prepare_chinese_search_terms(query)
            print(f"Query: '{query}' -> Terms: {terms}")
        
        print("\n=== Testing Actual Search Results ===")
        # Test actual search with space-separated keywords
        for query in test_queries:
            print(f"\nSearching for: '{query}'")
            try:
                results = index_manager.search_testcases(query)
                print(f"Found {len(results)} results:")
                for result in results:
                    print(f"  - {result['name']}")
            except Exception as e:
                print(f"  Error: {e}")
        
        print("\n=== Comparison with Single Keywords ===")
        # Compare space-separated vs single keyword searches
        comparison_queries = [
            ("用户", "用户 登录"),
            ("登录", "用户 登录"), 
            ("注册", "注册 功能"),
            ("功能", "注册 功能"),
        ]
        
        for single_query, space_query in comparison_queries:
            print(f"\nComparing search results:")
            print(f"Single '{single_query}' vs Space-separated '{space_query}'")
            
            single_results = index_manager.search_testcases(single_query)
            space_results = index_manager.search_testcases(space_query)
            
            print(f"  Single: {len(single_results)} results")
            print(f"  Space-separated: {len(space_results)} results")
            
            # Check if results are the same
            single_names = [r['name'] for r in single_results]
            space_names = [r['name'] for r in space_results]
            
            if set(single_names) == set(space_names):
                print("  Results: SAME")
            else:
                print("  Results: DIFFERENT")
                print(f"    Single only: {set(single_names) - set(space_names)}")
                print(f"    Space only: {set(space_names) - set(single_names)}")
        
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(test_dir)
        print(f"\nCleaned up test directory: {test_dir}")

if __name__ == "__main__":
    test_detailed_space_search()