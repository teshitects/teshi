#!/usr/bin/env python3
"""Test Chinese search functionality with n-gram tokenizer"""

import os
import tempfile
import sqlite3
from teshi.utils.testcase_index_manager import TestCaseIndexManager


def test_chinese_ngram_search():
    """Test Chinese search with 1-gram and 2-gram support"""
    print("Testing Chinese n-gram search functionality...")
    
    # Create temporary directory for test
    test_dir = tempfile.mkdtemp(prefix="teshi_chinese_search_")
    
    try:
        # Create test case file with Chinese content
        test_file = os.path.join(test_dir, "test_chinese.md")
        chinese_content = """# 测试用例名称

用户登录功能测试

# 前置条件

1. 系统已部署完成
2. 用户账户已创建

# 操作步骤

1. 打开登录页面
2. 输入用户名和密码
3. 点击登录按钮

# 预期结果

1. 登录成功
2. 跳转到首页

# 备注

测试正常登录流程
"""
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(chinese_content)
        
        # Initialize index manager
        index_manager = TestCaseIndexManager(test_dir)
        
        # Build index
        print("Building index...")
        index_manager.build_index(force_rebuild=True)
        
        # Test various Chinese search queries
        test_queries = [
            "登录",           # Single word
            "用户",           # Single character  
            "用户登录",       # Two characters
            "登录功能",       # Mixed words
            "系统",           # Single character
            "部署",           # Single character
            "首页",           # Two characters
            "测试",           # Common word
            "流程",           # Single word
            "正常",           # Single word
        ]
        
        print("\n=== Chinese Search Tests ===")
        for query in test_queries:
            print(f"\nSearching for: '{query}'")
            try:
                results = index_manager.search_testcases(query)
                print(f"  Found {len(results)} results")
                
                for i, result in enumerate(results):
                    print(f"    Result {i+1}: {result['name']}")
                    if result.get('name_snippet') and result['name_snippet'] != result['name']:
                        print(f"      Snippet: {result['name_snippet']}")
                        
            except Exception as e:
                print(f"  Search error: {e}")
        
        # Test partial matches
        print("\n=== Partial Match Tests ===")
        partial_queries = ["登", "录", "用", "户", "功", "能"]
        
        for query in partial_queries:
            print(f"\nSearching for single character: '{query}'")
            try:
                results = index_manager.search_testcases(query)
                print(f"  Found {len(results)} results")
                
                if results:
                    for i, result in enumerate(results[:2]):  # Show first 2 results
                        print(f"    Result {i+1}: {result['name']}")
                        
            except Exception as e:
                print(f"  Search error: {e}")
        
        print("\n[SUCCESS] Chinese search tests completed!")
        
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)


def test_search_terms_preparation():
    """Test the search terms preparation function"""
    print("\n=== Testing Search Terms Preparation ===")
    
    from teshi.utils.testcase_index_manager import TestCaseIndexManager
    index_manager = TestCaseIndexManager(tempfile.mkdtemp())
    
    test_cases = [
        "用户登录",           # Chinese two characters
        "登录功能测试",       # Chinese mixed words  
        "用户login功能",      # Mixed Chinese and English
        "Login功能",         # Mixed English and Chinese
        "测试",              # Single Chinese word
        "test",              # Single English word
        "用户登录测试功能",   # Long Chinese phrase
    ]
    
    for query in test_cases:
        terms = index_manager._prepare_chinese_search_terms(query)
        print(f"Query: '{query}' -> Terms: {terms}")


if __name__ == "__main__":
    test_search_terms_preparation()
    test_chinese_ngram_search()