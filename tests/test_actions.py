import tempfile
import unittest
from pathlib import Path
from captain.actions import Actions
from captain.config import Config
from captain.jobs import JobManager
from captain.memory import Memory
from captain.policy import PolicyError

class ActionTests(unittest.TestCase):
    def test_write_backup_and_unknown_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            jobs = JobManager(root/'jobs')
            actions = Actions(Config(workspace=str(root/'files')), jobs, Memory(root/'memory.db'))
            try:
                actions.execute({'type':'write_file','path':'note.txt','text':'original'})
                actions.execute({'type':'write_file','path':'note.txt','text':'updated'})
                self.assertEqual((root/'files/note.txt').read_text(), 'updated')
                backups = list((root/'files/.captain-backups').iterdir())
                self.assertEqual(backups[0].read_text(), 'original')
                for action in [{'type':'shell','command':'whoami'}, {'type':'open_browser','url':'file:///etc/passwd'}]:
                    with self.assertRaises(PolicyError):
                        actions.execute(action)
            finally:
                jobs.close()
