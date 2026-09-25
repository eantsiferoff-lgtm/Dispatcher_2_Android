import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from core.data_paths import DataPaths


class TestDataPaths(unittest.TestCase):
    def test_runtime_data_boundaries(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = DataPaths(root)

            self.assertEqual(paths.root, root)
            self.assertEqual(paths.state, root / "state")
            self.assertEqual(paths.tasks, root / "tasks")
            self.assertEqual(paths.requests, root / "requests")
            self.assertEqual(paths.results, root / "results")
            self.assertEqual(paths.traces, root / "traces")
            self.assertEqual(paths.artifacts, root / "artifacts")
            self.assertEqual(paths.projects, root / "projects")
            self.assertEqual(paths.archive, root / "archive")
            self.assertEqual(paths.archive_skills, root / "archive" / "skills")
            self.assertEqual(paths.archive_requests, root / "archive" / "requests")


if __name__ == "__main__":
    unittest.main()
