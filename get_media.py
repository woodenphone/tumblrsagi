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
        media_id_list = save_media(session,raw_post_dict)
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


def worker(post_row_list):
    logging.info("Worker started for "+repr(len(post_row_list))+" posts.")
    # Connect to DB
    session = sql_functions.connect_to_db()
    # Process posts
    for post_row in post_row_list:
        process_one_new_posts_media(session,post_row)
    # Disconnect from DB
    session.close()
    logging.info("Worker finished.")
    return


def post_consumer_process(log_queue, log_configurer, post_queue):
    """Consume post dicts"""
    log_configurer(log_queue)# Start logging for this process
    logging.info("post_consumer_process started:")
    # Connect to DB
    database_session = sql_functions.connect_to_db()
    # Process posts
    c = 0
    while True:
        c += 1
        if c%100 == 0:
            logging.info(repr(c)+" posts processed by this process")

        post_row = post_queue.get(timeout=600)
        process_one_new_posts_media(database_session,post_row)
        continue
    # Disconnect from DB
    database_session.close()
    logging.info("post_consumer_process finished.")
    return


def post_producer_process(log_queue, configurer, post_queue):
    """Provide post dicts"""
    configurer(log_queue)
    logging.info("post_producer_process started")
    database_session = sql_functions.connect_to_db()
    while True:
        if post_queue.qsize() < 100:
            logging.info("Adding more posts to post queue")
            new_posts = list_new_posts(database_session, max_rows=1000)
            for new_post in new_posts:
                assert(post_queue.full() is False)
                post_queue.put(new_post)
        else:
            time.sleep(1)


def list_new_posts(database_session,max_rows):
    logging.info("Getting list of new posts")
    # Select new posts
    # New posts don't have a processed JSON
    posts_query = sqlalchemy.select([RawPosts]).\
        where(RawPosts.media_processed != True ).\
        where((RawPosts.skip_processing == False) | (RawPosts.skip_processing == None)).\
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


def mp_process_posts(log_queue,worker_configurer):
    """Run workers as seperate processes"""
    logging.info("Starting workers...")
    # Start workers
    post_queue = multiprocessing.Queue(-1)
    # Start post provider
    provider = multiprocessing.Process(target=post_producer_process,
                                       args=(log_queue, worker_configurer, post_queue))
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


def mt_process_posts():
    """Clone of mp_process_posts() using threading instead so we can use normal logging"""
    logging.info("Starting workers...")
    # Start workers
    post_queue = Queue.Queue(-1)
    # Start post provider
    log_queue=1#Dummy
    worker_configurer=int#Dummy
    provider = threading.Thread(target=post_producer_process,
                                       args=(log_queue, worker_configurer, post_queue))
    provider.start()
    logging.info("Post provider started.")

    # Start post processors/consumers
    number_of_workers = config.number_of_media_workers
    workers = []
    for i in range(number_of_workers):
        worker = threading.Thread(
            target=post_consumer_process,
            args=(log_queue, worker_configurer, post_queue)
            )
        workers.append(worker)
        worker.start()
    logging.info("All consumers started.")
    # Wait until processed finish
    for w in workers:
        w.join()
    provider.join()
    logging.info("Finished processing posts.")
    return



def process_all_posts_media(max_rows=1000):
    # Connect to DB
    listing_session = sql_functions.connect_to_db()
    post_dicts = ["dummy"]
    counter = 0
    while len(post_dicts) > 0:
        # Get primary keys for some new posts
        logging.debug("Grabbing a thousand unprocessed post primary keys")
        post_dicts = list_new_posts(listing_session,max_rows)
        # Process posts
        logging.debug("Processing posts, "+repr(counter)+" done so far this run")
        logging.debug("Starting workers")

        jobs = split_list(
            list_in = post_dicts,
            number_of_pieces = config.number_of_media_workers
            )

        # http://stackoverflow.com/questions/2846653/python-multithreading-for-dummies
        # Make the Pool of workers

        # For some reason multiprocessing.Pool doesn't run through IDLE or pyscripter?
        #pool = ThreadPool(config.number_of_media_workers)# Set to one for debugging
        pool = Pool(processes=config.number_of_media_workers)
        logging.debug("pool opened")
        results = pool.map(worker, jobs)
        #close the pool and wait for the work to finish
        logging.debug("closing pool")
        pool.close()
        logging.debug("Pool closed")
        pool.join()
        logging.debug("All workers finished")
        logging.info("Finished proccessing this group of posts")
        counter += max_rows
        continue
    logging.info("Finished processing posts for media")
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
        mt_process_posts()
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
