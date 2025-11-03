import os
import sqlite3
from typing import Optional

from models.testcase_model import TestCaseModel


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


    def create_testcase(self, testcase: TestCaseModel) -> None:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO testcases VALUES (
                :uuid, :name, :number, :preconditions, :steps, :expected_results,
                :notes, :priority, :domain, :stage, :feature, :automate, :tags, :extras
            )
        """, testcase.__dict__)
        self.conn.commit()

    def get_testcase_by_id(self, uuid: str) -> Optional[TestCaseModel]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM testcases WHERE uuid = ?", (uuid,))
        row = cursor.fetchone()
        if row:
            return TestCaseModel(*row)
        return None

    def close(self):
        self.conn.close()
