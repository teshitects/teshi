import re
from typing import Dict, List, Optional


class BDDConverter:
    """Convert test cases from standard format to BDD (Gherkin) format"""
    
    def __init__(self):
        pass
    
    def convert_to_bdd(self, content: str) -> str:
        """
        Convert standard test case format to BDD format
        
        Args:
            content: Raw test case content in standard format
            
        Returns:
            BDD formatted test case content
        """
        # Parse the test cases
        test_cases = self._parse_test_cases(content)
        
        # Convert to BDD format
        bdd_content = ""
        for i, test_case in enumerate(test_cases, 1):
            bdd_content += self._convert_single_test_case(test_case, i)
            if i < len(test_cases):
                bdd_content += "\n\n---\n\n"
        
        return bdd_content
    
    def _parse_test_cases(self, content: str) -> List[Dict]:
        """Parse test cases from markdown content"""
        # Split by horizontal separators if present to handle multiple test cases
        sections = re.split(r'\n---\n', content)
        test_cases = []
        
        for section in sections:
            if section.strip():
                test_case = self._parse_single_test_case(section)
                if test_case:
                    test_cases.append(test_case)
                    
        return test_cases
    
    def _parse_single_test_case(self, content: str) -> Optional[Dict]:
        """Parse a single test case from content"""
        lines = content.strip().split('\n')
        if not lines:
            return None
        
        test_case = {
            'title': '',
            'preconditions': [],
            'steps': [],
            'expected_results': [],
            'notes': ''
        }
        
        current_section = None
        title_found = False
        test_case_name_line_index = -1
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Check for sections first (support both English and Chinese)
            if line.startswith('## ') or line.startswith('# '):
                section_name = line[3:].lower()
                
                # Chinese section names
                if '前置条件' in section_name:
                    current_section = 'preconditions'
                    continue
                elif '操作步骤' in section_name:
                    current_section = 'steps'
                    continue
                elif '预期结果' in section_name:
                    current_section = 'expected_results'
                    continue
                elif '备注' in section_name:
                    current_section = 'notes'
                    continue
                # English section names
                elif 'precondition' in section_name:
                    current_section = 'preconditions'
                    continue
                elif 'operation' in section_name or 'step' in section_name:
                    current_section = 'steps'
                    continue
                elif 'expected' in section_name or 'result' in section_name:
                    current_section = 'expected_results'
                    continue
                elif 'note' in section_name:
                    current_section = 'notes'
                    continue
                
                # Check for title (support both "# Title" and "## 测试用例名称")
                if not title_found:
                    # Remove all # characters and get the title
                    title = re.sub(r'^#+\s*', '', line)
                    
                    # Skip if this is a section header like "## 测试用例名称"
                    if not any(keyword in title.lower() for keyword in ['测试用例名称', '编号', 'precondition', 'step', 'operation', 'expected', 'result', 'note']):
                        test_case['title'] = title
                        title_found = True
                    elif '测试用例名称' in title:
                        test_case_name_line_index = i
                continue
            
            # Add content to current section
            if current_section and line:
                if current_section in ['preconditions', 'steps', 'expected_results']:
                    # Extract and preserve numbered list prefix
                    match = re.match(r'^(\d+[、.]\s*)(.*)', line)
                    if match:
                        number_prefix = match.group(1)
                        content = match.group(2).strip()
                        # Store both the original line with number and the clean content
                        test_case[current_section].append({
                            'original': line.strip(),
                            'content': content,
                            'number': number_prefix
                        })
                    else:
                        # Handle lines without numbers
                        test_case[current_section].append({
                            'original': line.strip(),
                            'content': line.strip(),
                            'number': ''
                        })
                elif current_section == 'notes':
                    test_case['notes'] += line + ' '
        
        # If no title found, try to extract from "测试用例名称" section
        if not title_found and test_case_name_line_index >= 0:
            # Look for the next non-empty line as title
            for j in range(test_case_name_line_index + 1, len(lines)):
                next_line = lines[j].strip()
                if next_line and not next_line.startswith('#'):
                    test_case['title'] = next_line
                    title_found = True
                    break
        
        # Clean up notes
        test_case['notes'] = test_case['notes'].strip()
        
        # If still no title, create one from available content
        if not title_found and (test_case['steps'] or test_case['preconditions'] or test_case['expected_results']):
            test_case['title'] = "Test Case"
            title_found = True
        
        return test_case if title_found else None
    
    def _convert_single_test_case(self, test_case: Dict, index: int) -> str:
        """Convert a single test case to BDD format with step-result correspondence"""
        bdd = f"  Scenario: {test_case['title']}\n"
        
        # Add preconditions as Given statements
        if test_case['preconditions']:
            for i, precondition in enumerate(test_case['preconditions']):
                if isinstance(precondition, dict):
                    content = precondition['content']
                    number = precondition['number']
                else:
                    # Handle legacy format
                    content = precondition
                    number = f"{i+1}. "
                
                if i == 0:
                    bdd += f"    Given {number}{content}\n"
                else:
                    bdd += f"    And {number}{content}\n"
        
        # Add operation steps and expected results in corresponding order
        if test_case['steps'] or test_case['expected_results']:
            steps_count = len(test_case['steps'])
            results_count = len(test_case['expected_results'])
            max_count = max(steps_count, results_count)
            
            first_step_added = False
            first_result_added = False
            
            for i in range(max_count):
                # Add step with When/And
                if i < steps_count:
                    step = test_case['steps'][i]
                    if isinstance(step, dict):
                        content = step['content']
                        number = step['number']
                    else:
                        # Handle legacy format
                        content = step
                        number = f"{i+1}. "
                    
                    if not first_step_added:
                        bdd += f"    When {number}{content}\n"
                        first_step_added = True
                    else:
                        bdd += f"    When {number}{content}\n"
                
                # Add corresponding expected result with Then/And
                if i < results_count:
                    result = test_case['expected_results'][i]
                    if isinstance(result, dict):
                        content = result['content']
                        number = result['number']
                    else:
                        # Handle legacy format
                        content = result
                        number = f"{i+1}. "
                    
                    if not first_result_added:
                        bdd += f"    Then {number}{content}\n"
                        first_result_added = True
                    else:
                        bdd += f"    Then {number}{content}\n"
        
        # Add notes as comments if present
        if test_case['notes']:
            clean_notes = test_case['notes'].replace('---', '').strip()
            bdd += f"\n    # Notes: {clean_notes}\n"
        
        return bdd
    
    def convert_to_standard(self, bdd_content: str) -> str:
        """
        Convert BDD format back to standard test case format
        
        Args:
            bdd_content: BDD formatted content
            
        Returns:
            Standard test case format content
        """
        # Parse BDD scenarios
        scenarios = self._parse_bdd_scenarios(bdd_content)
        
        # Convert back to standard format
        standard_content = ""
        for i, scenario in enumerate(scenarios, 1):
            standard_content += self._convert_bdd_to_standard(scenario)
            if i < len(scenarios):
                standard_content += "\n\n---\n\n"
        
        return standard_content
    
    def _parse_bdd_scenarios(self, content: str) -> List[Dict]:
        """Parse BDD scenarios from content"""
        scenarios = []
        # Split by scenario boundaries, accounting for leading spaces
        sections = re.split(r'\n(?:---\n)?\s*(?=Scenario:)', content)
        
        for section in sections:
            section = section.strip()
            if section and section.startswith('Scenario:'):
                scenario = self._parse_single_scenario(section)
                if scenario:
                    scenarios.append(scenario)
        
        return scenarios
    
    def _parse_single_scenario(self, content: str) -> Optional[Dict]:
        """Parse a single BDD scenario"""
        lines = content.split('\n')
        if not lines:
            return None
        
        scenario = {
            'title': '',
            'given': [],
            'when': [],
            'then': [],
            'notes': ''
        }
        
        for line in lines:
            line = line.strip()
            
            # Check for scenario title
            if line.startswith('Scenario:'):
                scenario['title'] = line[9:].strip()
                continue
            
            # Check for Gherkin keywords
            if line.startswith('Given '):
                scenario['given'].append(line[5:].strip())
            elif line.startswith('When '):
                scenario['when'].append(line[5:].strip())
            elif line.startswith('Then '):
                scenario['then'].append(line[5:].strip())
            elif line.startswith('And '):
                # Determine which section this "And" belongs to
                if scenario['when']:
                    if not scenario['then']:
                        scenario['when'].append(line[4:].strip())
                    else:
                        scenario['then'].append(line[4:].strip())
                elif scenario['given']:
                    scenario['given'].append(line[4:].strip())
            elif line.startswith('# Notes:'):
                scenario['notes'] = line[9:].strip()
        
        return scenario if scenario['title'] else None
    
    def _convert_bdd_to_standard(self, scenario: Dict) -> str:
        """Convert a BDD scenario back to standard format"""
        standard = f"# {scenario['title']}\n\n"
        
        # Preconditions (Given statements)
        if scenario['given']:
            standard += "## Preconditions\n"
            for i, given in enumerate(scenario['given'], 1):
                standard += f"{i}. {given}\n"
            standard += "\n"
        
        # Operation Steps (When statements)
        if scenario['when']:
            standard += "## Operation Steps\n"
            for i, when in enumerate(scenario['when'], 1):
                standard += f"{i}. {when}\n"
            standard += "\n"
        
        # Expected Results (Then statements)
        if scenario['then']:
            standard += "## Expected Results\n"
            for i, then in enumerate(scenario['then'], 1):
                standard += f"{i}. {then}\n"
            standard += "\n"
        
        # Notes
        if scenario['notes']:
            standard += "## Notes\n"
            standard += scenario['notes'] + "\n"
        
        return standard