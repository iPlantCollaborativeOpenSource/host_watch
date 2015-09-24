#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import csv
import json
import logging
import os
import time
import sys
from collections import namedtuple
from datetime import datetime
from pprint import pformat
from subprocess import Popen, PIPE

from celery import Celery
from celery.events.snapshot import Polaroid
from shapeshift import JSONFormatter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atmosphere.settings')
sys.path.append("/opt/dev/atmosphere")

import django
django.setup()
from django.conf import settings

try:
    import logstash
except ImportError:
    raise "Requires python-logstash to be installed"

logger = logging.getLogger(__name__)

DEFAULT_LOGSTASH_PORT = 5002
DEFAULT_MESSAGE_RATE = 60

ConnectionInfo = namedtuple("ConnectionInfo", ["listening", "establish_wait"])
ActiveInfo = namedtuple("ActiveInfo", ["active_workers", "idle_workers", "active_tasks"])
ReservedInfo = namedtuple("ReservedInfo", ["reserved_tasks", "queued_tasks"])


def log_celery_info(active, reserved, connections, error=None):
    logger.info("Celery monitoring information", extra={
        "type": "atmo-celery-data",
        "active_workers": active.active_workers,
        "active_task_count": active.active_tasks,
        "reserved_task_count": reserved.reserved_tasks,
        "reserved_queue_count": reserved.queued_tasks,
        "established_waiting_connection_count": connections.establish_wait,
        "error": 1 if error is None else 0
    })


def active_worker_and_task_count(app):
    active_worker_list = app.active()
    active_worker_count = 0
    active_task_count = 0
    empty_worker_count = 0

    for x in active_worker_list.iteritems():
        name , list_queue = x
        if len(list_queue) is not 0:
            active_worker_count += 1
            active_task_count += len(list_queue)
        else:
            empty_worker_count += 1

    return ActiveInfo(active_worker_count, active_task_count, empty_worker_count)


def reserve_count(app):

    reserverd_worker_list = app.reserved()
    reserved_queue_count = 0
    reserved_task_count = 0

    for x in reserverd_worker_list.iteritems():
        name, list_queue = x
        if len(list_queue) is not 0:
            reserved_queue_count += 0
            reserved_task_count += len(list_queue)

    return ReservedInfo(reserved_queue_count, reserved_task_count)


def total_connections_count():
    proc = Popen(["netstat", "-wltun"], stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()

    list_of_lines = out.splitlines()

    if len(list_of_lines) > 3:
        number_of_listeners = len(list_of_lines) -2
    else:
        number_of_listeners = 0


    proc2 = Popen(["netstat", "-wtun", "|", "grep", "-v", "127.0.0.1"], stdout=PIPE, stderr=PIPE)
    out, err = proc2.communicate()

    list_of_lines = out.splitlines()

    if len(list_of_lines) > 3:
        number_of_established_waiting = len(list_of_lines) -2
    else:
        number_of_established_waiting = 0

    return ConnectionInfo(number_of_listeners, number_of_established_waiting)

def main(args):
    app = Celery('atmosphere')
    app.config_from_object('django.conf:settings')

    if args.logfile:
        handler = logging.FileHandler(args.logfile)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    handler = logstash.TCPLogstashHandler(args.host, args.port, version=1)
    logger.addHandler(handler)
    print("Monitoring started")

    while True:
        print("Sending new message")
        state = app.events.State()
        app_inspect = app.control.inspect()

        if app_inspect is not None:
            a = active_worker_and_task_count(app_inspect)
            r = reserve_count(app_inspect)
            t = total_connections_count()
            log_celery_info(active=a, reserved=r, connections=t)
        else:
            log_celery_info(error=0)

        # How often to monitor the machine
        time.sleep(args.rate)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="host_watch",
        description="Forwards machine statistics to logstash.")
    parser.add_argument("host", help="Hostname of the logstash server")
    parser.add_argument("--port", default=DEFAULT_LOGSTASH_PORT, type=int,
                        help="Specify the port logstash is using.")
    parser.add_argument("--log-to", dest="logfile",
                        help="Specifies a file to log to.")
    parser.add_argument(
        "--rate", default=DEFAULT_MESSAGE_RATE, type=int,
        help="How often messages are sent to logstash in seconds (default=60)")
    args = parser.parse_args()
    main(args)
