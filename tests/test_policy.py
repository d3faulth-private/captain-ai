import tempfile
import unittest
from pathlib import Path
from captain.config import Config
from captain.policy import Policy, PolicyError

class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.policy = Policy(Config(workspace=self.temp.name, allowed_networks=['10.30.18.128/32']))

    def tearDown(self):
        self.temp.cleanup()

    def test_literal_scope_only(self):
        self.assertEqual(self.policy.host('10.30.18.128'), '10.30.18.128')
        for target in ['10.30.18.129', 'example.com', '10.30.18.0/24', '-iL /etc/passwd']:
            with self.assertRaises(PolicyError):
                self.policy.host(target)

    def test_no_path_traversal_or_absolute_escape(self):
        for path in ['../escape.txt', '/etc/passwd', '.']:
            with self.assertRaises(PolicyError):
                self.policy.path(path)
        self.assertEqual(self.policy.path('report.txt').parent, Path(self.temp.name))

    def test_symlink_escape(self):
        with tempfile.TemporaryDirectory() as outside:
            link = Path(self.temp.name) / 'link'
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest('Symlinks unavailable')
            with self.assertRaises(PolicyError):
                self.policy.path('link/private.txt')
