#!/usr/bin/env python
# Copyright (C) 2010 Vinay Sajip. All Rights Reserved.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose and without fee is hereby granted,
# provided that the above copyright notice appear in all copies and that
# both that copyright notice and this permission notice appear in
# supporting documentation, and that the name of Vinay Sajip
# not be used in advertising or publicity pertaining to distribution
# of the software without specific, written prior permission.
# VINAY SAJIP DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING
# ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL
# VINAY SAJIP BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR
# ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER
# IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#
"""
An example script showing how to use logging with multiprocessing.

The basic strategy is to set up a listener process which can have any logging
configuration you want - in this example, writing to rotated log files. Because
only the listener process writes to the log files, you don't have file
corruption caused by multiple processes trying to write to the file.

The listener process is initialised with a queue, and waits for logging events
(LogRecords) to appear in the queue. When they do, they are processed according
to whatever logging configuration is in effect for the listener process.

Other processes can delegate all logging to the listener process. They can have
a much simpler logging configuration: just one handler, a QueueHandler, needs
to be added to the root logger. Other loggers in the configuration can be set
up with levels and filters to achieve the logging verbosity you need.

A QueueHandler processes events by sending them to the multiprocessing queue
that it's initialised with.

In this demo, there are some worker processes which just log some test messages
and then exit.

This script was tested on Ubuntu Jaunty and Windows 7.

Copyright (C) 2010 Vinay Sajip. All Rights Reserved.
"""
# You'll need these imports in your own code
import logging
import logging.handlers
import multiprocessing


import os
import datetime


# Next two import lines for this demo only
from random import choice, random
import time

class QueueHandler(logging.Handler):
    """
    This is a logging handler which sends events to a multiprocessing queue.

    The plan is to add it to Python 3.2, but this can be copy pasted into
    user code for use with earlier Python versions.
    """

    def __init__(self, log_queue):
        """
        Initialise an instance, using the passed queue.
        """
        logging.Handler.__init__(self)
        self.log_queue = log_queue

    def emit(self, record):
        """
        Emit a record.

        Writes the LogRecord to the queue.
        """
        try:
            ei = record.exc_info
            if ei:
                dummy = self.format(record) # just to get traceback text into record.exc_text
                record.exc_info = None  # not needed any more
            self.log_queue.put_nowait(record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
#
# Because you'll want to define the logging configurations for listener and workers, the
# listener and worker process functions take a configurer parameter which is a callable
# for configuring logging for that process. These functions are also passed the queue,
# which they use for communication.
#
# In practice, you can configure the listener however you want, but note that in this
# simple example, the listener does not apply level or filter logic to received records.
# In practice, you would probably want to do ths logic in the worker processes, to avoid
# sending events which would be filtered out between processes.
#
# The size of the rotated files is made small so you can see the results easily.
# def listener_configurer():
#     root = logging.getLogger()
#     h = logging.handlers.RotatingFileHandler('/tmp/mptest.log', 'a', 300, 10)
#     f = logging.Formatter('%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s')
#     h.setFormatter(f)
#     root.addHandler(h)

def listener_configurer():
    log_file_path = os.path.join("debug","log.txt")
    max_log_size=104857600# 104857600 100MiB
    # 2015-08-14 17:46:47,371 - Process-10 - t.11536 - INFO - ln.220 - Random message #2
    formatter = logging.Formatter("%(asctime)s - %(processName)-10s - t.%(thread)d - %(levelname)s - ln.%(lineno)d - %(message)s")

    # Add timetamp for filename
    # http://stackoverflow.com/questions/8472413/add-utc-time-to-filename-python
    # '2015-06-30-13.44.15'
    timestamp_string = datetime.datetime.utcnow().strftime("%Y-%m-%d %H.%M.%S%Z")
    # Full log
    log_file_path = add_timestamp_to_log_filename(log_file_path,timestamp_string)

    # Make sure output dir(s) exists
    log_file_folder =  os.path.dirname(log_file_path)
    if log_file_folder is not None:
        if not os.path.exists(log_file_folder):
            os.makedirs(log_file_folder)

    root = logging.getLogger()

    # Rotating file handler
    # https://docs.python.org/2/library/logging.handlers.html
    # Rollover occurs whenever the current log file is nearly maxBytes in length; if either of maxBytes or backupCount is zero, rollover never occurs.
    fh = logging.handlers.RotatingFileHandler(
        filename=log_file_path,
        # https://en.wikipedia.org/wiki/Binary_prefix
        # 104857600 100MiB
        maxBytes=max_log_size,
        backupCount=10000,# Ten thousand should be enough to crash before we reach it.
        )
    fh.setFormatter(formatter)
    fh.setLevel(logging.DEBUG)
    root.addHandler(fh)  

    # Console output
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    root.addHandler(ch)

    logging.info("Logging started.")
    return

def add_timestamp_to_log_filename(log_file_path,timestamp_string):
    """Insert a string before a file extention"""
    base, ext = os.path.splitext(log_file_path)
    return base+"_"+timestamp_string+ext



# This is the listener process top-level loop: wait for logging events
# (LogRecords)on the queue and handle them, quit when you get a None for a
# LogRecord.
def listener_process(log_queue, configurer):
    configurer()
    while True:
        try:
            record = log_queue.get()
            if record is None: # We send this as a sentinel to tell the listener to quit.
                break
            logger = logging.getLogger(record.name)
            logger.handle(record) # No level or filter logic applied - just do it!
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            import sys, traceback
            print >> sys.stderr, 'Whoops! Problem:'
            traceback.print_exc(file=sys.stderr)

# Arrays used for random selections in this demo

LEVELS = [logging.DEBUG, logging.INFO, logging.WARNING,
          logging.ERROR, logging.CRITICAL]

LOGGERS = ['a.b.c', 'd.e.f']

MESSAGES = [
    'Random message #1',
    'Random message #2',
    'Random message #3',
]

# The worker configuration is done at the start of the worker process run.
# Note that on Windows you can't rely on fork semantics, so each process
# will run the logging configuration code when it starts.
def worker_configurer(log_queue):
    h = QueueHandler(log_queue) # Just the one handler needed
    root = logging.getLogger()
    root.addHandler(h)
    root.setLevel(logging.DEBUG) # send all messages, for demo; no other level or filter logic applied.

# This is the worker process top-level loop, which just logs ten events with
# random intervening delays before terminating.
# The print messages are just so you know it's doing something!
def worker_process(log_queue, configurer):
    configurer(log_queue)
    process_name = multiprocessing.current_process().name
    logging.info('Worker started: %s' % process_name)
    for i in range(10):
        time.sleep(random())
        logger = logging.getLogger(choice(LOGGERS))
        level = choice(LEVELS)
        message = choice(MESSAGES)
        logging.log(level, message)
    logging.info('Worker finished: %s' % process_name)



def post_consumer_process(log_queue, configurer, post_queue):
    """Process posts"""
    configurer(log_queue)
    process_name = multiprocessing.current_process().name
    logging.info('post_consumer_process started: %s' % process_name)
    database_session = ""# This is a pretend session to the DB
    while True:
        post = post_queue.get()
        process_post(database_session,post)

    return

def process_post(database_session,post):
    """Simulate processing a post"""
    time.sleep(1)
    logging.info("Processed post: "+repr(post))
    return

def post_producer_process(log_queue, configurer, post_queue):
    """Provide posts to process"""
    configurer(log_queue)
    process_name = multiprocessing.current_process().name
    logging.info('post_producer_process started: %s' % process_name)
    database_session = ""# This is a pretend session to the DB
    while True:
        if post_queue.qsize() < 100:
            logging.info("Adding more posts to post queue")
            new_posts = produce_posts(database_session, number_of_posts=50)
            for new_post in new_posts:
                assert(post_queue.full() is False)
                post_queue.put(new_post)
        else:
            time.sleep(1)
            assert(False)


def produce_posts(database_session,number_of_posts):
    """Simulate grabbing posts from the DB"""
    posts = []
    for n in xrange(number_of_posts):
        posts.append({
                "post_id":n,
                "foo":"bar"
                }
            )
    return posts


# Here's where the demo gets orchestrated. Create the queue, create and start
# the listener, create ten workers and start them, wait for them to finish,
# then send a None to the queue to tell the listener to finish.
def main():
    # Start logging
    log_queue = multiprocessing.Queue(-1)
    log_listener = multiprocessing.Process(target=listener_process,
                                       args=(log_queue, listener_configurer))
    log_listener.start()
    worker_configurer(log_queue)# Allow logging in main thread
    logging.debug("test main thread logging")
    # Start workers
    post_queue = multiprocessing.Queue(-1)
    # Start post provider
    provider = multiprocessing.Process(target=post_producer_process,
                                       args=(log_queue, worker_configurer, post_queue))
    provider.start()
    
    # Start post processors/consumers
    number_of_workers = 2
    workers = []
    for i in range(number_of_workers):
        worker = multiprocessing.Process(target=post_consumer_process,
                                       args=(log_queue, worker_configurer, post_queue))
        workers.append(worker)
        worker.start()
    for w in workers:
        w.join()
    log_queue.put_nowait(None)
    log_listener.join()

if __name__ == '__main__':
    main()