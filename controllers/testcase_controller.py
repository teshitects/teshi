import os

from repositories.testcase_repository import TestCaseRepository
from utils.excel_parser import ExcelParser
# from utils.testcase_parser import TestCaseParser

class TestCaseController:
    def __init__(self):
        super().__init__()
        self.testcase_repo = TestCaseRepository()
        self.testcase_list = []

    def import_test_cases(self, file_path):
        # 1. Parse the test case file


        # 2. Import test case to database
        # 3. Update the left panel

        pass

