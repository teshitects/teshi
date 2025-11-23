from teshi.utils.excel_parser import ExcelParser


class TestExcelParser:
    def setup_class(self):
        self.excel_parser = ExcelParser("tests/utils/test_excel_parser.xlsx")

    def test_parse_excel(self):
        self.excel_parser.parse()
        assert len(self.excel_parser.rows) == 9