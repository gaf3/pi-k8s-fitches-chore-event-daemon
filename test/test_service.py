import unittest
import unittest.mock

import os
import json

import service

class MockChoreRedis(object):

    def __init__(self, host, port, channel):

        self.host = host
        self.port = port
        self.channel = channel

        self.chores = {}
        self.nexted = []

    def get(self, node):

        if node in self.chores:
            return self.chores[node]

        return None

    def next(self, chore):

        self.nexted.append(chore)

class MockRedis(object):

    def __init__(self, host, port):

        self.host = host
        self.port = port
        self.channel = None
        self.messages = []

    def pubsub(self):

        return self

    def subscribe(self, channel):

        self.channel = channel

    def get_message(self):

        return self.messages.pop(0)

class TestService(unittest.TestCase):

    @unittest.mock.patch.dict(os.environ, {
        "REDIS_HOST": "data.com",
        "REDIS_PORT": "667",
        "REDIS_SPEECH_CHANNEL": "stuff",
        "REDIS_EVENT_CHANNEL": "things",
        "SLEEP": "7"
    })
    @unittest.mock.patch("pi_k8s_fitches.chore_redis.ChoreRedis", MockChoreRedis)
    @unittest.mock.patch("redis.StrictRedis", MockRedis)
    def setUp(self):

        self.daemon = service.Daemon()

    def test___init___(self):

        self.assertEqual(self.daemon.chore_redis.host, "data.com")
        self.assertEqual(self.daemon.chore_redis.port, 667)
        self.assertEqual(self.daemon.chore_redis.channel, "stuff")
        self.assertEqual(self.daemon.redis.host, "data.com")
        self.assertEqual(self.daemon.redis.port, 667)
        self.assertEqual(self.daemon.channel, "things")
        self.assertEqual(self.daemon.sleep, 7)
        self.assertIsNone(self.daemon.pubsub)

    def test_subscribe(self):

        self.daemon.subscribe()

        self.assertEqual(self.daemon.redis, self.daemon.pubsub)
        self.assertEqual(self.daemon.redis.channel, "things")

    def test_process(self):

        self.daemon.subscribe()

        self.daemon.redis.messages = [
            None,
            {
                "data": 1
            },
            {
                "data": json.dumps({
                    "timestamp": 7,
                    "type": "falling"
                })
            },
            {
                "data": json.dumps({
                    "timestamp": 7,
                    "type": "rising",
                    "gpio_port": 0
                })
            },
            {
                "data": json.dumps({
                    "timestamp": 7,
                    "type": "rising",
                    "gpio_port": 4,
                    "node": "nope"
                })
            },
            {
                "data": json.dumps({
                    "timestamp": 7,
                    "type": "rising",
                    "gpio_port": 4,
                    "node": "bump"
                })
            }
        ]
        self.daemon.chore_redis.chores = {
            "bump": {
                "text": "do it"
            }
        }

        self.daemon.process()
        self.assertEqual(self.daemon.chore_redis.nexted, [])

        self.daemon.process()
        self.assertEqual(self.daemon.chore_redis.nexted, [])

        self.daemon.process()
        self.assertEqual(self.daemon.chore_redis.nexted, [])

        self.daemon.process()
        self.assertEqual(self.daemon.chore_redis.nexted, [])

        self.daemon.process()
        self.assertEqual(self.daemon.chore_redis.nexted, [])

        self.daemon.process()
        self.assertEqual(self.daemon.chore_redis.nexted, [{
            "text": "do it"
        }])

    @unittest.mock.patch("service.time.sleep")
    @unittest.mock.patch("traceback.format_exc")
    @unittest.mock.patch('builtins.print')
    def test_run(self, mock_print, mock_traceback, mock_sleep):

        self.daemon.redis.messages = [
            {
                "data": json.dumps({
                    "timestamp": 7,
                    "type": "rising",
                    "gpio_port": 4,
                    "node": "bump"
                })
            },
            None,
            None
        ]
        self.daemon.chore_redis.chores = {
            "bump": {
                "text": "do it"
            }
        }

        mock_sleep.side_effect = [None, Exception("whoops"), Exception("whoops")]
        mock_traceback.side_effect = ["spirograph", Exception("doh")]

        self.assertRaisesRegex(Exception, "doh", self.daemon.run)

        self.assertEqual(self.daemon.chore_redis.nexted, [{
            "text": "do it"
        }])
        mock_print.assert_has_calls([
            unittest.mock.call("whoops"),
            unittest.mock.call("spirograph"),
            unittest.mock.call("whoops")
        ])
