import tempfile
import threading
import time
import unittest
from pathlib import Path
from captain.config import Config
from captain.controller import Controller

class DelayedModel:
    def __init__(self):
        self.entered = threading.Event()
        self.release = threading.Event()
    def reply(self, text, context):
        self.entered.set()
        self.release.wait(3)
        return {'say': 'done', 'action': {'type':'write_file', 'path':'bad.txt', 'text':'stale'}}

class ControllerTests(unittest.TestCase):
    def test_stop_invalidates_inflight_action_and_status_does_not_wait(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model, spoken = DelayedModel(), []
            c = Controller(Config(workspace=str(root/'files')), root, emit=spoken.append, model=model)
            try:
                c.submit('write a file')
                self.assertTrue(model.entered.wait(1))
                start = time.monotonic()
                c.submit('status')
                self.assertLess(time.monotonic() - start, .2)
                c.submit('stop')
                self.assertIn('What do you want me to stop, Boss?', spoken)
                model.release.set()
                c.pending.result(2)
                self.assertFalse((root/'files/bad.txt').exists())
            finally:
                model.release.set()
                c.close()

    def test_voice_actions_disabled_and_private_memory_not_saved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model, spoken = DelayedModel(), []
            model.release.set()
            c = Controller(Config(workspace=str(root/'files')), root, emit=spoken.append, model=model)
            try:
                c.submit('write a file', allow_actions=False)
                c.pending.result(2)
                self.assertFalse((root/'files/bad.txt').exists())
                c.submit('private mode')
                c.actions.execute({'type':'remember', 'text':'private preference'}, private=c.private)
                self.assertEqual(c.memory.list(), [])
            finally:
                c.close()
