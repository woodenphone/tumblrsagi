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

from utils import * # General utility functions
import sql_functions# Database interaction
from media_handlers import *# Media finding, extractiong, ect
import config # Settings and configuration
from tables import *# Table definitions


from sqlalchemy import update


def check_if_there_are_new_posts_to_do_media_for(session):
    """Return true if one or more rows in raw_posts has "null" as the value
    for the processed_post_json column.
    Otherwise return False"""
    posts_query = sqlalchemy.select([RawPosts]).where(RawPosts.processed_post_json == "null")
    post_rows = session.execute(posts_query)
    post_row = post_rows.fetchone()
    logging.debug("post_row: "+repr(post_row))
    return False




def process_one_new_posts_media(session):
    """Return True if everything was fine.
    Return False if no more posts should be tried"""
    # Select a new post from RawPosts table
    # New posts don't have a processed JSON
    posts_query = sqlalchemy.select([RawPosts]).where(RawPosts.processed_post_json == "null")# I expected "== None" to work, but apparently a string of "null" is the thing to do?
    logging.debug("posts_query"": "+repr(posts_query))
    post_rows = session.execute(posts_query)
    logging.debug("post_rows"": "+repr(post_rows))

    # Process posts
    post_row = post_rows.fetchone()
    # Stop if no rows
    if post_row is None:
        logging.info("No posts to check.")
        return False

    logging.debug("post_row"": "+repr(post_row))
    raw_post_dict = json.loads(post_row["raw_post_json"])
    blog_url = post_row["blog_domain"]
    username = post_row["poster_username"]
    primary_key = post_row["primary_key"]

    # Handle links for the post
    processed_post_dict = save_media(session,raw_post_dict)
    logging.debug("processed_post_dict"": "+repr(processed_post_dict))

    # Insert row to posts table
    # Insert post into the DB
    sql_functions.add_post_to_db(
        session=session,
        raw_post_dict=raw_post_dict,
        processed_post_dict=processed_post_dict,
        info_dict=None,
        blog_url=blog_url,
        username=username
        )
    session.commit()

    logging.debug("About to update RawPosts")
    # Modify origin row
    processed_post_json = json.dumps(processed_post_dict)
    update_statement = update(RawPosts).where(RawPosts.primary_key==primary_key).\
        values(processed_post_json=processed_post_json)
    update_statement.execute()
    session.commit()

    logging.debug("Finished processing new post media")
    return True





def process_all_posts_media(session):
    counter = 0
    keep_going = True
    while keep_going:
        counter += 1
        logging.debug("Row "+repr(counter))
        keep_going = process_one_new_posts_media(session)
    logging.debug("Finished processing posts for media")




def main():
    try:
        setup_logging(
        log_file_path=os.path.join("debug","tumblr-media-grabber-log.txt"),
        concise_log_file_path=os.path.join("debug","short-tumblr-media-grabber-log.txt")
        )
        # Program
        # Connect to DB
        session = sql_functions.connect_to_db()
        process_all_posts_media(session)
        # /Program
        logging.info("Finished, exiting.")
        return

    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return

if __name__ == '__main__':
    main()
