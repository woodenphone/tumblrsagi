#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     25/06/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import sqlalchemy

from utils import * # General utility functions
import sql_functions# Database interaction
import config # Settings and configuration
from tables import *# Table definitions


def add_blog(session,raw_blog_url):
    """Add a blog to the DB"""
    logging.info("Adding blog to db: "+repr(raw_blog_url))

    # Sanitize the blog URL
    sanitized_blog_url = clean_blog_url(raw_blog_url)

    # Make sure user is in blogs DB and get blog_id integer
    blog_id = sql_functions.add_blog(session, sanitized_blog_url)

    # Load row from blogs table so we can compare reason info
    select_query = sqlalchemy.select([twkr_blogs]).\
            where(twkr_blogs.blog_id == blog_id)
    blogs_rows = session.execute(select_query)
    blogs_row = blogs_rows.fetchone()

    # Make sure the URL we used to start this is in the reasons
    reasons_added = blogs_row["reasons_added"]
    logging.debug("Old reasons_added:"+repr(reasons_added))
    if type(reasons_added) is type(None):
        reasons_added = []
    if raw_blog_url not in reasons_added:
        reasons_added += [raw_blog_url]
    logging.debug("New reasons_added:"+repr(reasons_added))

    # Update data in the row
    update_statement = sqlalchemy.update(twkr_blogs).\
        where(twkr_blogs.blog_id == blog_id).\
        values(
            reasons_added = reasons_added
            )
    session.execute(update_statement)
    session.commit()
    return


def add_blogs(list_file_path="tumblr_todo_list.txt"):
    """Save tumblr blogs from a list"""
    logging.info("Adding blogs from list file: "+repr(list_file_path))
    # Get the list of blogs we want to add
    blog_url_list = import_blog_list(list_file_path)

    # Connect to DB
    session = sql_functions.connect_to_db()

    # Process each URL
    for blog_url in blog_url_list:
        add_blog(session,blog_url)

    logging.info("Finished downloading blogs list")
    return











def main():
    try:
        setup_logging(
        log_file_path=os.path.join("debug","add_blogs_log.txt"),
        concise_log_file_path=os.path.join("debug","short_add_blogs_log.txt")
        )
        # Program
        #classy_play()
        add_blogs(list_file_path=config.blog_list_path)
        # /Program
        logging.info("Finished, exiting.")
        return

    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return

if __name__ == '__main__':
    main()
