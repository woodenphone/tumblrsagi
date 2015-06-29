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
from multiprocessing.dummy import Pool as ThreadPool

from utils import * # General utility functions
import sql_functions# Database interaction
from media_handlers import *# Media finding, extractiong, ect
from tables import *# Table definitions
import config # Settings and configuration
import blog_themes# blog themes

class tumblr_blog:
    def __init__(self,session,consumer_key,blog_url=None,):
        # Store args for later and initialise variables
        self.blog_exists = None
        self.consumer_key = consumer_key
        self.raw_blog_url = blog_url
        self.blog_url = clean_blog_url(self.raw_blog_url)
        self.session = session
        self.posts_list = []# List of post dicts
        self.info_post_count = None # Number of posts the /info API says the blog has
        self.posts_post_count = None # Number of posts the /posts API says the blog has

        # Load blog info from API
        self.load_info()
        if not self.blog_exists:
            return
        # Convert blog username/URL into safer name
        self.sanitized_blog_url = self.blog_url# TODO FIXME!
        self.sanitized_username = self.info_blog_username# TODO FIXME!

        # Make sure user is in blogs DB and get blog_id integer
        self.blog_id = sql_functions.add_blog(self.session,self.sanitized_blog_url)

        if self.blog_exists:
            # These things shouldn't be done for dead blogs because they might corrupt the blog data
            # Add info to blogs table
            self.update_blog_row()
            # Update blog theme
            blog_themes.update_blog_theme(
                session=self.session,
                blog_url=self.blog_url
                )
        return

    def load_info(self):
        """Load data from API /info"""
        info_url = "http://api.tumblr.com/v2/blog/"+self.blog_url+"/info?api_key="+self.consumer_key
        info_json = get(info_url)
        if not info_json:
            logging.error("Cannot load info page! (Maybe blog URL is wrong?)")
            logging.error("locals(): "+repr(locals()))
            self.blog_exists = False
            return
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
        self.info_title = info_dict["response"]["blog"]["title"]
        self.info_updated = info_dict["response"]["blog"]["updated"]
        self.info_description = info_dict["response"]["blog"]["description"]
        self.info_ask = info_dict["response"]["blog"]["ask"]
        logging.debug("self.info_post_count: "+repr(self.info_post_count))
        # Determine if blog is alive
        if self.info_post_count > 0:
            # If we can get the API data AND there is at least one post
            logging.debug("load_info() blog is alive: "+repr(self.blog_url))
            self.blog_exists = True
        else:
            # If we dont have any posts, the blog is probably dead
            logging.error("load_info() blog has no posts! assuming it is dead: "+repr(self.blog_url))
            self.blog_exists = False
        return

    def update_blog_row(self):
        """Update this blog's row in the blogs table"""
        logging.debug("About to update blog metadata for: "+repr(self.blog_url))
        # Load row from blogs table so we can compare reason info
        select_query = sqlalchemy.select([twkr_blogs]).\
                where(twkr_blogs.blog_id == self.blog_id)
        blogs_rows = self.session.execute(select_query)
        blogs_row = blogs_rows.fetchone()

        # Make sure the URL we used to start this is in the reasons
        reasons_added = blogs_row["reasons_added"]
        if type(reasons_added) is type(None):
            reasons_added = []
        if self.raw_blog_url not in reasons_added:
            reasons_added += [self.raw_blog_url]

        # Update data in the row
        update_statement = sqlalchemy.update(twkr_blogs).\
            where(twkr_blogs.blog_id == self.blog_id).\
            values(
                title = self.info_title,
                updated = self.info_updated,
                postcount = self.info_post_count,
                name = self.info_name,
                description = self.info_description,
                ask = self.info_ask,
                alive = self.blog_exists,
                reasons_added = reasons_added
                )
        self.session.execute(update_statement)
        self.session.commit()
        logging.debug("Finsihed updating blog metadata for: "+repr(self.blog_url))
        return

    def save_new_posts(self,max_pages=None):
        """Load posts for the blog"""
        timestamp_of_last_post_in_db = sql_functions.get_timestamp_of_last_post(session=self.session,blog_domain=self.blog_url)
        preexisting_post_ids = sql_functions.find_blog_posts(self.session,self.sanitized_username)
        try:
            added_posts_counter = 0
            page_counter = -1 # -1 so we start at 0
            prev_page_posts_list = ["prev page"]# Dummy value
            this_page_posts_list = ["this page"]# Dummy value
            while page_counter <= 100000:# 100,000 pages should be enough for anyone - R.M. Stallman
                page_counter += 1
                if max_pages is not None:
                    if page_counter > max_pages:
                        logging.warning("Reached max pages")
                        break
                if (page % 100 == 0):# Every hundred pages throw an info level to let us know it's still working
                    logging.info("Loading page "+repr(page_counter)+" of posts for "+repr(self.blog_url))
                else:
                    logging.debug("Loading page "+repr(page_counter)+" of posts for "+repr(self.blog_url))


                # Load API page
                offset = page_counter*20 # Maximum posts per page is 20
                if offset != 0:
                    page_url = "http://api.tumblr.com/v2/blog/"+self.blog_url+"/posts/?api_key="+self.consumer_key+"&offset="+str(offset)
                else:
                    page_url = "http://api.tumblr.com/v2/blog/"+self.blog_url+"/posts/?api_key="+self.consumer_key
                logging.debug("page_url: "+repr(page_url))
                page_json = get(page_url)
                if not page_json:
                    logging.error("Failed to load API page for this blog")
                    self.session.rollback
                    appendlist(
                        blog_url,
                        list_file_path="tumblr_failed_list.txt",
                        initial_text="# List of failed items.\n"
                        )
                    return

                # Decode JSON
                page_dict = json.loads(page_json)

                # Stop if bad response
                if page_dict["meta"]["status"] != 200:
                    logging.error("Bad response, stopping scan for posts. "+repr(page_url))
                    logging.debug(repr(locals()))
                    break

                # Check how many posts the blog says it has
                if page_counter == 1:
                    self.posts_post_count = page_dict["response"]["total_posts"]
                    logging.info("Blog "+repr(self.blog_url)+" /posts post_count: "+repr(self.posts_post_count))

                # Add new posts to DB
                this_page_posts_list = page_dict["response"]["posts"]
                logging.debug("Processing "+repr(len(this_page_posts_list))+" posts for: "+repr(page_url)+" : ")
                added_count = 0
                for post_dict in this_page_posts_list:
                    # If post is new, add it to the DB
                    post_id = post_dict["id"]
                    if not(post_id in preexisting_post_ids):
                        added_count += 1
                        #logging.debug("Adding post:"+repr(post_id)+" for: "+repr(self.blog_url))
                        self.save_post(post_dict)
                self.session.flush()# Push changes to DB side temp storage
                logging.debug("Added "+repr(added_count)+" posts for "+repr(page_url))

                # Exit conditions
                # Stop if duplicate results
                if this_page_posts_list == prev_page_posts_list:
                    logging.info("Last pages post match this pages posts, stopping loading posts. "+repr(page_url))
                    break
                # Stop if no posts
                if len(this_page_posts_list) == 0:
                    logging.info("No posts found on this page, stopping loading posts. "+repr(page_url))
                    break
                # Update duplicate check list
                prev_page_posts_list = this_page_posts_list

                # Stop loading posts if the last post on this page is older than the newest on in the DB
                if config.stop_loading_posts_when_timestamp_match:
                    if this_page_posts_list[-1]["timestamp"] <= timestamp_of_last_post_in_db:
                        logging.debug("""this_page_posts_list[-1]["timestamp"]"""+repr(this_page_posts_list[-1]["timestamp"]))
                        logging.debug("timestamp_of_last_post_in_db:"+repr(timestamp_of_last_post_in_db))
                        logging.info("newest post in db is newer than one of the posts on this page, stopping loading posts. "+repr(page_url))
                        break
                continue

            # Commit changes once all posts have been proccessed
            logging.info("Finished loading posts, committing changes... "+repr(self.blog_url))
            self.session.commit()
            logging.info("Changes committed. "+repr(self.blog_url))
            return

        # Log exceptions and pass them on
        # Also rollback
        except Exception, e:
            logging.critical("Unhandled exception in save_blog()!")
            self.session.rollback()
            logging.exception(e)
            raise

    def save_post(self,post_dict):
        """Save a post for this blog, used by save_new_posts()"""
        sql_functions.add_raw_post(
            session = self.session,
            raw_post_dict = post_dict,
            processed_post_dict = "N/A",
            info_dict = self.info_dict,
            blog_url = self.sanitized_blog_url,
            username = self.sanitized_username,
            version = 0
            )
        return



def save_blog(blog_url):
    """Save one tumblr blog"""
    logging.info("Saving blog: "+repr(blog_url))
    try:
        # Connect to DB
        session = sql_functions.connect_to_db()

        # Instantiate blog, collect blog metadata
        blog = tumblr_blog(session, consumer_key = config.consumer_key, blog_url=blog_url)

        # Ensure blog actually exists
        if blog.blog_exists is False:
            logging.error("Blog does not exist! "+repr(blog_url))
            appendlist(
                blog_url,
                list_file_path="tumblr_failed_list.txt",
                initial_text="# List of failed items.\n"
                )
            return

        # Add new posts for the blog
        posts = blog.save_new_posts(config.max_pages_to_check)

        logging.info("Finished saving blog: "+repr(blog_url))
        appendlist(blog_url,list_file_path=config.done_list_path,initial_text="# List of completed items.\n")
    except Exception, e:# Log exceptions and pass them on
        logging.critical("Unhandled exception in save_blog()!")
        logging.exception(e)
        raise
    logging.debug("About to close db connection")
    session.close()
    logging.debug("Closed db connection")
    return


def save_blogs():
    """Save tumblr blogs from the DB twkr_blogs table"""
    logging.info("Saving posts for blogs in DB")
    blog_url_list = list_blogs()
    logging.info("Blogs about to be checked for posts: "+repr(blog_url_list))
    # Run workers
    # http://stackoverflow.com/questions/2846653/python-multithreading-for-dummies
    # Make the Pool of workers
    pool = ThreadPool(config.number_of_post_grab_workers)# Set to one for debugging
    results = pool.map(save_blog, blog_url_list)
    #close the pool and wait for the work to finish
    pool.close()
    pool.join()
    logging.info("Finished downloading blogs list")
    return


def list_blogs():
    """Return a list of up to maximum_blogs blogids"""
    # Connect to DB
    session = sql_functions.connect_to_db()

    # Load rows from blogs table so we can compare reason info
    # Order by ID
    # Offset by offset rows
    # maximum of maximum_blogs rows
    select_query = sqlalchemy.select([twkr_blogs]).\
        order_by(twkr_blogs.blog_id.asc())

    blogs_rows = session.execute(select_query)

    # Grab blog URLs
    blog_urls = []
    for blogs_row in blogs_rows:
        blog_url = blogs_row["blog_url"]
        blog_urls += [blog_url]

    # Disconnect from DB
    session.close()

    return blog_urls


def main():
    try:
        setup_logging(
        log_file_path=os.path.join("debug","get_posts_log.txt"),
        concise_log_file_path=os.path.join("debug","short_get_posts_log.txt")
        )
        # Program
        save_blogs()
        # /Program
        logging.info("Finished, exiting.")
        return

    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return

if __name__ == '__main__':
    main()
