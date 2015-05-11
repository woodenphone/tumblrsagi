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


import sqlalchemy# Database  library
from sqlalchemy.ext.declarative import declarative_base# Magic for ORM

from utils import *

import config # User specific settings

from tables import *# Table definitions


# General
def connect_to_db():
    """Provide a DB session
    http://www.pythoncentral.io/introductory-tutorial-python-sqlalchemy/"""
    logging.debug("Opening DB connection")
    # add "echo=True" to see SQL being run
    engine = sqlalchemy.create_engine(config.sqlalchemy_login, echo=config.echo_sql)
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


# Media
def check_if_hash_in_db(session,sha512base64_hash):
    """Check if a hash is in the media DB
    Return a dict of the first found row if it is, otherwise return None"""
    hash_query = sqlalchemy.select([Media]).where(Media.sha512base64_hash == sha512base64_hash)
    hash_rows = session.execute(hash_query)
    hash_row = hash_rows.fetchone()
    if hash_row:
        return hash_row
    else:
        return None


def check_if_media_url_in_DB(session,media_url):
    """Check if a URL is in the media DB
    Return a dict of the first found row if it is, otherwise return None"""
    media_url_query = sqlalchemy.select([Media]).where(Media.media_url == media_url)
    media_url_rows = session.execute(media_url_query)
    media_url_row = media_url_rows.fetchone()
    if media_url_row:
        return media_url_row
    else:
        return None


def lookup_media_url(session,table_class,media_url):# New and obsolete
    """Check if a URL is in the given table
    Return a dict of the first found row if it is, otherwise return None"""
    media_url_query = sqlalchemy.select([table_class]).where(table_class.media_url == media_url)
    media_url_rows = session.execute(media_url_query)
    media_url_row = media_url_rows.fetchone()
    if media_url_row:
        return media_url_row
    else:
        return None


def lookup_media_hash(session,table_class,sha512base64_hash):# New and obsolete
    """Check if a sha512base64_hash is in the given table
    Return a dict of the first found row if it is, otherwise return None"""
    media_url_query = sqlalchemy.select([table_class]).where(table_class.sha512base64_hash == sha512base64_hash)
    media_url_rows = session.execute(media_url_query)
    media_url_row = media_url_rows.fetchone()
    if media_url_row:
        return media_url_row
    else:
        return None


# Posts
def _add_post_to_db(session,raw_post_dict,processed_post_dict,info_dict,blog_url,username):# depricated by twkr's new tables
    """Insert a post into the DB"""
    #logging.debug("processed_post_dict: "+repr(processed_post_dict))
    #logging.debug("info_dict: "+repr(info_dict))
    # Build row to insert
    row_to_insert = {}
    # Local stuff
    row_to_insert["date_saved"] = get_current_unix_time()
    row_to_insert["version"] = 0# FIXME
    row_to_insert["link_to_hash_dict"] = json.dumps(processed_post_dict["link_to_hash_dict"])# Link mappings
    # User info
    row_to_insert["poster_username"] = username
    row_to_insert["blog_domain"] = blog_url
    # Things not in API docs
    row_to_insert["misc_slug"] = (processed_post_dict["slug"] if ("slug" in processed_post_dict.keys()) else None)# What does this do?
    row_to_insert["misc_short_url"] = (processed_post_dict["short_url"] if ("short_url" in processed_post_dict.keys()) else None)# shortened url?
    # All posts
    row_to_insert["all_posts_blog_name"] = processed_post_dict["blog_name"]
    row_to_insert["all_posts_id"] =  processed_post_dict["id"]
    row_to_insert["all_posts_post_url"] = processed_post_dict["post_url"]
    row_to_insert["all_posts_type"] = processed_post_dict["type"]
    row_to_insert["all_posts_timestamp"] = processed_post_dict["timestamp"]
    row_to_insert["all_posts_date"] = processed_post_dict["date"]
    row_to_insert["all_posts_format"] = processed_post_dict["format"]
    row_to_insert["all_posts_reblog_key"] = processed_post_dict["reblog_key"]
    row_to_insert["all_posts_tags"] = json.dumps(processed_post_dict["tags"])# FIXME! Disabled for coding (JSON?)
    row_to_insert["all_posts_bookmarklet"] = (processed_post_dict["bookmarklet"] if ("bookmarklet" in processed_post_dict.keys()) else None)# Optional in api
    row_to_insert["all_posts_mobile"] = (processed_post_dict["mobile"] if ("mobile" in processed_post_dict.keys()) else None)# Optional in api
    row_to_insert["all_posts_source_url"] = (processed_post_dict["source_url"] if ("source_url" in processed_post_dict.keys()) else None)# Optional in api
    row_to_insert["all_posts_source_title"] = (processed_post_dict["source_title"] if ("source_title" in processed_post_dict.keys()) else None)# Optional in api
    row_to_insert["all_posts_liked"] = (processed_post_dict["liked"] if ("liked" in processed_post_dict.keys()) else None)# Can be absent based on expreience
    row_to_insert["all_posts_state"] = processed_post_dict["state"]
    #row_to_insert["all_posts_total_posts"] = processed_post_dict["total_posts"]# Move to blogs table?
    # Text posts
    if processed_post_dict["type"] == "text":
        row_to_insert["text_title"] = processed_post_dict["title"]
        row_to_insert["text_body"] = processed_post_dict["body"]
    # Photo posts
    elif processed_post_dict["type"] == "photo":
        row_to_insert["photo_photos"] = json.dumps(processed_post_dict["photos"])
    # Quote posts
    elif processed_post_dict["type"] == "quote":
        row_to_insert["quote_text"] = processed_post_dict["text"]
        row_to_insert["quote_source"] = processed_post_dict["source"]
    # Link posts
    elif processed_post_dict["type"] == "link":
        row_to_insert["link_title"] = processed_post_dict["title"]
        row_to_insert["link_url"] = processed_post_dict["url"]
        row_to_insert["link_description"] = processed_post_dict["description"]
    # Chat posts
    elif processed_post_dict["type"] == "chat":
        row_to_insert["chat_title"] = processed_post_dict["title"]
        row_to_insert["chat_body"] = processed_post_dict["body"]
        row_to_insert["chat_dialogue"] = json.dumps(processed_post_dict["dialogue"])
    # Audio Posts
    elif processed_post_dict["type"] == "audio":
        row_to_insert["audio_caption"] = (processed_post_dict["caption"] if ("caption" in processed_post_dict.keys()) else None)
        row_to_insert["audio_player"] = (processed_post_dict["player"] if ("player" in processed_post_dict.keys()) else None)
        row_to_insert["audio_plays"] = (processed_post_dict["plays"] if ("plays" in processed_post_dict.keys()) else None)
        row_to_insert["audio_album_art"] = (processed_post_dict["album_art"] if ("album_art" in processed_post_dict.keys()) else None)
        row_to_insert["audio_artist"] = (processed_post_dict["artist"] if ("artist" in processed_post_dict.keys()) else None)
        row_to_insert["audio_album"] = (processed_post_dict["album"] if ("album" in processed_post_dict.keys()) else None)
        row_to_insert["audio_track_name"] = (processed_post_dict["track_name"] if ("track_name" in processed_post_dict.keys()) else None)
        row_to_insert["audio_track_number"] = (processed_post_dict["track_number"] if ("track_number" in processed_post_dict.keys()) else None)
        row_to_insert["audio_year"] = (processed_post_dict["year"] if ("year" in processed_post_dict.keys()) else None)
    # Video Posts
    elif processed_post_dict["type"] == "video":
        row_to_insert["video_caption"] = processed_post_dict["caption"]
        row_to_insert["video_player"] = "FIXME"#processed_post_dict["player"]
    # Answer Posts
    elif processed_post_dict["type"] == "answer":
        row_to_insert["answer_asking_name"] = processed_post_dict["asking_name"]
        row_to_insert["answer_asking_url"] = processed_post_dict["asking_url"]
        row_to_insert["answer_question"] = processed_post_dict["question"]
        row_to_insert["answer_answer"] = processed_post_dict["answer"]
    else:
        logging.error("Unknown post type!")
        logging.error(repr(locals()))
        assert(False)
    #
    if config.log_db_rows:
        logging.debug("row_to_insert: "+repr(row_to_insert))
    # Insert new row
    post_row = Posts(**row_to_insert)
    session.add(post_row)
    return


def add_raw_post(session,raw_post_dict,processed_post_dict,info_dict,blog_url,username,version=0):
    """Store the raw data from a post into the raw data table"""
    # Build row to insert
    row_to_insert = {}
    # Local stuff
    row_to_insert["date_saved"] = get_current_unix_time()
    row_to_insert["version"] = version# FIXME
    # User info
    row_to_insert["poster_username"] = username
    row_to_insert["blog_domain"] = blog_url
    # post identity
    row_to_insert["all_posts_id"] =  raw_post_dict["id"]
    row_to_insert["all_posts_post_url"] = raw_post_dict["post_url"]
    # Full post reencoded into JSON
    row_to_insert["raw_post_json"] = json.dumps(raw_post_dict)
    row_to_insert["processed_post_json"] = json.dumps(processed_post_dict)

    post_row = RawPosts(**row_to_insert)
    session.add(post_row)
    session.commit()
    return


def find_blog_posts(session,sanitized_username):
    """Lookup a blog's posts in the DB and return a list of the IDs"""
    logging.debug("find_blog_posts()"+"sanitized_username"+": "+repr(sanitized_username))
    # select all posts with field "poster_username" matching our value
    posts_query = sqlalchemy.select([RawPosts.all_posts_id]).where(RawPosts.poster_username == sanitized_username)
    posts_rows = session.execute(posts_query)
    post_ids = []
    for row in posts_rows:
        post_ids.append(row["all_posts_id"])
         #logging.debug("find_blog_posts()"+"row"+": "+repr(row))
    logging.debug("find_blog_posts()"+"for "+repr(sanitized_username)+"post_ids"+": "+repr(post_ids))
    return post_ids



# Blogs metadata table
def get_timestamp_of_last_post(session,blog_domain):
    """Get the timestamp (API-provided) of the most recent post saved for a blog from the blogs table
    Return the timestamp integer if it exists, if not available return 0.
    SELECT"""
    logging.debug("get_timestamp_of_last_post() blog_domain: "+repr(blog_domain))
    # Read the entry, if nothing is there we will find out pretty quickly
    post_query = sqlalchemy.select([Blogs]).where(Blogs.blog_domain == blog_domain)
    post_row = session.execute(post_query).fetchone()
    if post_row:
        timestamp_of_last_post_in_db = post_row["timestamp_of_last_post"]
        logging.debug("timestamp_of_last_post_in_db: "+repr(timestamp_of_last_post_in_db))
        return timestamp_of_last_post_in_db
    else:
        return 0


def update_date_of_last_post(session,blog_domain,timestamp_of_last_post):
    """Update the timestamp (API-provided) of the most recent post saved for a blog from the blogs table
    UPDATE"""
    logging.debug("update_date_of_last_post() blog_domain: "+repr(blog_domain)+" ,timestamp_of_last_post:"+repr(timestamp_of_last_post))
     # Make sure there is an entry

     # UPDATE the entry
    statement = sqlalchemy.update(Blogs).\
        where(Blogs.c.blog_domain == blog_domain).\
        values(timestamp_of_last_post = timestamp_of_last_post)
    session.execute(statement)
    session.commit()
    return


def create_blog_entry(session,poster_username,blog_domain):
    """Create an entry in the blogs table for a blog
    INSERT"""
    logging.debug("create_blog_entry() blog_domain: "+repr(blog_domain)+" ,blog_domain: "+repr(blog_domain))
    # Validate new values
    # Make sure there is no entry
    # Create entry
    row_to_insert = {}
    row_to_insert["date_added"] = get_current_unix_time()
    row_to_insert["date_last_saved"] = None
    row_to_insert["timestamp_of_last_post"] = None
    row_to_insert["poster_username"] = poster_username
    row_to_insert["blog_domain"] = blog_domain

    blogs_row = Blogs(**row_to_insert)
    session.add(blogs_row)
    session.commit()
    return


#


def _insert_user_into_db(session,info_dict,sanitized_username,sanitized_blog_url):# depricated by twkr's new tables
        """Add blog information to blogs DB"""
        logging.debug("Adding blog metadata to DB")
        # Check if blog is already in blogs table
        create_entry = False# Should we create a new entry?
        # Check username
        username_query = sqlalchemy.select([Blogs]).where(Blogs.poster_username == sanitized_username)
        username_rows = session.execute(username_query)
        username_row = username_rows.fetchone()
        if username_row:
            logging.debug("username_row: "+repr(username_row))
        else:
            create_entry = True
        # Check URL
        url_query = sqlalchemy.select([Blogs]).where(Blogs.blog_domain == sanitized_blog_url)
        url_rows = session.execute(url_query)
        url_row = url_rows.fetchone()
        if url_row:
            logging.debug("url_row: "+repr(url_row))
        else:
            create_entry = True
        logging.debug("Creating user entry")
        if create_entry:
            # Collect values to insert
            # Locally generated
            date_added = get_current_unix_time()# Creating this blog's entry now so it's now
            info_title = info_dict["response"]["blog"]["posts"]
            # Deal with optional values
            # From /info, documented
            try:
                info_posts = info_dict["response"]["blog"]["posts"]
                assert(type(info_posts) == type(123))# Should always be an integer
            except KeyError:
                info_posts = None
            try:
                info_name = info_dict["response"]["blog"]["name"]
                assert( (type(info_name) == type("") ) or ( type(info_name) == type(u"")) )# Should always be a string
            except KeyError:
                info_name = None
            try:
                info_updated = info_dict["response"]["blog"]["updated"]
                assert(type(info_updated) == type(123))# Should always be an integer
            except KeyError:
                info_updated = None
            try:
                info_description = info_dict["response"]["blog"]["description"]
                assert( (type(info_description) == type("") ) or ( type(info_description) == type(u"")) )# Should always be a string
            except KeyError:
                info_description = None
            try:
                info_ask = info_dict["response"]["blog"]["ask"]
                assert(type(info_ask) == bool )# Should always be a boolean
            except KeyError:
                info_ask = None
            try:
                info_ask_anon = info_dict["response"]["blog"]["ask_anon"]
                assert(type(info_ask_anon) == bool )# Should always be a boolean
            except KeyError:
                info_ask_anon = None
            try:
                info_likes = info_dict["response"]["blog"]["likes"]
                assert(type(info_likes) == type(123))# Should always be an integer
            except KeyError:
                info_likes = None
            # From /info, undocumented
            try:
                info_is_nsfw = info_dict["response"]["blog"]["is_nsfw"]
                assert(type(info_is_nsfw) == bool )# Should always be a boolean
            except KeyError:
                info_is_nsfw = None
            try:
                info_share_likes = info_dict["response"]["blog"]["share_likes"]
                assert(type(info_share_likes) == bool )# Should always be a boolean
            except KeyError:
                info_share_likes = None
            try:
                info_url = info_dict["response"]["blog"]["url"]
                assert( (type(info_url) == type("") ) or ( type(info_url) == type(u"")) )# Should always be a string
            except KeyError:
                info_url = None
            try:
                info_ask_page_title = info_dict["response"]["blog"]["ask_page_title"]
                assert( (type(info_ask_page_title) == type("") ) or ( type(info_ask_page_title) == type(u"")) )# Should always be a string
            except KeyError:
                info_ask_page_title = None
            # Add entry to blogs table
            new_blog_row = Blogs(
            # Locally generated
            date_added=date_added,
            poster_username = sanitized_username,
            blog_domain = sanitized_blog_url,
            # From /info, documented
            info_title=info_title,
            info_posts=info_posts,
            info_name=info_name,
            info_updated=info_updated,
            info_description=info_description,
            info_ask=info_ask,
            info_ask_anon=info_ask_anon,
            info_likes=info_likes,
            # From /info, undocumented
            info_is_nsfw=info_is_nsfw,
            info_share_likes=info_share_likes,
            info_url=info_url,
            info_ask_page_title=info_ask_page_title,
            )
            session.add(new_blog_row)
            session.commit()
            # Commit changes
            logging.debug("Finished adding blog metadata to DB")
        else:
            logging.debug("No need to add user to blogs table")
        return

def _update_last_saved(session,info_dict,sanitized_blog_url):# depricated by twkr's new tables
    """Set the date last saved to now"""
    logging.debug("Updating date last saved for: "+repr(sanitized_blog_url))
    date_last_saved = get_current_unix_time()
    statement = sqlalchemy.update(Blogs).\
        where(Blogs.c.blog_domain == sanitized_blog_url).\
        values(date_last_saved = date_last_saved)


    session.execute(statement)




def debug():
    """Temp code for debug"""
    session = connect_to_db()
    process_posts_media(session)
    #sanitized_username = "jessicaanner"
    #find_blog_posts(session,sanitized_username)


def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","sql-functions-log.txt"))
        debug()
        logging.info("Finished, exiting.")
        pass
    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return

if __name__ == '__main__':
    main()
