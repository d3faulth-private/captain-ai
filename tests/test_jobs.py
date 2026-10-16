import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from captain.jobs import JobManager

class JobsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.jobs = JobManager(Path(self.temp.name), max_jobs=1)

    def tearDown(self):
        self.jobs.close()
        self.temp.cleanup()

    def test_timeout_keeps_partial_output_and_next_job_runs(self):
        jid = self.jobs.start('slow', [sys.executable, '-u', '-c',
                    "print('partial'); import time; time.sleep(10)"], timeout=.2)
        job = self.jobs.wait(jid)
        self.assertEqual(job.status, 'timed_out')
        self.assertIn('partial', Path(job.output).read_text())
        next_id = self.jobs.start('next', [sys.executable, '-c', "print('done')"])
        self.assertEqual(self.jobs.wait(next_id).status, 'completed')

    def test_cancel_running_and_queued(self):
        first = self.jobs.start('first', [sys.executable, '-c', 'import time; time.sleep(10)'])
        second = self.jobs.start('second', [sys.executable, '-c', 'raise RuntimeError()'])
        self.jobs.cancel(second)
        self.assertEqual(self.jobs.wait(second).status, 'cancelled')
        self.jobs.cancel(first)
        self.assertEqual(self.jobs.wait(first).status, 'cancelled')

    def test_missing_executable_is_structured_failure(self):
        jid = self.jobs.start('missing', ['/no/such/captain-executable'])
        job = self.jobs.wait(jid)
        self.assertEqual(job.status, 'failed')
        self.assertTrue(job.error)

    def test_restart_marks_unfinished_job_interrupted(self):
        root = Path(self.temp.name)
        (root / 'old.json').write_text(json.dumps({'id': 'old', 'label':'old', 'status':'running'}))
        recovered = JobManager(root)
        self.assertEqual(recovered.jobs['old'].status, 'interrupted')
        self.assertIn('unknown', recovered.jobs['old'].error)
