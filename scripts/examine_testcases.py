#!/usr/bin/env python3
"""
Check test case file content and format
"""

import os
import sys

def examine_testcases():
    """Check test case files"""
    
    target_dir = r"C:\Users\lilin\OneDrive\文档\测试用例\Enhook"
    
    print(f"Checking directory: {target_dir}")
    
    # Find all Markdown files
    md_files = []
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if file.lower().endswith('.md'):
                md_files.append(os.path.join(root, file))
    
    print(f"\nFound {len(md_files)} Markdown files:")
    
    for md_file in md_files:
        print(f"\n=== {md_file} ===")
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            print(f"File size: {len(content)} characters, {len(lines)} lines")
            
            # Display first few lines
            print("First 10 lines:")
            for i, line in enumerate(lines[:10]):
                print(f"  {i+1:2d}: {line}")
            
            if len(lines) > 10:
                print("  ...(more content)")
            
            # Check format
            has_standard_format = '## Test Case Name' in content
            has_h1_headers = any(line.strip().startswith('# ') for line in lines)
            
            print(f"Format check:")
            print(f"  Standard format(## Test Case Name): {'YES' if has_standard_format else 'NO'}")
            print(f"  H1 header format: {'YES' if has_h1_headers else 'NO'}")
            
            # Parse test case count
            if has_standard_format:
                import re
                testcases = re.findall(r'## Test Case Name\s*\n\s*\n([^\n#]+)', content)
                print(f"  Detected test cases count: {len(testcases)}")
                for i, tc in enumerate(testcases[:3]):  # Only show first 3
                    print(f"    {i+1}. {tc.strip()}")
                if len(testcases) > 3:
                    print(f"    ...{len(testcases) - 3} more")
            
        except Exception as e:
            print(f"Read failed: {e}")
    
    # Test search functionality
    print(f"\n=== Testing search functionality ===")
    try:
        from teshi.utils.testcase_index_manager import TestCaseIndexManager
        
        index_manager = TestCaseIndexManager(target_dir)
        
        # Don't rebuild index, use existing one
        stats = index_manager.get_statistics()
        print(f"Current index statistics: {stats}")
        
        # Test search
        test_queries = ['Store', 'Library', 'HomePage', 'Software', 'Internationalization', 'CPU']
        
        for query in test_queries:
            results = index_manager.search_testcases(query)
            print(f"Search '{query}': {len(results)} results")
            for result in results:
                print(f"  - {result['name']}")
    
    except Exception as e:
        print(f"Search test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    examine_testcases()