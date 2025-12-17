#!/usr/bin/env python3
"""
Check test case directory
"""

import os
import sys

def check_directory():
    """Check test case directory"""
    
    # Target directory
    target_dir = r"C:\Users\lilin\OneDrive\文档\测试用例\Enhook"
    
    print(f"Check directory: {target_dir}")
    
    # Check if the directory exists
    if not os.path.exists(target_dir):
        print(f"[ERROR] Directory does not exist: {target_dir}")
        return
    
    if not os.path.isdir(target_dir):
        print(f"[ERROR] Path is not a directory: {target_dir}")
        return
    
    print(f"[OK] Directory exists")
    
    # Search all Markdown files recursively
    md_files = []
    try:
        for root, dirs, files in os.walk(target_dir):
            level = root.replace(target_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                file_path = os.path.join(root, file)
                if file.lower().endswith('.md'):
                    md_files.append(file_path)
                    print(f"{subindent}[FILE] {file} (Markdown)")
                else:
                    print(f"{subindent}[FILE] {file}")
        
        print(f"\n[INFO] Found {len(md_files)} Markdown files:")
        
        print(f"\n[INFO] Found {len(md_files)} Markdown files:")
        for md_file in md_files:
            file_path = os.path.join(target_dir, md_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    print(f"  - {md_file} ({len(lines)} lines)")
                    
                    # Check whether test case format is included
                    if '## Test case name' in content:
                        print(f"    [OK] Contains standard test case format")
                    elif '# ' in content:
                        print(f"    [WARN] Contains H1 header, format may not match")
                    else:
                        print(f"    [INFO] Standard format not detected")
                        
            except Exception as e:
                print(f"    [ERROR] Read failed: {e}")
    
    except Exception as e:
        print(f"[ERROR] Failed to list directory contents: {e}")
    
    # Test the working of the index manager in this directory
    print(f"\n[INFO] Testing index functionality...")
    try:
        from teshi.utils.testcase_index_manager import TestCaseIndexManager
        
        index_manager = TestCaseIndexManager(target_dir)
        
        print("Build index...")
        count = index_manager.build_index(force_rebuild=True)
        print(f"Processed {count} files")
        
        stats = index_manager.get_statistics()
        print(f"Statistics: {stats}")
        
        # Get all test cases
        all_testcases = index_manager.get_all_testcases()
        print(f"Number of indexed test cases: {len(all_testcases)}")
        for tc in all_testcases:
            print(f"  - {tc['name']}")
    
    except Exception as e:
        print(f"[ERROR] Index test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_directory()