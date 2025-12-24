#!/usr/bin/env python3
"""
Test space-separated keyword search functionality
"""

import os
import tempfile
from teshi.utils.testcase_index_manager import TestCaseIndexManager

def test_space_separated_search():
    """Test search with space-separated keywords"""
    print("=== Testing Space-Separated Keyword Search ===")
    
    # Create temporary directory for testing
    test_dir = tempfile.mkdtemp(prefix="teshi_space_search_")
    
    try:
        print(f"Testing space-separated search in directory: {test_dir}")
        
        # Create test file with multiple test cases
        test_md_file = os.path.join(test_dir, "test.md")
        with open(test_md_file, 'w', encoding='utf-8') as f:
            f.write("""# Test Cases

## Test Case Name
用户登录功能测试

### Number
TC001

### Preconditions
用户已注册账号

### Operation Steps
1. 打开登录页面
2. 输入用户名和密码
3. 点击登录按钮

### Expected Results
成功登录到系统

---

## Test Case Name
User Registration Test

### Number
TC002

### Preconditions
用户未注册账号

### Operation Steps
1. 打开注册页面
2. 填写注册信息
3. 提交注册表单

### Expected Results
成功创建用户账号

---

## Test Case Name
系统权限管理

### Number
TC003

### Preconditions
用户已登录系统

### Operation Steps
1. 进入权限管理页面
2. 设置用户权限
3. 保存权限设置

### Expected Results
权限设置生效
""")
        
        # Initialize index manager
        index_manager = TestCaseIndexManager(test_dir)
        index_manager.build_index()
        
        # Test cases for space-separated search
        test_queries = [
            "用户 登录",        # Chinese keywords with space
            "User Registration", # English keywords with space  
            "系统 权限",        # Chinese keywords with space
            "登录 权限",        # Keywords from different test cases
            "Test User",        # English keywords from different test cases
            "用户 权限 管理",    # Multiple Chinese keywords
        ]
        
        for query in test_queries:
            print(f"\nSearching for: '{query}'")
            try:
                results = index_manager.search_testcases(query)
                print(f"Found {len(results)} results:")
                for result in results:
                    print(f"  - {result['name']}")
                
                # Show search terms preparation
                terms = index_manager._prepare_chinese_search_terms(query)
                print(f"  Prepared search terms: {terms}")
                
            except Exception as e:
                print(f"  Error: {e}")
        
        print("\n=== Single Keyword Comparison ===")
        # Compare with single keyword search
        single_queries = ["用户", "登录", "权限", "User", "Test"]
        
        for query in single_queries:
            print(f"\nSingle keyword search: '{query}'")
            results = index_manager.search_testcases(query)
            print(f"Found {len(results)} results")
            
            terms = index_manager._prepare_chinese_search_terms(query)
            print(f"Prepared search terms: {terms}")
        
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(test_dir)
        print(f"\nCleaned up test directory: {test_dir}")

if __name__ == "__main__":
    test_space_separated_search()