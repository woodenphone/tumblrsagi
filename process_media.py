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










def process_new_posts_media():
    # Connect to DB
    session = sql_functions.connect_to_db()
    # Select a new post from RawPosts table
    # New posts don't have a processed JSON
    posts_query = sqlalchemy.select([RawPosts]).where(RawPosts.processed_post_json == "null")# I expected "== None" to work, but apparently a string of "null" is the thing to do?
    logging.debug("posts_query"": "+repr(posts_query))
    post_rows = session.execute(posts_query)
    logging.debug("post_rows"": "+repr(post_rows))

    # Process posts
    counter = 0
    for post_row in post_rows:
        counter += 1
        logging.debug("Row "+repr(counter))
        logging.debug("post_row"": "+repr(post_row))
        raw_post_dict = json.loads(post_row["raw_post_json"])
        blog_url = post_row["blog_domain"]
        username = post_row["poster_username"]
        primary_key = post_row["primary_key"]

        # Handle links for the post
        processed_post_dict = save_media(session,raw_post_dict)

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

        # Modify origin row
        sqlalchemy.update(RawPosts).\
            where(RawPosts.primary_key==primary_key).\
            values(processed_post_dict=processed_post_dict)
        session.commit()

    logging.debug("Finished processing new post media")
    return










def main():
    try:
        setup_logging(
        log_file_path=os.path.join("debug","tumblr-media-grabber-log.txt"),
        concise_log_file_path=os.path.join("debug","short-tumblr-media-grabber-log.txt")
        )
        # Program
        process_new_posts_media()
        # /Program
        logging.info("Finished, exiting.")
        return

    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return

if __name__ == '__main__':
    main()
