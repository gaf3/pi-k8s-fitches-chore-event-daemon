"""
Main module for daemon
"""

import os
import time
import json
import traceback

import redis
import pi_k8s_fitches.chore_redis


class Daemon(object):
    """
    Main class for daemon
    """

    def __init__(self):

        self.chore_redis = pi_k8s_fitches.chore_redis.ChoreRedis(
            host=os.environ['REDIS_HOST'],
            port=int(os.environ['REDIS_PORT']),
            channel=os.environ['REDIS_SPEECH_CHANNEL']
        )
        self.redis = redis.StrictRedis(host=os.environ['REDIS_HOST'], port=int(os.environ['REDIS_PORT']))
        self.channel = os.environ['REDIS_EVENT_CHANNEL']
        self.sleep = int(os.environ['SLEEP'])
        self.pubsub = None

    def subscribe(self):
        """
        Subscribes to the event channel on Redis
        """

        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(self.channel) 

    def process(self, start):
        """
        Processes a message from the channel if later than the daemons start time
        """

        message = self.pubsub.get_message()

        if not message or isinstance(message['data'], int):
            return

        data = json.loads(message['data'])

        if data["timestamp"] < start or data["type"] != "rising" or data["gpio_port"] != 4:
            return

        chore = self.chore_redis.get(data["node"])

        if not chore:
            return

        self.chore_redis.next(chore)
            
    def run(self):
        """
        Runs the daemon
        """

        start = time.time()
        self.subscribe()

        while True:
            try:
                self.process(start)
                time.sleep(self.sleep)
            except Exception as exception:
                print(str(exception))
                print(traceback.format_exc())