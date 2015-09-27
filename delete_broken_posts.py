#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     09/06/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import sqlalchemy

from utils import * # General utility functions
import sql_functions# Database interaction
from media_handlers import *# Media finding, extractiong, ect
from tables import *# Table definitions
import config # Settings and configuration






def delete_broken_posts():
    """Remove posts that do not have the processed flag set to true in the rawposts table"""
    session = sql_functions.connect_to_db()

    # -Posts with status mismatch-

    # Each post row must have the same timestamp, blog url, and origin id as a rawposts row
    # The rawposts row must have media_processed == True

    # Choose a blog
    blog_statement = sqlalchemy.select([blogs]).\
        where(blogs.blog_id < 100)
    blog_rows = session.execute(blog_statement)
    blog_row = blog_rows.fetchone()
    logging.debug(repr(blog_row))
    blog_id = 1

    # For each post from this blog
    select_posts_statement = sqlalchemy.select([posts]).\
        where(posts.blog_id == blog_id).\
        limit(100)
    post_rows = session.execute(select_posts_statement)
    for post_row in post_rows:
        logging.debug("post_row:"+repr(post_row))
        post_id = post_row["post_id"]

        # Grab the matching row from rawposts
        compare_statement  = sqlalchemy.select([RawPosts]).\
            where(post_row.source_url == RawPosts.all_posts_post_url).\
            where(post_row.timestamp == RawPosts.all_posts_timestamp).\
            limit(10)
        compare_rows = session.execute(compare_statement)
        compare_row = compare_rows.fetchone()
        logging.debug("compare_row:"+repr(compare_row))

        # If post row exists but processed flag is not true, delete post
        if compare_row["media_processed"] == False:
            logging.debug("Bad")

            # Delete post
            delete_post_statement = sqlalchemy.select([posts]).\
                where(posts.post_id == post_id)
            session.execute(delete_post_statement)

            continue
        else:
            logging.debug("Good")
            continue








    # Delete child rows

    # Delete post row

    # Commit changes
    session.commit()

    # -Posts without Rawposts row-

##                [
##                posts,
##                posts_photo,
##                posts_photo_text,
##                posts_link,
##                posts_answer,
##                posts_text,
##                posts_quote,
##                posts_chat,
##                post_reblog_trail,
##                post_audio,
##                post_video,
##                media_associations,
##                ]).\


def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","delete_broken_posts_log.txt"))
        delete_broken_posts()
        logging.info("Finished, exiting.")
        pass
    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return

if __name__ == '__main__':
    main()
