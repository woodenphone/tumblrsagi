#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     05/07/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------


import sqlalchemy


import lockfiles # MutEx lockfiles
from utils import * # General utility functions
import sql_functions# Database interaction
from media_handlers import *# Media finding, extractiong, ect
from tables import *# Table definitions
import config # Settings and configuration



def splitthousands(s, sep=','):
    #http://code.activestate.com/recipes/498181-add-thousands-separator-commas-to-formatted-number/
    if len(s) <= 3: return s
    return splitthousands(s[:-3], sep) + sep + s[-3:]




def generate_stats_page():
    logging.info("Generating stats page...")
    # Connect to the DB
    session = sql_functions.connect_to_db()
    page_html = "Rowcounts:"+"\r\n"
    # Get rowcounts
    raw_posts_rowcount = session.query(sqlalchemy.func.count(RawPosts.primary_key)).scalar()
    media_rowcount = session.query(sqlalchemy.func.count(Media.media_id)).scalar()
    twkr_posts_rowcount = session.query(sqlalchemy.func.count(twkr_posts.post_id)).scalar()
    twkr_blogs_rowcount = session.query(sqlalchemy.func.count(twkr_blogs.blog_id)).scalar()
    # Add values to page
    page_html += "raw_posts: "+splitthousands(str(raw_posts_rowcount))+"\r\n"
    page_html += "twkr_posts: "+splitthousands(str(twkr_posts_rowcount))+"\r\n"
    page_html += "twkr_blogs: "+splitthousands(str(twkr_blogs_rowcount))+"\r\n"
    page_html += "Media: "+splitthousands(str(media_rowcount))+"\r\n"
    page_html += "\r\n"
    page_html += "\r\n"
    page_html += "\r\n"
    page_html += "Ratios:"+"\r\n"
    page_html += "raw_posts/twkr_posts: "+repr((raw_posts_rowcount/twkr_posts_rowcount))+"\r\n"
    page_html += "raw_posts: "+splitthousands(str(raw_posts_rowcount))+", twkr_posts: "+splitthousands(str(twkr_posts_rowcount))+"\r\n"
    logging.debug(page_html)
    save_file(
            file_path="stats.txt",
            data=page_html,
            force_save=True,
            allow_fail=False
            )
    logging.info("Generated stats page.")




def main():
    try:
        setup_logging(
        log_file_path=os.path.join("debug","generate_stats_page_log.txt"),
        )
        # Program
        generate_stats_page()
        # /Program
        logging.info("Finished, exiting.")
        return

    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return

if __name__ == '__main__':
    main()
