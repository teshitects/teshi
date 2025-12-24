#!/usr/bin/env python3
"""
Debug AND logic for space-separated keyword search
"""

import os
import tempfile
from teshi.utils.testcase_index_manager import TestCaseIndexManager

def test_and_logic_debug():
    """Debug AND logic behavior"""
    print("=== Debug AND Logic ===")
    
    # Create temporary directory for testing
    test_dir = tempfile.mkdtemp(prefix="teshi_and_debug_")
    
    try:
        # Create simple test file
        test_md_file = os.path.join(test_dir, "test.md")
        with open(test_md_file, 'w', encoding='utf-8') as f:
            f.write("""# Test Cases

## Test Case Name
登录功能

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
注册功能

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
用户管理

### Number
TC003

### Preconditions
管理员权限

### Operation Steps
用户管理操作

### Expected Results
管理成功
""")
        
        # Initialize index manager
        index_manager = TestCaseIndexManager(test_dir)
        index_manager.build_index()
        
        # Test queries
        queries = ["登录", "注册", "用户", "管理", "用户 登录", "用户 管理", "登录 管理"]
        
        for query in queries:
            print(f"\n--- Query: '{query}' ---")
            
            # Show prepared terms
            terms = index_manager._prepare_chinese_search_terms(query)
            print(f"Prepared terms: {terms}")
            
            # Show FTS query if it's space-separated
            if ' ' in query:
                keywords = [kw.strip() for kw in query.split() if kw.strip()]
                if len(keywords) > 1:
                    keyword_queries = []
                    for keyword in keywords:
                        keyword_terms = index_manager._prepare_chinese_search_terms(keyword)
                        keyword_query = " OR ".join([f'"{term}"' for term in keyword_terms])
                        keyword_queries.append(f"({keyword_query})")
                    fts_query = " AND ".join(keyword_queries)
                    print(f"FTS query: {fts_query}")
            
            # Get results
            results = index_manager.search_testcases(query)
            print(f"Results ({len(results)}):")
            for result in results:
                print(f"  - {result['name']}")
        
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(test_dir)

if __name__ == "__main__":
    test_and_logic_debug()