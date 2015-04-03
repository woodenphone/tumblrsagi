#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     04/03/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import sqlalchemy

from utils import * # General utility functions
import sql_functions# Database interaction
from media_handlers import *# Media finding, extractiong, ect
import config # Settings and configuration



class tumblr_blog:
    def __init__(self,session,consumer_key,blog_url=None,blog_username=None):
        # Store args for later and initialise variables
        self.consumer_key = consumer_key
        self.blog_url = blog_url
        self.blog_username = blog_username
        self.session = session
        self.posts_list = []# List of post dicts
        self.info_post_count = None # Number of posts the /info API says the blog has
        self.posts_post_count = None # Number of posts the /posts API says the blog has
        # Load blog info from API
        self.load_info()
        # Convert blog username/URL into safer name
        self.sanitized_blog_url = self.blog_url# TODO FIXME!
        self.sanitized_username = self.info_blog_username# TODO FIXME!
        # Make sure user is in blogs DB
        #sql_functions.insert_user_into_db(self.session,self.info_dict,self.sanitized_username,self.sanitized_blog_url)
        # DEBUG
        #sql_functions.update_last_saved(self.session,self.info_dict,self.sanitized_blog_url)# REMOVEME FIXME DEBUG
        #self.session.commit()
        # /DEBUG
        return

    def clean_blog_url(self,raw_blog_url):
        return raw_blog_url

    def load_info(self):
        """Load data from API /info"""
        info_url = "http://api.tumblr.com/v2/blog/"+self.blog_url+"/info?api_key="+self.consumer_key
        info_json = get(info_url)
        if not info_json:
            logging.error("Cannot load info page! (Maybe blog URL is wrong?)")
            logging.error("locals(): "+repr(locals()))
            assert(False)# We should stop if this happens, without /info data later code will probably malfunction
        info_dict = json.loads(info_json)
        logging.debug("info_dict"+repr(info_dict))
        assert(type(info_dict) is type({}))
        # Check response is valid
        if info_dict["meta"]["status"] != 200:
            logging.error("Bad response, cannot load info.")
            logging.debug(repr(locals()))
            assert(False)
        self.info_dict = info_dict
        self.info_name = info_dict["response"]["blog"]["name"]
        self.info_post_count = info_dict["response"]["blog"]["posts"]
        self.info_blog_username = info_dict["response"]["blog"]["name"]
        logging.debug("self.info_post_count: "+repr(self.info_post_count))
        return

    def load_posts(self,max_pages=None):
        """Load posts for the blog"""
        page_counter = -1 # -1 so we start at 0
        prev_page_posts_list = ["prev page"]# Dummy value
        this_page_posts_list = ["this page"]# Dummy value
        while page_counter <= 100000:# 100,000 pages should be enough for anyone - R.M. Stallman
            page_counter += 1
            if max_pages is not None:
                if page_counter > max_pages:
                    logging.info("Reached max pages")
                    break
            logging.info("Loading page "+repr(page_counter))
            # Load API page
            offset = page_counter*20 # Maximum posts per page is 20
            if offset != 0:
                page_url = "http://api.tumblr.com/v2/blog/"+self.blog_url+"/posts/?api_key="+self.consumer_key+"&offset="+str(offset)
            else:
                page_url = "http://api.tumblr.com/v2/blog/"+self.blog_url+"/posts/?api_key="+self.consumer_key
            logging.debug("page_url: "+repr(page_url))
            page_json = get(page_url)
            page_dict = json.loads(page_json)
            #logging.debug("page_dict: "+repr(page_dict))
            # Stop if bad response
            if page_dict["meta"]["status"] != 200:
                logging.error("Bad response, stopping scan for posts.")
                logging.debug(repr(locals()))
                break
            # Check how many posts the blog says it has
            if page_counter == 1:
                self.posts_post_count = page_dict["response"]["total_posts"]
                logging.info("Blog thinks it has "+repr(self.posts_post_count)+" posts.")
            # Add posts
            this_page_posts_list = page_dict["response"]["posts"]
            #logging.debug("this_page_posts_list: "+repr(this_page_posts_list))
            logging.debug("posts on this page: "+repr(len(this_page_posts_list)))

            # Exit conditions
            # Stop if duplicate results
            if this_page_posts_list == prev_page_posts_list:
                logging.info("Last pages post match this pages posts, stopping loading posts.")
                break
            # Stop if no posts
            if len(this_page_posts_list) == 0:
                logging.error("No posts found on this page, stopping loading posts.")
                break
            # Add posts to post list
            for current_post_dict in this_page_posts_list:
                self.posts_list.append(current_post_dict)
            # Update duplicate check list
            prev_page_posts_list = this_page_posts_list
            continue

        # Make sure we got all posts
        number_of_posts_retrieved = len(self.posts_list)
        logging.info("number_of_posts_retrieved: "+repr(number_of_posts_retrieved)+
        ", self.posts_post_count: "+repr(self.posts_post_count)+", self.info_post_count: "+repr(self.info_post_count))
        if max_pages is None:# Only run these tests if max_pages option not used
            if number_of_posts_retrieved < self.posts_post_count:
                logging.error("Post count from /posts API was higher than the number of posts retrieved!")
                logging.error(repr(locals()))
                assert(False)# Stop for easier debugging
            if number_of_posts_retrieved < self.info_post_count:
                logging.error("Post count from /info API was higher than the number of posts retrieved!")
                logging.error(repr(locals()))
                assert(False)# Stop for easier debugging
        logging.info("Finished loading posts.")
        return

    def get_posts(self,max_pages=None):
        try:
            if len(self.posts_list) > 0:
                return self.posts_list
        except AttributeError:
            pass
        self.load_posts(max_pages)
        return self.posts_list

    def crop_exisiting_posts(self,posts_list):
        logging.debug("crop_exisiting_posts()"+" "+"len(posts_list)"+": "+repr(len(posts_list)))
        existing_post_ids = sql_functions.find_blog_posts(self.session,self.sanitized_username)
        new_posts = []
        c = 0
        for post in posts_list:
            c += 1
            if post["id"] in existing_post_ids:
                continue
            else:
                new_posts.append(post)
        logging.debug("crop_exisiting_posts()"+" "+"len(new_posts)"+": "+repr(len(new_posts)))
        return new_posts

    def insert_posts_into_db(self):
        raw_posts_list = self.get_posts()
        # Skip processing any posts that have previously been saved
        new_posts_list = self.crop_exisiting_posts(raw_posts_list)
        counter = 0
        for raw_post_dict in new_posts_list:
            counter += 1
            logging.debug("Processing "+str(counter)+"th post")
            # Dump post to disk for easier debugging
            save_file(os.path.join("debug","last_post_tried_to_insert"),repr(raw_post_dict))
            # Handle links for the post
            processed_post_dict = save_media(self.session,raw_post_dict)
            # Insert post into the DB
            sql_functions.add_post_to_db(self.session,
            raw_post_dict, processed_post_dict,
            self.info_dict, self.sanitized_blog_url,
            self.sanitized_username)

            self.session.commit()
        logging.info("Finished processing posts")
        # Change date last saved in DB
        logging.warning("DATE LAST SAVED NOT YET IMPLIMENTED!")# TODO FIXME!
        #sql_functions.update_last_saved(self.session,self.info_dict,self.sanitized_blog_url)
        # Commit/save new data
        logging.debug("Committing new data to DB.")
        self.session.commit()
        return

    def print_posts(self):
        """Output posts to log file for debugging"""
        c = 0
        for post in self.posts_list:
            c += 1
            logging.debug(repr(c)+": "+repr(post))
        return



def save_blog(blog_url,max_pages=None):
    """Save one tumblr blog"""
    logging.info("Saving blog: "+repr(blog_url))
    # Connect to DB
    session = sql_functions.connect_to_db()
    # Instantiate blog, collect blog metadata
    blog = tumblr_blog(session, consumer_key = config.consumer_key, blog_url=blog_url)
    # Collect posts for the blog
    posts = blog.get_posts(max_pages)
    # Save media for posts and insert them into the DB
    blog.insert_posts_into_db()
    logging.info("Finished saving blog: "+repr(blog_url))
    return



def save_blogs(list_file_path="tumblr_todo_list.txt",max_pages=None):
    """Save tumblr blogs from a list"""
    logging.info("Saving list of blogs: "+repr(list_file_path))
    blog_url_list = import_blog_list(list_file_path)
    for blog_url in blog_url_list:
        save_blog(blog_url,max_pages)
        appendlist(blog_url,list_file_path=config.done_list_path,initial_text="# List of completed items.\n")
    logging.info("Finished downloading blogs list")
    return


def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","tumblr-api-dumper-log.txt"))
        # Program
        #classy_play()
        save_blogs(list_file_path="tumblr_todo_list.txt",max_pages=None)
        # /Program
        logging.info("Finished, exiting.")
        return

    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return

if __name__ == '__main__':
    main()
