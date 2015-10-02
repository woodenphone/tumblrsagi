#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     06/07/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import sqlalchemy
from sqlalchemy import update

import lockfiles # MutEx lockfiles
from utils import * # General utility functions
import sql_functions# Database interaction
from media_handlers import *# Media finding, extractiong, ect
import config # Settings and configuration
from tables import RawPosts



def process_posts(blog_domain):
    """Find all posts for a given blog"""
    # Connect to the DB
    session = sql_functions.connect_to_db()
    # Grab the posts
    posts_query = sqlalchemy.select([RawPosts]).\
        where(RawPosts.blog_domain == blog_domain)
    posts_rows = session.execute(posts_query)

    found_blog_links = []

    # Process each post
    counter = 0
    for posts_row in posts_rows:
        counter += 1
        logging.debug("Processing post "+repr(counter))
        # Grab post data from DB
        post_dict = posts_row["raw_post_json"]
        # Stringify post data
        post_string = repr(post_dict)
        # Parse out links
        blog_links_in_post = find_blog_links(post_string)
        logging.debug("blog_links_in_post: "+repr(blog_links_in_post))
        # Append found blogs to list
        found_blog_links += blog_links_in_post

    # Clean up links
    logging.debug("found_blog_links: "+repr(found_blog_links))

    kept_blog_links = remove_unwanted_links(found_blog_links)
    logging.debug("kept_blog_links: "+repr(kept_blog_links))

    output_list = uniquify(kept_blog_links)
    logging.debug("output_list: "+repr(output_list))

    timestamp_string = datetime.datetime.utcnow().strftime("%Y-%m-%d %H.%M.%S%Z")

    # Save found links to file
    appendlist(
        output_list,
        list_file_path="linked_blogs_"+blog_domain+"_"+timestamp_string+".txt",
        initial_text="# List of found blog_links.\n"
        )
    return


def find_blog_links(post_string):
    blog_link_regex = """([\w\-\_]+\.tumblr\.com)"""
    blog_links = re.findall(blog_link_regex, post_string, re.DOTALL)
    return blog_links


def remove_unwanted_links(link_list):
    kept_links = []
    for link in link_list:
        if "media.tumblr.com".lower() in link.lower():
            continue
        if "static.tumblr.com".lower() in link.lower():
            continue
        if "assets.tumblr.com".lower() in link.lower():
            continue
        else:
            kept_links.append(link)
    return kept_links

def main():
    try:
        setup_logging(
            log_file_path=os.path.join("debug","find_linked_blogs_log.txt"),
            )
        # Program
        print "Enter target blog"
        target_blog = raw_input("Target blog?")
        logging.debug("target_blog: "+repr(target_blog))
        process_posts(blog_domain=target_blog)
        # /Program
        logging.info("Finished, exiting.")
        return

    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return

if __name__ == '__main__':
    main()
