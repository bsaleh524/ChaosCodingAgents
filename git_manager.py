"""Handles all git operations inside the workspace directory."""

from pathlib import Path
import git


class GitManager:
    def __init__(self, workspace_path: Path):
        self.path = workspace_path
        self.path.mkdir(exist_ok=True)

        try:
            self.repo = git.Repo(self.path)
        except git.InvalidGitRepositoryError:
            self.repo = git.Repo.init(self.path)
            seed = self.path / "solution.py"
            seed.write_text("# Chaos Coding Agents — workspace\n# Waiting for the first move...\n")
            self.repo.index.add(["solution.py"])
            self.repo.index.commit("workspace: init")

    # ── Public API ────────────────────────────────────────────────────────────

    def write_solution(self, code: str, filename: str = "solution.py") -> None:
        (self.path / filename).write_text(code)

    def commit(self, message: str) -> None:
        self.repo.git.add("-A")
        if self.repo.is_dirty(index=True, untracked_files=True):
            self.repo.index.commit(message)

    def diff_last(self) -> str:
        """Unified diff of the most recent commit vs its parent."""
        try:
            return self.repo.git.diff("HEAD~1", "HEAD")
        except git.GitCommandError:
            return "(no previous commit to diff against)"

    def diff_stat_last(self) -> str:
        try:
            return self.repo.git.diff("HEAD~1", "HEAD", "--stat")
        except git.GitCommandError:
            return ""

    def read_workspace(self) -> dict[str, str]:
        """Returns {relative_path: contents} for every .py file in workspace."""
        return {
            str(f.relative_to(self.path)): f.read_text()
            for f in sorted(self.path.rglob("*.py"))
        }

    def log_oneline(self, n: int = 10) -> str:
        return self.repo.git.log(f"-{n}", "--oneline")
