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

from multiprocessing.dummy import Pool as ThreadPool

from utils import * # General utility functions
import sql_functions# Database interaction
from media_handlers import *# Media finding, extractiong, ect
import config # Settings and configuration
from tables import RawPosts


def process_one_new_posts_media(post_row):
    """Return True if everything was fine.
    Return False if no more posts should be tried"""
    try:
        session = sql_functions.connect_to_db()
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

        logging.debug("Finished processing new post media")
        return

    # Log exceptions and pass them on
    # Also rollback
    except Exception, e:
        logging.critical("Unhandled exception in save_blog()!")
        session.rollback()
        logging.exception(e)
        raise
    logging.debug("About to close db connection")
    session.close()
    logging.debug("Closd db connection")
    return


def list_new_posts(session,max_rows):
    logging.debug("Getting list of new posts")
    # Select new posts
    # New posts don't have a processed JSON
    posts_query = sqlalchemy.select([RawPosts]).\
        where(RawPosts.media_processed != True ).\
        limit(max_rows)
    #logging.debug("posts_query"": "+repr(posts_query))
    post_rows = session.execute(posts_query)
    #logging.debug("post_rows"": "+repr(post_rows))

    # List rows to grab
    logging.debug("Getting list of rows")
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
    return post_dicts


def process_all_posts_media(max_rows=1000):
    # Connect to DB
    session = sql_functions.connect_to_db()
    post_dicts = ["dummy"]
    while len(post_dicts) > 0:
        # Get primary keys for some new posts
        post_dicts = list_new_posts(session,max_rows)
        # Process posts
        logging.debug("Processing posts")
        # http://stackoverflow.com/questions/2846653/python-multithreading-for-dummies
        # Make the Pool of workers
        pool = ThreadPool(config.number_of_media_workers)# Set to one for debugging
        results = pool.map(process_one_new_posts_media, post_dicts)
        #close the pool and wait for the work to finish
        pool.close()
        pool.join()
        logging.debug("Finished proccessing this group of posts")
        continue
    logging.debug("Finished processing posts for media")
    return


def main():
    try:
        setup_logging(
            log_file_path=os.path.join("debug","get_media_log.txt"),
            concise_log_file_path=os.path.join("debug","short_get_media_log.txt")
            )
        # Program
        process_all_posts_media()
        # /Program
        logging.info("Finished, exiting.")
        return

    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return

if __name__ == '__main__':
    main()
