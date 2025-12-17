#!/usr/bin/env python3
"""Enhanced Chinese and English mixed search tests"""

import os
import tempfile
from teshi.utils.testcase_index_manager import TestCaseIndexManager


def test_mixed_language_search():
    """Test mixed Chinese and English search functionality"""
    print("Testing mixed Chinese-English search...")
    
    # Create temporary directory for test
    test_dir = tempfile.mkdtemp(prefix="teshi_mixed_search_")
    
    try:
        # Create test case file with mixed content
        test_file = os.path.join(test_dir, "test_mixed.md")
        mixed_content = """# 测试用例名称

User Login Function Test 用户登录功能测试

# 前置条件

1. 系统已部署完成 System deployed
2. 用户账户已创建 User account created

# 操作步骤

1. 打开登录页面 Open login page
2. 输入用户名和密码 Enter username and password
3. 点击登录按钮 Click login button

# 预期结果

1. 登录成功 Login successful
2. 跳转到首页 Redirect to homepage

# 备注

测试正常登录流程 Test normal login process
"""
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(mixed_content)
        
        # Initialize index manager
        index_manager = TestCaseIndexManager(test_dir)
        
        # Build index
        print("Building index for mixed content...")
        index_manager.build_index(force_rebuild=True)
        
        # Test mixed search queries
        test_queries = [
            # Chinese queries
            "用户登录",
            "登录功能", 
            "系统部署",
            "测试流程",
            
            # English queries
            "Login",
            "User",
            "System",
            "Test",
            
            # Mixed queries
            "用户 Login",
            "登录 Function",
            "System 部署",
            "Test 流程",
            
            # Partial queries
            "登",
            "Log",
            "用",
            "sys",
        ]
        
        print("\n=== Mixed Language Search Tests ===")
        for query in test_queries:
            print(f"\nSearching for: '{query}'")
            try:
                results = index_manager.search_testcases(query)
                print(f"  Found {len(results)} results")
                
                if results:
                    # Show first result with snippets
                    result = results[0]
                    print(f"    Name: {result['name']}")
                    if result.get('name_snippet') and result['name_snippet'] != result['name']:
                        print(f"    Snippet: {result['name_snippet']}")
                        
            except Exception as e:
                print(f"  Search error: {e}")
        
        print("\n[SUCCESS] Mixed language search tests completed!")
        
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    test_mixed_language_search()