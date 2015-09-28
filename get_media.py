#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     20/04/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import sqlalchemy
from sqlalchemy import update

#import multiprocessing
import threading
import Queue
#from multiprocessing import Pool
#from multiprocessing.dummy import Pool

import lockfiles # MutEx lockfiles
from utils import * # General utility functions
import sql_functions# Database interaction
from media_handlers import *# Media finding, extractiong, ect
import config # Settings and configuration
from tables import RawPosts


import mp_logging_setup

def process_one_new_posts_media(session,post_row):
    """Return True if everything was fine.
    Return False if no more posts should be tried"""
    try:
        post_primary_key = post_row["primary_key"]
        logging.debug("Processing post with primary_key: "+repr(post_primary_key))
        logging.debug("post_row"": "+repr(post_row))
        raw_post_dict = post_row["raw_post_json"]
        blog_url = post_row["blog_domain"]
        username = post_row["poster_username"]
        # Get blog_id
        blog_id = sql_functions.add_blog(session,blog_url)

        # Handle links for the post
        media_id_list = save_media(session,raw_post_dict,blog_id)
        logging.debug("media_id_list"": "+repr(media_id_list))
        session.commit()# Media can be safely persisted without the post

        # Insert row to posts tables
        sql_functions.insert_one_post(
                session = session,
                post_dict = raw_post_dict,
                blog_id = blog_id,
                media_id_list = media_id_list
                )

        # Modify origin row to show media has been processed
        logging.debug("About to update RawPosts")
        update_statement = update(RawPosts).where(RawPosts.primary_key == post_primary_key).\
            values(media_processed = True)
        session.execute(update_statement)

        session.commit()

        logging.debug("Finished processing new post media with primary_key: "+repr(post_primary_key))
        return

    # Log exceptions and pass them on
    # Also rollback
    except Exception, e:
        logging.critical("Unhandled exception in save_blog()!")
        logging.exception(e)
        # Rollback
        session.rollback()
        raise
    assert(False)# Thsi should never run


def post_consumer(post_queue):
    "Process posts for  a queue-like object containing post dicts"
    logging.debug("Consumer function started.")
    # Connect to DB
    database_session = sql_functions.connect_to_db()
    # Process posts from the queue
    c = 0# Counter for number of posts processed
    while True:
        c += 1
        if c%100 == 0:
            logging.info(repr(c)+" posts processed by this process")
        post_row = post_queue.get(timeout=600)
        if post_row is None:# Stop if None object is put into the queue
            logging.info("Post consumer recieved None object as exit signal")
            break# Stop doing work and exit thread/process        
        process_one_new_posts_media(database_session,post_row)
        continue
    # Disconnect from DB
    database_session.close()
    logging.debug("Consumer function exiting.")
    return


def post_consumer_process(log_queue, log_configurer, post_queue):
    """Multiprocessing wrapper for post_consumer"""
    # Setup logging for this process
    log_configurer(log_queue)
    logging.info("post_consumer_process started:")
    # Do work
    post_consumer(post_queue)
    # Exit process
    logging.info("post_consumer_process finished.")
    return


def post_producer(post_queue,target_blog=None):
    """Keep a queue-like object filled with post dicts"""
    # Connect to the DB
    database_session = sql_functions.connect_to_db()
    # Keep the queue supplied with posts
    counter = 0
    while True:
        if post_queue.qsize() < 100:
            logging.info("Adding more posts to post queue. Posts added so far: "+repr(counter))
            new_posts = list_new_posts(
                database_session=database_session,
                max_rows=1000, 
                target_blog=target_blog
                )

            if len(new_posts) == 0:
                # Tell consumers to stop by flooding the queue with None objects
                #logging.error("No more posts to process, exiting.")
                for n in xrange(100):
                    post_queue.put(None)
                return
            for new_post in new_posts:
                assert(post_queue.full() is False)
                counter += 1
                post_queue.put(new_post)
        else:
            time.sleep(1)


def post_producer_process(log_queue, configurer, post_queue, target_blog):
    """Multiprocessing wrapper for post_producer"""
    # Setup logging for this process
    configurer(log_queue)
    logging.info("post_producer_process started")
    # Supply posts
    post_producer(post_queue,target_blog)


def list_new_posts(database_session,max_rows,target_blog=None):
    logging.info("Getting list of new posts")
    # Select new posts
    # New posts don't have a processed JSON
    if target_blog is None:
        # Target all unprocessed posts
        posts_query = sqlalchemy.select([RawPosts]).\
            where(RawPosts.media_processed != True ).\
            where((RawPosts.skip_processing == False) | (RawPosts.skip_processing == None)).\
            limit(max_rows)
    else:
        # Target a specific blog
        posts_query = sqlalchemy.select([RawPosts]).\
            where(RawPosts.media_processed != True ).\
            where((RawPosts.skip_processing == False) | (RawPosts.skip_processing == None)).\
            where((RawPosts.blog_domain == blog_domain)).\
            limit(max_rows)        
    #logging.debug("posts_query"": "+repr(posts_query))
    post_rows = database_session.execute(posts_query)
    #logging.debug("post_rows"": "+repr(post_rows))

    # List rows to grab
    #logging.debug("Getting list of rows")
    post_dicts = []
    row_list_counter = 0
    for post_row in post_rows:
        row_list_counter += 1
        if row_list_counter > max_rows:
            break
        if post_row:
            #logging.debug("post_row: "+repr(post_row))
            post_dicts.append(post_row)
        continue
    #logging.debug("post_dicts: "+repr(post_dicts))
    logging.info("list_new_posts() found "+repr(len(post_dicts))+" matching post rows")
    return post_dicts


def mp_process_posts(log_queue,worker_configurer,target_blog=None):
    """Run workers as seperate processes"""
    logging.info("Starting workers...")
    # Start workers
    post_queue = multiprocessing.Queue(-1)
    # Start post provider
    provider = multiprocessing.Process(target=post_producer_process,
        args=(log_queue, worker_configurer, post_queue, target_blog))
    provider.daemon = True# Make sure process is killed on exit
    provider.start()
    logging.info("Post provider started.")

    # Start post processors/consumers
    number_of_workers = config.number_of_media_workers
    workers = []
    for i in range(number_of_workers):
        worker = multiprocessing.Process(
            target=post_consumer_process,
            args=(log_queue, worker_configurer, post_queue)
            )
        worker.daemon = True# Make sure process is killed on exit
        workers.append(worker)
        worker.start()
    logging.info("All consumers started.")
    # Wait until processed finish
    for w in workers:
        w.join()
    provider.join()
    logging.info("Finished processing posts.")
    return


def mt_process_posts(target_blog=None):
    """Clone of mp_process_posts() using threading instead so we can use normal logging"""
    logging.info("Starting workers...")
    # Start workers
    post_queue = Queue.Queue(-1)
    # Start post provider
    provider = threading.Thread(target=post_producer,
       args=(post_queue,target_blog))
    provider.start()
    logging.info("Post provider started.")

    # Start post processors/consumers
    number_of_workers = config.number_of_media_workers
    logging.debug("Starting "+repr(number_of_workers)+" consumer threads...")
    workers = []
    for i in range(number_of_workers):
        logging.debug("Starting worker "+repr(i))
        worker = threading.Thread(
            target=post_consumer,
            args=(post_queue,)
            )
        workers.append(worker)
        worker.start()
        logging.debug("Worker "+repr(i)+" started.")
    logging.info("All consumers started.")
    # Wait until processed finish
    for w in workers:
        w.join()
    provider.join()
    logging.info("Finished processing posts.")
    return


def main():
    # Check and create lockfiles OUTSIDE trt / except block to ensure it is
    # not removed on lock-related crash
    lock_file_path = os.path.join(config.lockfile_dir, "get_media.lock")
    lockfiles.start_lock(lock_file_path)
    try:
        # Start logging
        setup_logging(
            log_file_path=os.path.join("debug","get_media_log.txt"),
            )
        # log_queue = multiprocessing.Queue(-1)
        # log_listener = multiprocessing.Process(target=mp_logging_setup.listener_process,
        #                                    args=(log_queue, mp_logging_setup.listener_configurer))
        # log_listener.start()
        # mp_logging_setup.worker_configurer(log_queue)# Log in main process as well

        # Program
        #mp_process_posts(log_queue,worker_configurer=mp_logging_setup.worker_configurer)
        mt_process_posts(target_blog=None)
        # /Program

        logging.info("Finished, exiting.")

    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    finally:
        # Remove lockfile even if we crashed
        lockfiles.remove_lock(lock_file_path)
        # # Finsih logging
        # log_queue.put_nowait(None)
        # log_listener.join()
        return

if __name__ == '__main__':
    main()
