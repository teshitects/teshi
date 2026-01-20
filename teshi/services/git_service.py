"""
Git Service for handling Git operations.
Provides a high-level interface to Git commands using subprocess.
"""
import os
import subprocess
from typing import List, Dict, Optional, Tuple
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication


class GitStatus:
    """Represents the status of a file in Git"""

    MODIFIED = "M"
    ADDED = "A"
    DELETED = "D"
    UNTRACKED = "?"
    RENAMED = "R"
    COPIED = "C"

    # Status display names
    STATUS_NAMES = {
        MODIFIED: "Modified",
        ADDED: "Added",
        DELETED: "Deleted",
        UNTRACKED: "Untracked",
        RENAMED: "Renamed",
        COPIED: "Copied",
        "MM": "Modified (both)",
        "UU": "Conflict",
    }

    # Staging states
    STAGED = "staged"
    UNSTAGED = "unstaged"
    CONFLICT = "conflict"


class GitFileStatus:
    """Represents the status of a single file"""

    def __init__(self, path: str, index_status: str, work_status: str):
        self.path = path
        self.index_status = index_status  # Status in staging area
        self.work_status = work_status  # Status in working directory

    @property
    def is_staged(self) -> bool:
        """Check if file is staged"""
        return self.index_status != " " and self.index_status != "?"

    @property
    def is_unstaged(self) -> bool:
        """Check if file has unstaged changes"""
        return self.work_status != " " and self.work_status != "?"

    @property
    def is_untracked(self) -> bool:
        """Check if file is untracked"""
        return self.work_status == "?"

    @property
    def is_conflicted(self) -> bool:
        """Check if file has conflicts"""
        return self.index_status == "U" or self.work_status == "U"

    @property
    def display_status(self) -> str:
        """Get display status string"""
        if self.is_conflicted:
            return "Conflict"
        if self.is_untracked:
            return GitStatus.STATUS_NAMES.get("?", "Untracked")
        if self.is_staged and self.is_unstaged:
            return "Modified (both)"
        if self.is_staged:
            return GitStatus.STATUS_NAMES.get(self.index_status, self.index_status)
        if self.is_unstaged:
            return GitStatus.STATUS_NAMES.get(self.work_status, self.work_status)
        return ""

    @property
    def state(self) -> str:
        """Get file state: staged, unstaged, conflict, or untracked"""
        if self.is_conflicted:
            return GitStatus.CONFLICT
        if self.is_untracked:
            return GitStatus.UNTRACKED
        if self.is_staged:
            return GitStatus.STAGED
        if self.is_unstaged:
            return GitStatus.UNSTAGED
        return ""


class GitService(QObject):
    """Service for Git operations"""

    # Signals
    status_changed = Signal()
    error_occurred = Signal(str)
    operation_completed = Signal(str, str)  # operation, message

    def __init__(self, repo_path: str):
        super().__init__()
        self.repo_path = repo_path
        self._is_git_repo = self._check_git_repo()

    def _check_git_repo(self) -> bool:
        """Check if current directory is a Git repository"""
        git_dir = os.path.join(self.repo_path, ".git")
        return os.path.exists(git_dir)

    def is_git_repo(self) -> bool:
        """Check if the path is a Git repository"""
        return self._is_git_repo

    def _run_git_command(self, args: List[str], cwd: Optional[str] = None) -> Tuple[bool, str, str]:
        """
        Run a Git command and return (success, stdout, stderr)
        """
        if not self._is_git_repo:
            return False, "", "Not a Git repository"

        try:
            cmd = ["git"] + args
            process = subprocess.Popen(
                cmd,
                cwd=cwd or self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                return True, stdout, stderr
            else:
                return False, stdout, stderr
        except FileNotFoundError:
            return False, "", "Git is not installed or not in PATH"
        except Exception as e:
            return False, "", str(e)

    def get_status(self) -> Tuple[List[GitFileStatus], List[GitFileStatus], List[GitFileStatus], List[GitFileStatus]]:
        """
        Get current Git status.
        Returns (staged, unstaged, untracked, conflicts) lists
        """
        if not self._is_git_repo:
            return [], [], [], []

        success, stdout, _ = self._run_git_command(
            ["status", "--porcelain", "-z"]
        )

        if not success:
            return [], [], [], []

        # Parse porcelain status
        staged = []
        unstaged = []
        untracked = []
        conflicts = []

        # Split by null byte
        entries = stdout.split("\0")
        i = 0
        while i < len(entries):
            entry = entries[i]
            if not entry:
                i += 1
                continue

            if len(entry) < 3:
                i += 1
                continue

            index_status = entry[0]
            work_status = entry[1]
            path = entry[3:]

            # Handle renamed/copied files
            if index_status in ("R", "C") and i + 1 < len(entries):
                # Next entry is the original path
                i += 1

            file_status = GitFileStatus(path, index_status, work_status)

            if file_status.is_conflicted:
                conflicts.append(file_status)
            elif file_status.is_untracked:
                untracked.append(file_status)
            elif file_status.is_staged and not file_status.is_unstaged:
                staged.append(file_status)
            elif file_status.is_unstaged:
                unstaged.append(file_status)
            elif file_status.is_staged and file_status.is_unstaged:
                # File with both staged and unstaged changes - show in both lists
                staged.append(file_status)
                unstaged.append(file_status)

            i += 1

        return staged, unstaged, untracked, conflicts

    def get_current_branch(self) -> str:
        """Get current branch name"""
        if not self._is_git_repo:
            return ""

        success, stdout, _ = self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
        if success:
            return stdout.strip()
        return ""

    def get_branches(self) -> Tuple[List[str], List[str]]:
        """Get all local and remote branches. Returns (local, remote)"""
        if not self._is_git_repo:
            return [], []

        local = []
        remote = []

        success, stdout, _ = self._run_git_command(["branch", "-a"])
        if success:
            for line in stdout.split("\n"):
                line = line.strip()
                if not line:
                    continue
                # Remove leading * for current branch
                line = line.lstrip("*").strip()

                if line.startswith("remotes/"):
                    # Remove 'remotes/' prefix and duplicate origin/
                    remote_branch = line.replace("remotes/", "", 1)
                    # Remove 'origin/' if present
                    if remote_branch.startswith("origin/"):
                        remote_branch = remote_branch[7:]
                    if remote_branch and remote_branch not in remote:
                        remote.append(remote_branch)
                else:
                    if line and line not in local:
                        local.append(line)

        return local, remote

    def stage_file(self, file_path: str) -> bool:
        """Stage a single file"""
        success, _, stderr = self._run_git_command(["add", file_path])
        if success:
            self.status_changed.emit()
            self.operation_completed.emit("stage", f"Staged: {file_path}")
        else:
            self.error_occurred.emit(f"Failed to stage {file_path}: {stderr}")
        return success

    def stage_all(self) -> bool:
        """Stage all changes"""
        success, _, stderr = self._run_git_command(["add", "-A"])
        if success:
            self.status_changed.emit()
            self.operation_completed.emit("stage", "All changes staged")
        else:
            self.error_occurred.emit(f"Failed to stage all: {stderr}")
        return success

    def unstage_file(self, file_path: str) -> bool:
        """Unstage a file"""
        success, _, stderr = self._run_git_command(["reset", file_path])
        if success:
            self.status_changed.emit()
            self.operation_completed.emit("unstage", f"Unstaged: {file_path}")
        else:
            self.error_occurred.emit(f"Failed to unstage {file_path}: {stderr}")
        return success

    def discard_changes(self, file_path: str) -> bool:
        """Discard changes to a file"""
        success, _, stderr = self._run_git_command(["checkout", "--", file_path])
        if success:
            self.status_changed.emit()
            self.operation_completed.emit("discard", f"Discarded changes: {file_path}")
        else:
            self.error_occurred.emit(f"Failed to discard changes: {stderr}")
        return success

    def commit(self, message: str) -> bool:
        """Create a commit with the given message"""
        if not message.strip():
            self.error_occurred.emit("Commit message cannot be empty")
            return False

        success, stdout, stderr = self._run_git_command(["commit", "-m", message])
        if success:
            self.status_changed.emit()
            self.operation_completed.emit("commit", "Commit successful")
        else:
            self.error_occurred.emit(f"Commit failed: {stderr}")
        return success

    def get_log(self, max_count: int = 50) -> List[Dict]:
        """Get commit history"""
        if not self._is_git_repo:
            return []

        # Pretty format: hash, author, date, message
        success, stdout, _ = self._run_git_command([
            "log",
            f"-{max_count}",
            '--pretty=format:%H|%an|%ae|%ad|%s',
            '--date=iso'
        ])

        if not success:
            return []

        commits = []
        for line in stdout.split("\n"):
            if not line:
                continue

            parts = line.split("|")
            if len(parts) >= 5:
                commits.append({
                    "hash": parts[0][:8],  # Short hash
                    "full_hash": parts[0],
                    "author": parts[1],
                    "email": parts[2],
                    "date": parts[3],
                    "message": parts[4]
                })

        return commits

    def get_diff(self, file_path: Optional[str] = None, cached: bool = False) -> str:
        """
        Get diff for a file or all changes.
        If cached is True, show staged changes.
        """
        if not self._is_git_repo:
            return ""

        args = ["diff"]
        if cached:
            args.append("--cached")
        if file_path:
            args.append("--")
            args.append(file_path)

        success, stdout, _ = self._run_git_command(args)
        if success:
            return stdout
        return ""

    def create_branch(self, branch_name: str) -> bool:
        """Create a new branch"""
        success, _, stderr = self._run_git_command(["branch", branch_name])
        if success:
            self.operation_completed.emit("branch", f"Created branch: {branch_name}")
        else:
            self.error_occurred.emit(f"Failed to create branch: {stderr}")
        return success

    def checkout_branch(self, branch_name: str) -> bool:
        """Checkout a branch"""
        success, _, stderr = self._run_git_command(["checkout", branch_name])
        if success:
            self.status_changed.emit()
            self.operation_completed.emit("checkout", f"Checked out: {branch_name}")
        else:
            self.error_occurred.emit(f"Failed to checkout branch: {stderr}")
        return success

    def delete_branch(self, branch_name: str, force: bool = False) -> bool:
        """Delete a branch"""
        args = ["branch", "-d" if not force else "-D", branch_name]
        success, _, stderr = self._run_git_command(args)
        if success:
            self.operation_completed.emit("branch", f"Deleted branch: {branch_name}")
        else:
            self.error_occurred.emit(f"Failed to delete branch: {stderr}")
        return success

    def pull(self, remote: str = "origin", branch: Optional[str] = None) -> bool:
        """Pull changes from remote"""
        args = ["pull", remote]
        if branch:
            args.append(branch)

        success, stdout, stderr = self._run_git_command(args)
        if success:
            self.status_changed.emit()
            self.operation_completed.emit("pull", "Pull successful")
        else:
            self.error_occurred.emit(f"Pull failed: {stderr}")
        return success

    def push(self, remote: str = "origin", branch: Optional[str] = None) -> bool:
        """Push changes to remote"""
        args = ["push", remote]
        if branch:
            args.append(branch)

        success, stdout, stderr = self._run_git_command(args)
        if success:
            self.status_changed.emit()
            self.operation_completed.emit("push", "Push successful")
        else:
            self.error_occurred.emit(f"Push failed: {stderr}")
        return success

    def get_remotes(self) -> List[str]:
        """Get list of remotes"""
        success, stdout, _ = self._run_git_command(["remote"])
        if success:
            return [line.strip() for line in stdout.split("\n") if line.strip()]
        return []

    def is_ignored(self, file_path: str) -> bool:
        """Check if a file is ignored by Git"""
        success, stdout, _ = self._run_git_command(["check-ignore", file_path])
        return success and len(stdout.strip()) > 0
