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

import pytumblr


from utils import * # General utility functions
from sql_functions import *

import config # Settings and configuration



class tumblr_blog:
    def __init__(self,connection,consumer_key,blog_url=None,blog_username=None):
        # Store args for later and initialise variables
        self.consumer_key = consumer_key
        self.blog_url = blog_url
        self.blog_username = blog_username
        self.connection = connection
        self.posts_list = []# List of post dicts
        # Load blog info from API
        self.load_info()
        return
    def clean_blog_url(self,raw_blog_url):
        return raw_blog_url

    def load_info(self):
        """Load data from API /info"""
        info_url = "http://api.tumblr.com/v2/blog/"+self.blog_url+"/info?api_key="+self.consumer_key
        info_json = get(info_url)
        info_dict = json.loads(info_json)
        logging.debug("info_dict"+repr(info_dict))
        # Check response is valid
        if info_dict["meta"]["status"] != 200:
            logging.error("Bad response, cannot load info.")
            logging.debug(repr(locals()))
            assert(False)
        self.info_dict = info_dict
        return

    def load_posts(self):
        """Load posts for the blog"""
        page_counter = -1 # -1 so we start at 0
        prev_page_posts_list = ["prev page"]# Dummy value
        this_page_posts_list = ["this page"]# Dummy value
        while page_counter <= 100:# TOO SMALL, INCREASE LATER
            page_counter += 1
            # Load API page
            offset = page_counter*20 # Maximum posts per page is 20
            page_url = "http://api.tumblr.com/v2/blog/"+self.blog_url+"/posts/text?api_key="+self.consumer_key+"&offset="+str(offset)
            logging.debug("page_url"+repr(page_url))
            page_json = get(page_url)
            page_dict = json.loads(page_json)
            logging.debug("page_dict"+repr(page_dict))
            # Stop if bad response
            if page_dict["meta"]["status"] != 200:
                logging.error("Bad response, stopping scan for posts.")
                logging.debug(repr(locals()))
                break
            # Add posts
            this_page_posts_list = page_dict["response"]["posts"]
            # Stop if duplicate results
            if this_page_posts_list == prev_page_posts_list:
                logging.info("Last pages post match this pages posts")
                break
            # Add posts to post list
            for current_post_dict in this_page_posts_list:
                self.posts_list.append(current_post_dict)
            # Update duplicate check list
            prev_page_posts_list = this_page_posts_list
            continue
        return

    def get_posts(self):
        try:
            if len(self.posts_list) > 0:
                return self.posts_list
        except AttributeError:
            pass
        self.load_posts()
        return self.posts_list

    def insert_posts_into_db(self):
        posts_list = self.get_posts()
        counter = 0
        for post_dict in posts_list:
            counter += 1
            add_post_to_db(self.connection,post_dict,self.info_dict)
            logging.debug("Inserting "+str(counter)+"th post")
        # Commit/save new data
        self.connection.commit()
        return








def classy_play():
    logging.debug("Opening DB connection")
    connection = mysql.connector.connect(**config.sql_login)
    blog = tumblr_blog(connection, consumer_key = config.consumer_key, blog_url = "citriccomics.tumblr.com")
    posts = blog.get_posts()
    logging.debug("posts"+repr(posts))
    blog.insert_posts_into_db()
    logging.debug("Closing DB connection")
    connection.close()





def find_images(post_dict):
    pass

def process_iamge(image_url):
    # Compare url with DB
    # Load image URL
    # Generate image hash
    # Compare hash with DB
    # If hash is in DB, add URL to db and return
    # If hash is not in DB, save it to disk and add image data to the DB
    pass


def save_images(post_dict):
    pass





# Functional




def process_blog():
    return




def load_api_raw():
    """Test/learning.debug during coding"""
    url = "http://api.tumblr.com/v2/blog/citriccomics.tumblr.com/posts/text?api_key="+config.consumer_key
    logging.debug("url"+repr(url))
    api_json = get(url)
    logging.debug("api_json"+repr(api_json))
    global api_dict
    api_dict = json.loads(api_json)
    logging.debug("api_dict"+repr(api_dict))
    # Check that api responed correctly
    if api_dict["meta"]["status"] == 200:
        page_posts = api_dict["response"]["posts"]




def load_api_pytumblr():
    """Test/learning.debug during coding"""
    client = pytumblr.TumblrRestClient(consumer_key = config.consumer_key)
    print(client.posts(blogname="tsitra360"))


def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","tumblr-api-dumper-log.txt"))
        # Program
        #load_api_raw()
        classy_play()
        # /Program
        logging.info("Finished, exiting.")
        return

    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return

if __name__ == '__main__':
    main()

# Test code



