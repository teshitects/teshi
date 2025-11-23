import pytest
import os
from teshi.models.testcase_model import TestCaseModel
from teshi.repositories.testcase_repository import TestCaseRepository


class TestTestCaseRepository:
    def setup_method(self, method):
        """Setup test resources."""
        self.db_path = "test_testcase.db"
        self.repo = TestCaseRepository(self.db_path)

    def teardown_method(self, method):
        """Clean up test resources."""
        if hasattr(self, 'repo') and self.repo:
            self.repo.close()
            os.remove(self.db_path)

    def test_create_testcase(self):
        """Test creating a test case in the repository."""
        testcase = TestCaseModel(
            uuid="test-uuid",
            name="Test Case",
            number="TC001",
            preconditions="Preconditions",
            steps="Steps",
            expected_results="Expected Results",
            notes="Notes",
            priority="High",
            domain="Domain",
            stage="Stage",
            feature="Feature",
            automate=True,
            tags="tag1,tag2",
            extras="Extras"
        )
        self.repo.create_testcase(testcase)

        # Verify the test case was created
        retrieved_testcase = self.repo.get_testcase_by_id("test-uuid")
        assert retrieved_testcase is not None
        assert retrieved_testcase.name == "Test Case"

    def test_import_testcases(self):
        testcases = [
            [".", None, "uuid0", "name0", "number0", "preconditions0", "steps0", "expected_results0", "notes0",
             "priority0", "domain0", "stage0", "automate0", "tags0", "extras0"],
            [".", "folder1", None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            ["..", None, "uuid11", "name11", "number11", "preconditions11", "steps11", "expected_results11", "notes11",
             "priority11", "domain11", "stage11", "automate11", "tags11", "extras11"],
            ["..", None, "uuid12", "name12", "number12", "preconditions12", "steps12", "expected_results12", "notes12",
             "priority12", "domain12", "stage12", "automate12", "tags12", "extras12"],
            ["..", "folder11", None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            ["...", None, "uuid111", "name111", "number111", "preconditions111", "steps111", "expected_results111", "notes111",
             "priority111", "domain111", "stage111", "automate111", "tags111", "extras111"],
            [".", "folder2", None, None, None, None, None, None, None, None, None, None, None, None, None, None],
        ]

        ret_list = self.repo._import_testcases(testcases)

        assert ret_list[0][1] == "Feature" and ret_list[0][3] == "name0"
        assert ret_list[1][1] == "folder1" and ret_list[1][3] == "name11"
        assert ret_list[2][1] == "folder1" and ret_list[2][3] == "name12"
        assert ret_list[3][1] == "folder11" and ret_list[3][3] == "name111"
