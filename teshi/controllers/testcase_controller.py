from teshi.repositories.testcase_repository import TestCaseRepository
from teshi.utils.excel_parser import ExcelParser
# from utils.testcase_parser import TestCaseParser

class TestCaseController:
    def __init__(self):
        super().__init__()
        self.testcase_repo = TestCaseRepository()
        self.testcase_list_rows = []

    def load_test_cases_file(self, file_path):
        excel_parser = ExcelParser(file_path)
        excel_parser.parse()
        self.testcase_list_rows = excel_parser.rows

    def get_specific_row(self, row_index):
        """ Get row data to field mapping"""
        return self.testcase_list_rows[row_index-1]

    def import_test_cases(self, start_row=3, field_mapping=None):
        self.testcase_repo.import_testcases(self.testcase_list_rows, start_row=start_row, field_mapping=None)
