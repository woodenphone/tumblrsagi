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
import sqlalchemy

from utils import * # General utility functions
#from sql_functions import *# Database interaction
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
        self.info_post_count = info_dict["response"]["blog"]["posts"]
        logging.debug("self.info_post_count: "+repr(self.info_post_count))
        return

    def load_posts(self,max_pages=None):
        """Load posts for the blog"""
        page_counter = -1 # -1 so we start at 0
        prev_page_posts_list = ["prev page"]# Dummy value
        this_page_posts_list = ["this page"]# Dummy value
        while page_counter <= 100:# TOO SMALL, INCREASE LATER
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
            logging.debug("this_page_posts_list: "+repr(this_page_posts_list))
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
        posts_to_compare = posts_list
        existing_post_ids = find_blog_posts(self.session,self.blog_username)
        new_posts = []
        c = 0
        for post in posts_to_compare:
            c += 1
            if post["id"] in existing_post_ids:
                continue
            else:
                new_posts.append(post)
        return new_posts

    def insert_posts_into_db(self):
        raw_posts_list = self.get_posts()
        # Skip processing any posts that have previously been saved
        new_posts_list = self.crop_exisiting_posts(raw_posts_list)
        counter = 0
        for post_dict in new_posts_list:
            counter += 1
            # Handle links for the post
            # Extract links from the post
            #all_post_links = extract_post_links(post_dict)
            # For each media link, check against DB and if applicable download it
            new_post_dict = save_media(self.session,post_dict)
            # Replace links with something frontend can use later
            # Insert links into the DB
            add_post_to_db(self.session,new_post_dict,self.info_dict)
            logging.debug("Inserting "+str(counter)+"th post")
        # Commit/save new data
        logging.debug("Committing new data to DB.")
        self.session.commit()
        return

    def insert_user_into_db(self):
        """Add blog information to blogs DB"""
        logging.debug("Adding blog info to DB")
        add_blog_to_db(self.session,info_dict)
        return

    def create_blog(self):
        """Create blog table and populate meta-table with blog info"""
        # Convert blog username/URL into table name
        # Check if
        # Create blog posts table
        # Add entry to blogs table
        # Commit changes
        return

    def print_posts(self):
        """Output posts to log file for debugging"""
        c = 0
        for post in self.posts_list:
            c += 1
            logging.debug(repr(c)+": "+repr(post))
        return


def classy_play():
    """Debug and develop classes"""
    # Connect to DB
    session = connect_to_db()

    blog = tumblr_blog(session, consumer_key = config.consumer_key, blog_url = "askbuttonsmom.tumblr.com")
    posts = blog.get_posts(max_pages=1)
    #blog.print_posts()
    blog.insert_posts_into_db()
    return



# DB funcs
def connect_to_db():
    """Provide a DB session
    http://www.pythoncentral.io/introductory-tutorial-python-sqlalchemy/"""
    logging.debug("Opening DB connection")
    engine = sqlalchemy.create_engine('sqlite:///sqlalchemy_example.db')
    # Bind the engine to the metadata of the Base class so that the
    # declaratives can be accessed through a DBSession instance
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)

    DBSession = sqlalchemy.orm.sessionmaker(bind=engine)
    # A DBSession() instance establishes all conversations with the database
    # and represents a "staging zone" for all the objects loaded into the
    # database session object. Any change made against the objects in the
    # session won't be persisted into the database until you call
    # session.commit(). If you're not happy about the changes, you can
    # revert all of them back to the last commit by calling
    # session.rollback()
    session = DBSession()

    logging.debug("Session connected to DB")
    return session


def find_blog_posts(connection,blog_username):
    """Lookup a blog's posts in the DB and return a list of the IDs"""
    logging.warning("Posts lookup not implimented")# TODO FIXME
    return []



def add_post_to_db(connection,post_dict,info_dict):
    """Insert a post into the DB"""
    cursor =  connection.cursor()
    logging.debug("post_dict: "+repr(post_dict))
    logging.debug("info_dict: "+repr(info_dict))
    # Build row to insert
    row_to_insert = {} # TODO, Waiting on ATC for DB design # actually fuck waiting he can clean this up later
    # Local stuff
    row_to_insert["date_saved"] = get_current_unix_time()
    row_to_insert["version"] = 0# FIXME
    row_to_insert["link_to_hash_dict"] = json.dumps(post_dict["link_to_hash_dict"])# Link mappings
    # Things not in API docs
    row_to_insert["misc_slug"] = (post_dict["slug"] if ("slug" in post_dict.keys()) else None)# What does this do?
    row_to_insert["misc_short_url"] = (post_dict["short_url"] if ("short_url" in post_dict.keys()) else None)# shortened url?
    # All posts
    row_to_insert["all_posts_blog_name"] = post_dict["blog_name"]
    row_to_insert["all_posts_id"] =  post_dict["id"]
    row_to_insert["all_posts_post_url"] = post_dict["post_url"]
    row_to_insert["all_posts_type"] = post_dict["type"]
    row_to_insert["all_posts_timestamp"] = post_dict["timestamp"]
    row_to_insert["all_posts_date"] = post_dict["date"]
    row_to_insert["all_posts_format"] = post_dict["format"]
    row_to_insert["all_posts_reblog_key"] = post_dict["reblog_key"]
    row_to_insert["all_posts_tags"] = json.dumps(post_dict["tags"])# FIXME! Disabled for coding (JSON?)
    row_to_insert["all_posts_bookmarklet"] = (post_dict["bookmarklet"] if ("bookmarklet" in post_dict.keys()) else None)# Optional in api
    row_to_insert["all_posts_mobile"] = (post_dict["mobile"] if ("mobile" in post_dict.keys()) else None)# Optional in api
    row_to_insert["all_posts_source_url"] = (post_dict["source_url"] if ("source_url" in post_dict.keys()) else None)# Optional in api
    row_to_insert["all_posts_source_title"] = (post_dict["source_title"] if ("source_title" in post_dict.keys()) else None)# Optional in api
    row_to_insert["all_posts_liked"] = (post_dict["liked"] if ("liked" in post_dict.keys()) else None)# Can be absent based on expreience
    row_to_insert["all_posts_state"] = post_dict["state"]
    #row_to_insert["all_posts_total_posts"] = post_dict["total_posts"]# Move to blogs table?
    # Text posts
    if post_dict["type"] == "text":
        row_to_insert["text_title"] = post_dict["title"]
        row_to_insert["text_body"] = post_dict["body"]
    # Photo posts
    elif post_dict["type"] == "photo":
        row_to_insert["photo_photos"] = None#post_dict[""]
        row_to_insert["photo_caption"] = None#post_dict["caption"]
        row_to_insert["photo_width"] = None#post_dict["width"]
        row_to_insert["photo_height"] = None#post_dict["height"]
    # Quote posts
    elif post_dict["type"] == "quote":
        row_to_insert["quote_text"] = post_dict["text"]
        row_to_insert["quote_source"] = post_dict["source"]
    # Link posts
    elif post_dict["type"] == "link":
        row_to_insert["link_title"] = post_dict["title"]
        row_to_insert["link_url"] = post_dict["url"]
        row_to_insert["link_description"] = post_dict["description"]
    # Chat posts
    elif post_dict["type"] == "chat":
        row_to_insert["chat_title"] = post_dict["title"]
        row_to_insert["chat_body"] = post_dict["body"]
        row_to_insert["chat_dialogue"] = post_dict["dialogue"]
    # Audio Posts
    elif post_dict["type"] == "audio":
        row_to_insert["audio_caption"] = (post_dict["caption"] if ("caption" in post_dict.keys()) else None)
        row_to_insert["audio_player"] = (post_dict["player"] if ("player" in post_dict.keys()) else None)
        row_to_insert["audio_plays"] = (post_dict["plays"] if ("plays" in post_dict.keys()) else None)
        row_to_insert["audio_album_art"] = (post_dict["album_art"] if ("album_art" in post_dict.keys()) else None)
        row_to_insert["audio_artist"] = (post_dict["artist"] if ("artist" in post_dict.keys()) else None)
        row_to_insert["audio_album"] = (post_dict["album"] if ("album" in post_dict.keys()) else None)
        row_to_insert["audio_track_name"] = (post_dict["track_name"] if ("track_name" in post_dict.keys()) else None)
        row_to_insert["audio_track_number"] = (post_dict["track_number"] if ("track_number" in post_dict.keys()) else None)
        row_to_insert["audio_year"] = (post_dict["year"] if ("year" in post_dict.keys()) else None)
    # Video Posts
    elif post_dict["type"] == "video":
        row_to_insert["video_caption"] = post_dict["caption"]
        row_to_insert["video_player"] = "FIXME"#post_dict["player"]
    # Answer Posts
    elif post_dict["type"] == "answer":
        row_to_insert["answer_asking_name"] = post_dict["asking_name"]
        row_to_insert["answer_asking_url"] = post_dict["asking_url"]
        row_to_insert["answer_question"] = post_dict["question"]
        row_to_insert["answer_answer"] = post_dict["answer"]
    else:
        logging.error("Unknown post type!")
        logging.error(repr(locals()))
        assert(False)
    #
    if config.log_db_rows:
        logging.debug("row_to_insert: "+repr(row_to_insert))
    # Insert dict into DB
    fields = row_to_insert.keys()
    values = row_to_insert.values()
    query = generate_insert_query(table_name="posts",value_names=fields)
    logging.debug(repr(query))
    result = cursor.execute(query, values)
    cursor.close()
    return

# /DB funcs


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



