#!/usr/bin/env python3
"""
Test AND logic for space-separated keyword search
"""

import os
import tempfile
from teshi.utils.testcase_index_manager import TestCaseIndexManager

def test_and_logic_search():
    """Test AND logic for space-separated keywords"""
    print("=== Testing AND Logic for Space-Separated Search ===")
    
    # Create temporary directory for testing
    test_dir = tempfile.mkdtemp(prefix="teshi_and_logic_search_")
    
    try:
        # Create test file with specific content to test AND logic
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
2. 输入用户名密码
3. 点击登录按钮

### Expected Results
成功登录系统

---

## Test Case Name
用户注册功能测试

### Number
TC002

### Preconditions
新用户未注册

### Operation Steps
1. 打开注册页面
2. 填写用户信息
3. 提交注册表单

### Expected Results
成功创建用户账号

---

## Test Case Name
管理员权限管理

### Number
TC003

### Preconditions
管理员已登录

### Operation Steps
1. 进入权限管理
2. 设置用户权限
3. 保存权限配置

### Expected Results
权限管理生效

---

## Test Case Name
用户个人资料修改

### Number
TC004

### Preconditions
用户已登录

### Operation Steps
1. 进入个人中心
2. 修改个人资料
3. 保存修改

### Expected Results
资料更新成功
""")
        
        # Initialize index manager
        index_manager = TestCaseIndexManager(test_dir)
        index_manager.build_index()
        
        print("\n=== Testing AND Logic with Space-Separated Keywords ===")
        
        # Test cases for AND logic
        test_cases = [
            ("用户 登录", "Should return only test cases with both '用户' and '登录'"),
            ("用户 注册", "Should return only test cases with both '用户' and '注册'"),
            ("管理员 权限", "Should return only test cases with both '管理员' and '权限'"),
            ("用户 权限", "Should return test cases with both '用户' and '权限' (TC003, TC004)"),
            ("登录 权限", "Should return test cases with both '登录' and '权限' (TC003)"),
        ]
        
        for query, description in test_cases:
            print(f"\nQuery: '{query}'")
            print(f"Expected: {description}")
            
            try:
                results = index_manager.search_testcases(query)
                print(f"Found {len(results)} results:")
                for result in results:
                    print(f"  - {result['name']}")
                
                # Also test individual keywords for comparison
                keywords = query.split()
                print("Individual keyword results:")
                for keyword in keywords:
                    individual_results = index_manager.search_testcases(keyword.strip())
                    keyword_names = [r['name'] for r in individual_results]
                    print(f"  '{keyword}': {len(individual_results)} results - {keyword_names}")
                
            except Exception as e:
                print(f"  Error: {e}")
        
        print("\n=== Testing Precision Comparison ===")
        # Compare precision between OR and AND logic
        precision_queries = [
            "用户 登录",
            "用户 注册", 
            "管理员 权限"
        ]
        
        for query in precision_queries:
            print(f"\nPrecision test for: '{query}'")
            
            # Current AND logic results
            and_results = index_manager.search_testcases(query)
            and_names = [r['name'] for r in and_results]
            
            # Test what OR logic would return (by searching individual keywords and combining)
            keywords = [kw.strip() for kw in query.split()]
            all_or_results = set()
            for keyword in keywords:
                keyword_results = index_manager.search_testcases(keyword)
                for result in keyword_results:
                    all_or_results.add(result['name'])
            
            or_names = list(all_or_results)
            
            print(f"  AND logic ({len(and_results)}): {and_names}")
            print(f"  OR logic ({len(or_names)}): {or_names}")
            
            if len(and_names) < len(or_names):
                print(f"  [OK] AND logic is more precise by {len(or_names) - len(and_names)} results")
            elif len(and_names) == len(or_names):
                print(f"  [=] Both logics return same number of results")
            else:
                print(f"  [WARNING] AND logic returns more results than OR (unexpected)")
        
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(test_dir)
        print(f"\nCleaned up test directory: {test_dir}")

if __name__ == "__main__":
    test_and_logic_search()