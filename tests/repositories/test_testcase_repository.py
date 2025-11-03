import time

import pytest
import os
from models.testcase_model import TestCaseModel
from repositories.testcase_repository import TestCaseRepository


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

