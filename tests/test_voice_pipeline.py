import queue
import unittest
from unittest.mock import patch
from captain.voice import calibrated_threshold, put_latest
from captain.model import Ollama
from captain.config import Config


class VoicePipelineTests(unittest.TestCase):
    def test_quiet_microphone_and_isolated_click(self):
        threshold = calibrated_threshold([.00002] * 39 + [.00561])
        self.assertLess(threshold, .002)
        self.assertGreater(threshold, .00002)

    def test_noisy_room_threshold_tracks_background(self):
        self.assertAlmostEqual(calibrated_threshold([.001] * 40), .004)

    def test_backlog_replaced_by_fresh_audio(self):
        pending = queue.Queue(maxsize=1)
        put_latest(pending, ('old', b'old audio'))
        put_latest(pending, ('fresh', b'new audio'))
        self.assertEqual(pending.get_nowait()[0], 'fresh')
        self.assertTrue(pending.empty())

    def test_warmup_retains_model_and_only_runs_once(self):
        import io
        import json
        with patch('captain.model.urllib.request.build_opener') as factory:
            factory.return_value.open.return_value = io.BytesIO(b'{"done":true}')
            model = Ollama(Config())
            model.warmup()
            model.warmup()
            self.assertEqual(factory.return_value.open.call_count, 1)
            request = factory.return_value.open.call_args.args[0]
            self.assertEqual(json.loads(request.data)['keep_alive'], '30m')

    def test_failed_warmup_can_retry(self):
        with patch('captain.model.urllib.request.build_opener') as factory:
            factory.return_value.open.side_effect = TimeoutError('load timeout')
            model = Ollama(Config())
            with self.assertRaises(TimeoutError):
                model.warmup()
            self.assertFalse(model.warmed)
