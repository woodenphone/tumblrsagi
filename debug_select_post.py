#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     26/05/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import sqlalchemy

from utils import * # General utility functions
import sql_functions# Database interaction
import config # User specific settings
from tables import *# Table definitions

def read_post(session,post_url):
    posts_query = sqlalchemy.select([RawPosts]).\
        where(RawPosts.all_posts_post_url == post_url)
    posts_rows = session.execute(posts_query)
    post_ids = []
    for row in posts_rows:
        logging.debug("row in db:"+repr(row))
    return


def debug():
    """Temp code for debug"""
    session = sql_functions.connect_to_db()

    read_post(session,post_url="http://askbuttonsmom.tumblr.com/post/118625666843/happy-mothers-day")




def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","debug-select-post-log.txt"))
        debug()
        logging.info("Finished, exiting.")
        pass
    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return


if __name__ == '__main__':
    main()
