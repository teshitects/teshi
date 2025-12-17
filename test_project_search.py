#!/usr/bin/env python3
"""
Test search functionality with actual data in project
"""

import os
import sys

# Add project path to system path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from teshi.utils.testcase_index_manager import TestCaseIndexManager

def test_project_search():
    """Test actual search functionality in project"""
    
    # Use test data from project
    project_path = os.getcwd()
    index_manager = TestCaseIndexManager(project_path)
    
    try:
        # Rebuild index
        print('Building index for project...')
        count = index_manager.build_index(force_rebuild=True)
        print(f'Processed {count} files')
        
        # Get statistics
        stats = index_manager.get_statistics()
        print(f'Statistics: {stats}')
        
        # Test search
        test_queries = ['Login', 'Register', 'System', 'User', 'Function']
        
        for query in test_queries:
            results = index_manager.search_testcases(query)
            print(f'Search "{query}": {len(results)} results')
            for result in results[:3]:  # Show only first 3 results
                print(f'  - {result["name"]}')
            if len(results) > 3:
                print(f'  ... and {len(results) - 3} more')
        
    except Exception as e:
        print(f'Test failed: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_project_search()