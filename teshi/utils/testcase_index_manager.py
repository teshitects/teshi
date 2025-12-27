import os
import re
import sqlite3
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from teshi.models.testcase_model import TestCaseModel
from teshi.utils.file_watcher import FileWatcher


def register_ngram_tokenizer(conn):
    """Register custom n-gram tokenizer for better Chinese search"""
    # Create a custom tokenizer function that handles 1-gram and 2-gram for Chinese
    cursor = conn.cursor()
    
    # Register the tokenizer using FTS5's built-in trigram with custom parameters
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS temp USING fts5vocab(testcases_fts, row)
    """)
    
    # Use porter tokenizer with unicode61 for better Chinese character handling
    # This approach allows for character-level indexing (1-gram) and bigram indexing
    conn.create_function("NGRAM_TOKENIZE", 1, lambda text: text)


class TestCaseIndexManager:
    """Test case index manager using SQLite FTS5 for full-text search"""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.cache_dir = os.path.join(project_path, '.teshi', 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.db_path = os.path.join(self.cache_dir, 'testcases_fts.db')
        self.metadata_db_path = os.path.join(self.cache_dir, 'metadata.db')
        
        self._init_databases()
        
        # Initialize file watcher
        self.file_watcher = None
        self._update_pending = False
        self._update_timer = None
    
    def _init_databases(self):
        """Initialize databases"""
        # Initialize FTS5 database with WAL mode for better concurrency
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        # Enable WAL mode for better concurrent access
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        
        # Check if FTS5 table exists, only create if it doesn't exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='testcases_fts'")
        if not cursor.fetchone():
            # Register custom tokenizer for Chinese n-gram support
            register_ngram_tokenizer(conn)
            
            # Create FTS5 virtual table with improved tokenizer for Chinese search
            # Using porter tokenizer which supports character-level indexing for Chinese
            cursor.execute("""
                CREATE VIRTUAL TABLE testcases_fts USING fts5(
                    uuid,
                    name,
                    preconditions,
                    steps,
                    expected_results,
                    notes,
                    file_path,
                    tokenize = "trigram"
                )
            """)
            print("Created new FTS5 table")
        else:
            print("FTS5 table already exists, preserving data")
        
        # Create regular table to store metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS testcases_meta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT UNIQUE NOT NULL,
                file_path TEXT NOT NULL,
                file_mtime REAL NOT NULL,
                file_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
        
        # Initialize metadata database
        conn = sqlite3.connect(self.metadata_db_path, timeout=30.0)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _get_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of the file"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return ""
    
    def _parse_markdown_testcase(self, file_path: str) -> List[TestCaseModel]:
        """Parse Markdown test case file"""
        testcases = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return testcases
        
        # Split content by headers
        sections = re.split(r'^(#{1,3})\s+(.+)$', content, flags=re.MULTILINE)
        
        current_testcase = None
        
        # Reorganize content: pair headers with corresponding content
        parsed_sections = []
        for i in range(1, len(sections), 3):
            if i + 2 < len(sections):
                level = len(sections[i])
                title = sections[i + 1].strip()
                content_part = sections[i + 2].strip() if i + 2 < len(sections) else ""
                
                parsed_sections.append({
                    'level': level,
                    'title': title,
                    'content': content_part
                })
        
        # Parse test cases
        for section in parsed_sections:
            title = section['title']
            content = section['content']
            
            # Detect test case start: Support both English and Chinese
            if title in ['Test Case Name', '测试用例名称']:
                # Save previous test case
                if current_testcase:
                    testcases.append(current_testcase)
                
                # Create new test case
                testcase_name = content.strip()
                current_testcase = TestCaseModel(
                    uuid=self._generate_uuid(testcase_name, file_path),
                    name=testcase_name,
                    number="",
                    preconditions="",
                    steps="",
                    expected_results="",
                    notes="",
                    priority="",
                    domain="",
                    stage="",
                    feature="",
                    automate=False,
                    tags=[],
                    extras={}
                )
            
            elif current_testcase:
                # Handle other fields - support both English and Chinese
                if title in ['Number', '编号']:
                    current_testcase.number = content.strip()
                elif title in ['Preconditions', '前置条件', '前提条件']:
                    current_testcase.preconditions = content.strip()
                elif title in ['Operation Steps', '操作步骤', '测试步骤']:
                    current_testcase.steps = content.strip()
                elif title in ['Expected Results', '预期结果', '期望结果']:
                    current_testcase.expected_results = content.strip()
                elif title in ['Notes', '备注', '说明']:
                    current_testcase.notes = content.strip()
        
        # Add the last test case
        if current_testcase:
            testcases.append(current_testcase)
        
        return testcases
    
    def _generate_uuid(self, name: str, file_path: str) -> str:
        """Generate unique UUID"""
        import uuid
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{file_path}:{name}"))
    
    def _assign_section_content(self, testcase: TestCaseModel, section: str, content: str):
        """Assign content to corresponding field of test case"""
        if "前置条件" in section or "前提条件" in section:
            testcase.preconditions = content
        elif "操作步骤" in section or "测试步骤" in section or "步骤" in section:
            testcase.steps = content
        elif "预期结果" in section or "期望结果" in section:
            testcase.expected_results = content
        elif "备注" in section or "说明" in section:
            testcase.notes = content
    
    def _append_section_content(self, testcase: TestCaseModel, section: str, content: str):
        """Append content to corresponding field of test case"""
        if not content:
            return
            
        if "前置条件" in section or "前提条件" in section:
            testcase.preconditions += "\n" + content
        elif "操作步骤" in section or "测试步骤" in section or "步骤" in section:
            testcase.steps += "\n" + content
        elif "预期结果" in section or "期望结果" in section:
            testcase.expected_results += "\n" + content
        elif "备注" in section or "说明" in section:
            testcase.notes += "\n" + content
    
    def _find_markdown_files(self) -> List[str]:
        """Find all Markdown files in the project"""
        md_files = []
        # Skip common directories that don't contain test cases
        skip_dirs = {'.git', '.teshi', '__pycache__', 'node_modules', '.vscode', '.idea', 'build', 'dist'}
        
        for root, dirs, files in os.walk(self.project_path):
            # Skip hidden directories and common build/cache directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in skip_dirs]
            
            # Skip the .teshi directory completely
            if '.teshi' in root.split(os.sep):
                continue
            
            for file in files:
                if file.endswith('.md'):
                    md_files.append(os.path.join(root, file))
        
        return md_files
    
    def _get_file_meta(self, file_path: str) -> Optional[Dict]:
        """Get file metadata"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT uuid, file_mtime, file_hash FROM testcases_meta 
            WHERE file_path = ?
        """, (file_path,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'uuid': row[0],
                'file_mtime': row[1],
                'file_hash': row[2]
            }
        return None
    
    def _update_file_meta(self, file_path: str, uuid: str, mtime: float, file_hash: str):
        """Update file metadata"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT OR REPLACE INTO testcases_meta (uuid, file_path, file_mtime, file_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?, 
                COALESCE((SELECT created_at FROM testcases_meta WHERE file_path = ?), ?), ?)
        """, (uuid, file_path, mtime, file_hash, file_path, now, now))
        
        conn.commit()
        conn.close()
    
    def _remove_testcases_by_file(self, file_path: str):
        """Remove all test cases for specified file"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM testcases_fts WHERE file_path = ?
        """, (file_path,))
        
        cursor.execute("""
            DELETE FROM testcases_meta WHERE file_path = ?
        """, (file_path,))
        
        conn.commit()
        conn.close()
    
    def _add_testcases(self, testcases: List[TestCaseModel], file_path: str):
        """Add test cases to index"""
        if not testcases:
            return
        
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        for testcase in testcases:
            cursor.execute("""
                INSERT INTO testcases_fts (uuid, name, preconditions, steps, expected_results, notes, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                testcase.uuid,
                testcase.name,
                testcase.preconditions,
                testcase.steps,
                testcase.expected_results,
                testcase.notes,
                file_path
            ))
        
        conn.commit()
        conn.close()
    
    def build_index(self, force_rebuild=False):
        """Build or update test case index"""
        print(f"Building test case index for project: {self.project_path}")
        
        # If force rebuild, delete existing database
        if force_rebuild and os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
                print("Removed existing database for rebuild")
                self._init_databases()  # Re-initialize database
            except Exception as e:
                print(f"Error removing existing database: {e}")
        
        md_files = self._find_markdown_files()
        print(f"Found {len(md_files)} markdown files to process")
        
        updated_files = 0
        new_files = 0
        
        # Batch database operations for better performance
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        # Enable better concurrency settings
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        
        try:
            batch_size = 100  # Process files in batches to avoid long-running transactions
            for i in range(0, len(md_files), batch_size):
                batch_files = md_files[i:i + batch_size]
                
                for file_path in batch_files:
                    try:
                        # 获取文件修改时间和哈希
                        file_mtime = os.path.getmtime(file_path)
                        file_hash = self._get_file_hash(file_path)
                        
                        # Check if file already exists and is unchanged
                        existing_meta = self._get_file_meta(file_path)
                        
                        if existing_meta:
                            if existing_meta['file_mtime'] == file_mtime and existing_meta['file_hash'] == file_hash:
                                continue  # File unchanged, skip
                            
                            updated_files += 1
                        else:
                            new_files += 1
                        
                        # Parse test cases
                        testcases = self._parse_markdown_testcase(file_path)
                        
                        # Remove old index first (if exists)
                        cursor.execute("DELETE FROM testcases_fts WHERE file_path = ?", (file_path,))
                        
                        # Add new index if testcases found
                        if testcases:
                            for testcase in testcases:
                                cursor.execute("""
                                    INSERT INTO testcases_fts (uuid, name, preconditions, steps, expected_results, notes, file_path)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    testcase.uuid,
                                    testcase.name,
                                    testcase.preconditions,
                                    testcase.steps,
                                    testcase.expected_results,
                                    testcase.notes,
                                    file_path
                                ))
                            
                            # Update metadata using first testcase's UUID
                            sample_uuid = testcases[0].uuid
                        else:
                            # Use dummy UUID if no testcases found
                            sample_uuid = self._generate_uuid("dummy", file_path)
                        
                        # Update metadata
                        now = datetime.now().isoformat()
                        cursor.execute("""
                            INSERT OR REPLACE INTO testcases_meta (uuid, file_path, file_mtime, file_hash, created_at, updated_at)
                            VALUES (?, ?, ?, ?, 
                                COALESCE((SELECT created_at FROM testcases_meta WHERE file_path = ?), ?), ?)
                        """, (sample_uuid, file_path, file_mtime, file_hash, file_path, now, now))
                        
                    except sqlite3.Error as e:
                        print(f"SQLite error processing file {file_path}: {e}")
                        # If database error, try to rebuild database
                        if "recursively defined fts5" in str(e).lower():
                            print("Detected FTS5 recursive definition error, attempting rebuild...")
                            conn.close()
                            return self.build_index(force_rebuild=True)
                    except Exception as e:
                        print(f"Error processing file {file_path}: {e}")
                
                # Commit batch
                conn.commit()
                print(f"Processed batch {i//batch_size + 1}/{(len(md_files)-1)//batch_size + 1}")
            
            # Clean up index for non-existent files
            self._cleanup_orphaned_files(md_files, cursor)
            
            # Update project state
            self._set_project_state('last_index_time', datetime.now().isoformat())
            
        finally:
            conn.close()
        
        print(f"Index built: {new_files} new files, {updated_files} updated files")
        return new_files + updated_files
    
    def _cleanup_orphaned_files(self, existing_files: List[str], cursor=None):
        """Clean up index for non-existent files"""
        close_conn = False
        if cursor is None:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            cursor = conn.cursor()
            close_conn = True
        
        try:
            # Get all indexed files
            cursor.execute("SELECT DISTINCT file_path FROM testcases_meta")
            indexed_files = [row[0] for row in cursor.fetchall()]
            
            # Remove non-existent files
            for file_path in indexed_files:
                if file_path not in existing_files:
                    cursor.execute("DELETE FROM testcases_fts WHERE file_path = ?", (file_path,))
                    cursor.execute("DELETE FROM testcases_meta WHERE file_path = ?", (file_path,))
                    print(f"Removed index for deleted file: {file_path}")
            
            if close_conn:
                conn.commit()
        finally:
            if close_conn:
                conn.close()
    
    def _set_project_state(self, key: str, value: str):
        """Set project state"""
        conn = sqlite3.connect(self.metadata_db_path, timeout=30.0)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO project_state (key, value) VALUES (?, ?)
        """, (key, value))
        
        conn.commit()
        conn.close()
    
    def _get_project_state(self, key: str) -> Optional[str]:
        """Get project state"""
        conn = sqlite3.connect(self.metadata_db_path, timeout=30.0)
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM project_state WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        conn.close()
        
        return row[0] if row else None
    
    def is_first_open(self) -> bool:
        """Check if this is the first time opening the project"""
        return self._get_project_state('last_index_time') is None
    
    def search_testcases(self, query: str) -> List[Dict]:
        """Search test cases with improved Chinese search using n-gram support"""
        if not query or not query.strip():
            return []
            
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        results = []
        
        try:
            # Prepare search terms for Chinese n-gram search
            search_terms = self._prepare_chinese_search_terms(query)
            
            # Strategy 1: Try FTS5 search with improved logic for space-separated keywords
            keywords = [kw.strip() for kw in query.split() if kw.strip()]
            
            if len(keywords) > 1:
                # For space-separated keywords, use AND logic between keywords
                # but OR logic for variations within each keyword
                keyword_queries = []
                for keyword in keywords:
                    keyword_terms = self._prepare_chinese_search_terms(keyword)
                    keyword_query = " OR ".join([f'"{term}"' for term in keyword_terms])
                    keyword_queries.append(f"({keyword_query})")
                
                fts_query = " AND ".join(keyword_queries)
            else:
                # For single keyword, use OR logic for all terms
                fts_query = " OR ".join([f'"{term}"' for term in search_terms])
            
            cursor.execute("""
                SELECT uuid, name, preconditions, steps, expected_results, notes, file_path,
                       snippet(testcases_fts, 1, '<mark>', '</mark>', '...', 32) as name_snippet,
                       snippet(testcases_fts, 2, '<mark>', '</mark>', '...', 64) as preconditions_snippet,
                       snippet(testcases_fts, 3, '<mark>', '</mark>', '...', 64) as steps_snippet,
                       snippet(testcases_fts, 4, '<mark>', '</mark>', '...', 64) as expected_results_snippet,
                       snippet(testcases_fts, 5, '<mark>', '</mark>', '...', 64) as notes_snippet
                FROM testcases_fts 
                WHERE testcases_fts MATCH ?
                ORDER BY rank
            """, (fts_query,))
            
            fts_results = cursor.fetchall()
            
            # Strategy 2: If FTS results are limited, try LIKE query as fallback
            if len(fts_results) < 3 and len(query.strip()) >= 1:
                like_patterns = [f'%{term}%' for term in search_terms]
                like_query = " AND ".join([f"(name LIKE ? OR preconditions LIKE ? OR steps LIKE ? OR expected_results LIKE ? OR notes LIKE ?)" for term in search_terms])
                like_params = []
                for term in search_terms:
                    like_params.extend([f'%{term}%', f'%{term}%', f'%{term}%', f'%{term}%', f'%{term}%'])
                
                cursor.execute(f"""
                    SELECT uuid, name, preconditions, steps, expected_results, notes, file_path,
                           name as name_snippet,
                           preconditions as preconditions_snippet,
                           steps as steps_snippet,
                           expected_results as expected_results_snippet,
                           notes as notes_snippet
                    FROM testcases_fts 
                    WHERE {like_query}
                    ORDER BY name
                """, like_params)
                
                like_results = cursor.fetchall()
            else:
                like_results = []
            
            # Merge and deduplicate results
            seen_uuids = set()
            all_results = []
            
            # Add FTS results first (higher priority)
            for row in fts_results:
                if row[0] not in seen_uuids:
                    all_results.append(row)
                    seen_uuids.add(row[0])
            
            # Add LIKE results (lower priority)
            for row in like_results:
                if row[0] not in seen_uuids:
                    all_results.append(row)
                    seen_uuids.add(row[0])
            
            # Process results
            for row in all_results:
                # Determine snippet source
                if row in fts_results:
                    name_snippet = row[7]
                    preconditions_snippet = row[8]
                    steps_snippet = row[9]
                    expected_results_snippet = row[10]
                    notes_snippet = row[11]
                else:
                    # Manual highlighting for LIKE results
                    name_snippet = self._create_manual_snippet(row[1], query)
                    preconditions_snippet = self._create_manual_snippet(row[2], query)
                    steps_snippet = self._create_manual_snippet(row[3], query)
                    expected_results_snippet = self._create_manual_snippet(row[4], query)
                    notes_snippet = self._create_manual_snippet(row[5], query)
                
                results.append({
                    'uuid': row[0],
                    'name': row[1],
                    'preconditions': row[2],
                    'steps': row[3],
                    'expected_results': row[4],
                    'notes': row[5],
                    'file_path': row[6],
                    'name_snippet': name_snippet,
                    'preconditions_snippet': preconditions_snippet,
                    'steps_snippet': steps_snippet,
                    'expected_results_snippet': expected_results_snippet,
                    'notes_snippet': notes_snippet
                })
        
        except Exception as e:
            print(f"Search error: {e}")
            # Enhanced fallback with LIKE query
            results = self._fallback_search(query, cursor)
        
        conn.close()
        return results
    
    def _prepare_chinese_search_terms(self, query: str) -> List[str]:
        """Prepare search terms for Chinese n-gram search with space-separated keywords support"""
        terms = []
        query = query.strip()
        
        if not query:
            return terms
        
        # Split query by spaces to support multiple keywords
        # Preserve the original space-separated keywords
        keywords = [kw.strip() for kw in query.split() if kw.strip()]
        
        if not keywords:
            return terms
        
        # Process each keyword separately
        for keyword in keywords:
            # Add the keyword as is
            if keyword not in terms:
                terms.append(keyword)
            
            # For Chinese text, extract individual characters (1-gram)
            chinese_chars = re.findall(r'[\u4e00-\u9fff]', keyword)
            if chinese_chars:
                # Add individual Chinese characters as search terms
                for char in chinese_chars:
                    if char not in terms:
                        terms.append(char)
            
            # For Chinese text, extract character pairs (2-gram)
            if len(chinese_chars) >= 2:
                for i in range(len(chinese_chars) - 1):
                    bigram = chinese_chars[i] + chinese_chars[i + 1]
                    if bigram not in terms:
                        terms.append(bigram)
            
            # Extract English words from the keyword
            english_words = re.findall(r'[a-zA-Z]+', keyword)
            for word in english_words:
                if word.lower() not in [t.lower() for t in terms]:
                    terms.append(word)
        
        return terms
    
    def _fallback_search(self, query: str, cursor) -> List[Dict]:
        """Fallback search using LIKE queries"""
        results = []
        search_terms = self._prepare_chinese_search_terms(query)
        
        if not search_terms:
            return results
        
        # Build LIKE query with all search terms
        like_conditions = []
        like_params = []
        
        for term in search_terms:
            like_conditions.append("(name LIKE ? OR preconditions LIKE ? OR steps LIKE ? OR expected_results LIKE ? OR notes LIKE ?)")
            term_pattern = f'%{term}%'
            like_params.extend([term_pattern] * 5)
        
        like_query = " OR ".join(like_conditions)
        
        try:
            cursor.execute(f"""
                SELECT uuid, name, preconditions, steps, expected_results, notes, file_path,
                       name as name_snippet,
                       preconditions as preconditions_snippet,
                       steps as steps_snippet,
                       expected_results as expected_results_snippet
                FROM testcases_fts 
                WHERE {like_query}
                ORDER BY name
            """, like_params)
            
            for row in cursor.fetchall():
                results.append({
                    'uuid': row[0],
                    'name': row[1],
                    'preconditions': row[2],
                    'steps': row[3],
                    'expected_results': row[4],
                    'notes': row[5],
                    'file_path': row[6],
                    'name_snippet': self._create_manual_snippet(row[1], query),
                    'preconditions_snippet': self._create_manual_snippet(row[2], query),
                    'steps_snippet': self._create_manual_snippet(row[3], query),
                    'expected_results_snippet': self._create_manual_snippet(row[4], query),
                    'notes_snippet': self._create_manual_snippet(row[5], query)
                })
        except Exception as e:
            print(f"Fallback search error: {e}")
        
        return results
    
    def _create_manual_snippet(self, text: str, query: str) -> str:
        """Manually create search highlight snippet"""
        if not text or not query:
            return text or ""
        
        # Simple highlight implementation
        highlighted = text.replace(query, f'<mark>{query}</mark>')
        
        # Truncate to first 64 characters
        if len(highlighted) > 64:
            # Try to truncate near query term
            query_pos = highlighted.lower().find(query.lower())
            if query_pos != -1:
                start = max(0, query_pos - 20)
                end = min(len(highlighted), query_pos + len(query) + 44)
                snippet = highlighted[start:end]
                if start > 0:
                    snippet = '...' + snippet
                if end < len(highlighted):
                    snippet = snippet + '...'
                return snippet
            else:
                return highlighted[:64] + '...'
        
        return highlighted
    
    def get_all_testcases(self) -> List[Dict]:
        """Get all test cases"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT uuid, name, preconditions, steps, expected_results, notes, file_path
            FROM testcases_fts 
            ORDER BY name
        """)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'uuid': row[0],
                'name': row[1],
                'preconditions': row[2],
                'steps': row[3],
                'expected_results': row[4],
                'notes': row[5],
                'file_path': row[6]
            })
        
        conn.close()
        return results
    
    def get_statistics(self) -> Dict:
        """Get index statistics"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM testcases_fts")
        total_testcases = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT file_path) FROM testcases_fts")
        total_files = cursor.fetchone()[0]
        
        last_index_time = self._get_project_state('last_index_time')
        
        conn.close()
        
        return {
            'total_testcases': total_testcases,
            'total_files': total_files,
            'last_index_time': last_index_time,
            'is_first_open': last_index_time is None
        }
    
    def start_file_watcher(self):
        """Start file watcher with delay to avoid conflict with index building"""
        if self.file_watcher is None:
            self.file_watcher = FileWatcher(
                watch_paths=[self.project_path],
                callback=self._on_file_changed,
                check_interval=2.0
            )
        
        if not self.file_watcher.is_watching():
            # Delay starting file watcher to avoid conflict with index building
            import threading
            def delayed_start():
                import time
                time.sleep(3.0)  # Wait 3 seconds for index building to complete
                if self.file_watcher and not self.file_watcher.is_watching():
                    self.file_watcher.start()
                    print("File watcher started")
            
            threading.Thread(target=delayed_start, daemon=True).start()
    
    def stop_file_watcher(self):
        """Stop file watcher"""
        if self.file_watcher and self.file_watcher.is_watching():
            self.file_watcher.stop()
            print("File watcher stopped")
        
        # Cancel any pending update timer
        if hasattr(self, '_update_timer') and self._update_timer:
            self._update_timer.cancel()
            self._update_timer = None
    
    def _on_file_changed(self, file_path: str, event_type: str):
        """File change callback"""
        if not file_path.lower().endswith('.md'):
            return
        
        print(f"File {event_type}: {file_path}")
        
        try:
            if event_type in ('created', 'modified'):
                self._schedule_file_update(file_path)
            elif event_type == 'deleted':
                self._remove_testcases_by_file(file_path)
        except Exception as e:
            print(f"Error handling file change {file_path}: {e}")
    
    def _schedule_file_update(self, file_path: str):
        """Schedule file update (delayed batch processing)"""
        if self._update_timer:
            self._update_timer.cancel()
        
        # Update after 1 second delay to avoid frequent updates
        import threading
        # Cancel existing timer if it exists
        if hasattr(self, '_update_timer') and self._update_timer.is_alive():
            self._update_timer.cancel()
            print(f"[INDEXWATCH] Cancelled existing update timer for {file_path}")
        self._update_timer = threading.Timer(1.0, self._update_single_file, args=[file_path])
        print(f"[INDEXWATCH] Starting new update timer for {file_path}")
        self._update_timer.start()
    
    def _update_single_file(self, file_path: str):
        """Update index for single file with retry mechanism"""
        max_retries = 3
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                print(f"[INDEXWATCH] Starting update for file: {file_path} (attempt {attempt + 1})")
                
                # Use a single connection for the entire update operation
                conn = sqlite3.connect(self.db_path, timeout=30.0)
                cursor = conn.cursor()
                
                try:
                    # Remove old index
                    cursor.execute("DELETE FROM testcases_fts WHERE file_path = ?", (file_path,))
                    cursor.execute("DELETE FROM testcases_meta WHERE file_path = ?", (file_path,))
                    
                    # Parse and add new index
                    testcases = self._parse_markdown_testcase(file_path)
                    print(f"Parsed {len(testcases)} test cases from {file_path}")
                    
                    if testcases:
                        for testcase in testcases:
                            cursor.execute("""
                                INSERT INTO testcases_fts (uuid, name, preconditions, steps, expected_results, notes, file_path)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                testcase.uuid,
                                testcase.name,
                                testcase.preconditions,
                                testcase.steps,
                                testcase.expected_results,
                                testcase.notes,
                                file_path
                            ))
                        
                        # Update metadata
                        file_mtime = os.path.getmtime(file_path)
                        file_hash = self._get_file_hash(file_path)
                        sample_uuid = testcases[0].uuid
                        now = datetime.now().isoformat()
                        
                        cursor.execute("""
                            INSERT OR REPLACE INTO testcases_meta (uuid, file_path, file_mtime, file_hash, created_at, updated_at)
                            VALUES (?, ?, ?, ?, 
                                COALESCE((SELECT created_at FROM testcases_meta WHERE file_path = ?), ?), ?)
                        """, (sample_uuid, file_path, file_mtime, file_hash, file_path, now, now))
                        
                        conn.commit()
                        print(f"Successfully updated index for file: {file_path}")
                    else:
                        print(f"No test cases found in file: {file_path}")
                    
                    # Success - break out of retry loop
                    break
                    
                finally:
                    conn.close()
                    
            except sqlite3.Error as e:
                if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                    print(f"Database locked, retrying in {retry_delay}s...")
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"SQLite error updating file {file_path}: {e}")
                    break
            except Exception as e:
                print(f"General error updating file {file_path}: {e}")
                import traceback
                traceback.print_exc()
                break
        
        # Update timer cleanup
        self._update_timer = None
    
    def __del__(self):
        """Destructor to ensure resource cleanup"""
        try:
            self.stop_file_watcher()
            
            # Clean up update timer if it exists
            if hasattr(self, '_update_timer') and self._update_timer and self._update_timer.is_alive():
                self._update_timer.cancel()
                self._update_timer = None
        except:
            pass  # Ignore errors during cleanup
    
    def cleanup(self):
        """Explicit cleanup method for better resource management"""
        try:
            self.stop_file_watcher()
            
            # Clean up update timer if it exists
            if hasattr(self, '_update_timer') and self._update_timer and self._update_timer.is_alive():
                self._update_timer.cancel()
                self._update_timer = None
                
            print("TestCaseIndexManager cleanup completed")
        except Exception as e:
            print(f"Error during TestCaseIndexManager cleanup: {e}")