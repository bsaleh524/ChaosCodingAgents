"""Handles all file I/O inside a session's workspace folder."""

from pathlib import Path


class WorkspaceManager:
    def __init__(self, workspace_path: Path):
        self.path = workspace_path
        self.path.mkdir(parents=True, exist_ok=True)

        seed = self.path / "solution.py"
        if not seed.exists():
            seed.write_text(
                "# Chaos Coding Agents — workspace\n"
                "# Waiting for the first move...\n"
            )

    def write_solution(self, code: str, filename: str = "solution.py") -> None:
        if not code.strip():
            return  # never wipe the file with an empty parse result
        (self.path / filename).write_text(code)

    def read_workspace(self) -> dict[str, str]:
        """Returns {relative_path: contents} for every .py file in the workspace."""
        return {
            str(f.relative_to(self.path)): f.read_text()
            for f in sorted(self.path.rglob("*.py"))
        }
