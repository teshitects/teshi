import os
import sqlite3
from typing import Optional

from teshi.models.testcase_model import TestCaseModel


class TestCaseRepository:
    def __init__(self, db_path: str="testcase.db"):
        self.db_path = db_path
        if not os.path.exists(self.db_path):
            self.conn = sqlite3.connect(self.db_path)
            self._create_table()
        else:
            self.conn = sqlite3.connect(self.db_path)
            print(os.path.exists(self.db_path))

    def _create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS testcases (
                uuid TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                number TEXT NOT NULL,
                preconditions TEXT,
                steps TEXT,
                expected_results TEXT,
                notes TEXT,
                priority TEXT,
                domain TEXT,
                stage TEXT,
                feature TEXT,
                automate BOOLEAN,
                tags TEXT,
                extras TEXT
            )
        """)
        self.conn.commit()

    def _import_testcases(self, testcases):
        """
        Import test cases from a list and organize them by feature hierarchy

        Args:
            testcases: List of test cases where each test case is represented as
            [level, feature, uuid, name, number, preconditions, steps, expected_results, notes,
            priority, domain, stage, automate, tags, extras]

        Returns:
            List of processed test cases with proper feature assignments
        """

        folder_list = [["Feature","1"]]
        testcase_list = []
        cur_level = 1
        for testcase in testcases:
            level = len(testcase[0])
            feature = testcase[1]

            if level < cur_level:
                folder_list.pop(-1)
                cur_level -= 1

            if level >= cur_level:
                if feature == None:
                    testcase[1] = folder_list[-1][0]
                    testcase_list.append(testcase)
                else:
                    folder_list.append([feature, level])

            cur_level = level
        return testcase_list


    def get_testcase_by_id(self, uuid: str) -> Optional[TestCaseModel]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM testcases WHERE uuid = ?", (uuid,))
        row = cursor.fetchone()
        if row:
            return TestCaseModel(*row)
        return None


    def close(self):
        self.conn.close()

    def import_testcases(self, testcase_list_rows, start_row, field_mapping):
        pass
