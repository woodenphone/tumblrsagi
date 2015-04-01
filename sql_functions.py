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




# SQLAlchemy table setup
Base = declarative_base()

class Blogs(Base):
    """Class that defines the Blog meta table in the DB"""
    #__table_args__ = {'useexisting': True}# Magic to fix some sort of import problem?
    __tablename__ = "blogs"
    # Columns
    # Locally generated
    primary_key = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)# Is used only as primary key
    date_added = sqlalchemy.Column(sqlalchemy.BigInteger)# Unix time of date first added to table
    date_last_saved = sqlalchemy.Column(sqlalchemy.BigInteger)# Unix time of date last saved
    # Posts table values
    poster_username = sqlalchemy.Column(sqlalchemy.String())# username for a blog, as given by the API "tsitra360"
    blog_domain = sqlalchemy.Column(sqlalchemy.String())# domain for the blog"tsitra360.tumblr.com"
    # From /info, documented
    info_title = sqlalchemy.Column(sqlalchemy.String())#String	The display title of the blog	Compare name
    info_posts = sqlalchemy.Column(sqlalchemy.String())#Number	The total number of posts to this blog
    info_name = sqlalchemy.Column(sqlalchemy.String())#String	The short blog name that appears before tumblr.com in a standard blog hostname (and before the domain in a custom blog hostname)	Compare title
    info_updated = sqlalchemy.Column(sqlalchemy.String())#	Number	The time of the most recent post, in seconds since the epoch
    info_description = sqlalchemy.Column(sqlalchemy.String())#String	You guessed it! The blog's description
    info_ask = sqlalchemy.Column(sqlalchemy.Boolean())#Boolean	Indicates whether the blog allows questions
    info_ask_anon = sqlalchemy.Column(sqlalchemy.Boolean())#	Boolean	Indicates whether the blog allows anonymous questions	Returned only if ask is true
    info_likes = sqlalchemy.Column(sqlalchemy.String())#Number	Number of likes for this user	Returned only if this is the user's primary blog and sharing of likes is enabled
    # From /info, undocumented
    info_is_nsfw = sqlalchemy.Column(sqlalchemy.Boolean())
    info_share_likes = sqlalchemy.Column(sqlalchemy.Boolean())
    info_url = sqlalchemy.Column(sqlalchemy.Boolean())
    info_ask_page_title = sqlalchemy.Column(sqlalchemy.String())


class Media(Base):
    """Class that defines the media table in the DB"""
    #__table_args__ = {'useexisting': True}# Magic to fix some sort of import problem?
    __tablename__ = "media"
    # Columns
    # Locally generated
    primary_key = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    date_added = sqlalchemy.Column(sqlalchemy.BigInteger)
    media_url = sqlalchemy.Column(sqlalchemy.String())
    sha512base64_hash = sqlalchemy.Column(sqlalchemy.String(250))
    local_filename = sqlalchemy.Column(sqlalchemy.String(250))# Filename on local storage, file path is deterministically generated from this
    remote_filename = sqlalchemy.Column(sqlalchemy.String())# Filename from original location (If any)
    file_extention = sqlalchemy.Column(sqlalchemy.String(250))# ex. .png, .jpeg
    extractor_used = sqlalchemy.Column(sqlalchemy.String(250))# internal name of the extractor used
    # Video
    # Youtube
    youtube_yt_dl_info_json = sqlalchemy.Column(sqlalchemy.String())
    youtube_video_id = sqlalchemy.Column(sqlalchemy.String(250))
    # Tubmlr video
    tumblrvideo_yt_dl_info_json = sqlalchemy.Column(sqlalchemy.String())
    # Vine Video embeds
    vine_yt_dl_info_json = sqlalchemy.Column(sqlalchemy.String())
    vine_video_id = sqlalchemy.Column(sqlalchemy.String(250))# https://vine.co/v/hjWIUFOYD31/embed/simple -> hjWIUFOYD31
    # Tumblr audio
    tumblraudio_album_art = sqlalchemy.Column(sqlalchemy.String())
    tumblraudio_artist = sqlalchemy.Column(sqlalchemy.String())
    # Vimeo embeds
    vimeo_yt_dl_info_json = sqlalchemy.Column(sqlalchemy.String())
    vimeo_video_id = sqlalchemy.Column(sqlalchemy.String())# https://player.vimeo.com/video/11891219 > 11891219
    # Audio
    # SoundCloud audio embeds
    soundcloud_id = sqlalchemy.Column(sqlalchemy.String())
    soundcloud_yt_dl_info_json = sqlalchemy.Column(sqlalchemy.String())



class Posts(Base):
    """The posts in a blog
    <type>_<api_field_name>
    https://www.tumblr.com/docs/en/api/v2"""
    #__table_args__ = {'useexisting': True}# Magic to fix some sort of import problem?
    __tablename__ = "posts"
    # Columns
    # Local stuff
    primary_key = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)# Is used only as primary key
    version = sqlalchemy.Column(sqlalchemy.BigInteger) # The version of this post this row is associated with
    date_saved = sqlalchemy.Column(sqlalchemy.BigInteger)# The unix time the post was saved
    link_to_hash_dict = sqlalchemy.Column(sqlalchemy.String())# mapping of links in the post to hashes of associated media
    # Who does this post belong to?
    poster_username = sqlalchemy.Column(sqlalchemy.String())# username for a blog, as given by the API "tsitra360"
    blog_domain = sqlalchemy.Column(sqlalchemy.String())# domain for the blog"tsitra360.tumblr.com"
    # Full post API data
    raw_post_json = sqlalchemy.Column(sqlalchemy.String())# The post's section of the API, reencoded into JSON
    processed_post_json = sqlalchemy.Column(sqlalchemy.String())# The post's section of the API, reencoded into JSON, after we've fucked with it
    # Missing from API docs
    misc_slug = sqlalchemy.Column(sqlalchemy.String())
    misc_short_url = sqlalchemy.Column(sqlalchemy.String())
    # From API
    # All Post Types
    all_posts_blog_name = sqlalchemy.Column(sqlalchemy.String())# String	The short name used to uniquely identify a blog
    all_posts_id = sqlalchemy.Column(sqlalchemy.BigInteger)# Number	The post's unique ID
    all_posts_post_url = sqlalchemy.Column(sqlalchemy.String())# String	The location of the post
    all_posts_type = sqlalchemy.Column(sqlalchemy.String())#String	The type of post	See the type request parameter
    all_posts_timestamp = sqlalchemy.Column(sqlalchemy.String())#	Number	The time of the post, in seconds since the epoch
    all_posts_date = sqlalchemy.Column(sqlalchemy.String())#	String	The GMT date and time of the post, as a string
    all_posts_format = sqlalchemy.Column(sqlalchemy.String())#String	The post format: html or markdown
    all_posts_reblog_key = sqlalchemy.Column(sqlalchemy.String())#	String	The key used to reblog this post	See the /post/reblog method
    all_posts_tags = sqlalchemy.Column(sqlalchemy.String())#Array (string)	Tags applied to the post
    all_posts_bookmarklet = sqlalchemy.Column(sqlalchemy.Boolean())#	Boolean	Indicates whether the post was created via the Tumblr bookmarklet	Exists only if true
    all_posts_mobile = sqlalchemy.Column(sqlalchemy.Boolean())#Boolean	Indicates whether the post was created via mobile/email publishing	Exists only if true
    all_posts_source_url = sqlalchemy.Column(sqlalchemy.String())#String	The URL for the source of the content (for quotes, reblogs, etc.)	Exists only if there's a content source
    all_posts_source_title = sqlalchemy.Column(sqlalchemy.String())#String	The title of the source site	Exists only if there's a content source
    all_posts_liked = sqlalchemy.Column(sqlalchemy.Boolean())#Boolean	Indicates if a user has already liked a post or not	Exists only if the request is fully authenticated with OAuth.
    all_posts_state = sqlalchemy.Column(sqlalchemy.String())# String	Indicates the current state of the post	States are published, queued, draft and private
    # Text Posts
    text_title = sqlalchemy.Column(sqlalchemy.String())#String	The optional title of the post
    text_body = sqlalchemy.Column(sqlalchemy.String())#String	The full post body
    # Photo posts
    photo_photos = sqlalchemy.Column(sqlalchemy.String())# Array	Photo objects with properties:
    photo_caption = sqlalchemy.Column(sqlalchemy.String())#	String	The user-supplied caption
    photo_width = sqlalchemy.Column(sqlalchemy.BigInteger)#	Number	The width of the photo or photoset
    photo_height = sqlalchemy.Column(sqlalchemy.BigInteger)#	Number	The height of the photo or photoset
    # Quote Posts
    quote_text = sqlalchemy.Column(sqlalchemy.String())# 	String	The text of the quote (can be modified by the user when posting)
    quote_source = sqlalchemy.Column(sqlalchemy.String())# 	String	Full HTML for the source of the quote
    # Link Posts
    link_title = sqlalchemy.Column(sqlalchemy.String())#	String	The title of the page the link points to
    link_url = sqlalchemy.Column(sqlalchemy.String())#	String	The link
    link_description = sqlalchemy.Column(sqlalchemy.String())#	String	A user-supplied description
    # Chat Posts
    chat_title = sqlalchemy.Column(sqlalchemy.String())
    chat_body = sqlalchemy.Column(sqlalchemy.String())
    chat_dialogue = sqlalchemy.Column(sqlalchemy.String())
    # Audio Posts
    audio_caption = sqlalchemy.Column(sqlalchemy.String())
    audio_player = sqlalchemy.Column(sqlalchemy.String())
    audio_plays = sqlalchemy.Column(sqlalchemy.BigInteger)
    audio_album_art = sqlalchemy.Column(sqlalchemy.String())
    audio_artist = sqlalchemy.Column(sqlalchemy.String())
    audio_album = sqlalchemy.Column(sqlalchemy.String())
    audio_track_name = sqlalchemy.Column(sqlalchemy.String())
    audio_track_number = sqlalchemy.Column(sqlalchemy.BigInteger)
    audio_year = sqlalchemy.Column(sqlalchemy.BigInteger)
    # Video Posts
    video_caption = sqlalchemy.Column(sqlalchemy.String())
    video_player = sqlalchemy.Column(sqlalchemy.String())
    # Answer Posts
    answer_asking_name = sqlalchemy.Column(sqlalchemy.String())
    answer_asking_url = sqlalchemy.Column(sqlalchemy.String())
    answer_question = sqlalchemy.Column(sqlalchemy.String())
    answer_answer = sqlalchemy.Column(sqlalchemy.String())
# /SQLAlchemy table setup


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


# Posts
def add_post_to_db(session,raw_post_dict,processed_post_dict,info_dict,blog_url,username):
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
    # Full post reencoded into JSON
    row_to_insert["raw_post_json"] = json.dumps(raw_post_dict)
    row_to_insert["processed_post_json"] = json.dumps(processed_post_dict)
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

    post_row = Posts(**row_to_insert)
    session.add(post_row)
    session.commit()
    return


def find_blog_posts(session,sanitized_username):
    """Lookup a blog's posts in the DB and return a list of the IDs"""
    logging.debug("find_blog_posts()"+"sanitized_username"+": "+repr(sanitized_username))
    # select all posts with field "poster_username" matching our value
    posts_query = sqlalchemy.select([Posts.all_posts_id]).where(Posts.poster_username == sanitized_username)
    posts_rows = session.execute(posts_query)
    post_ids = []
    for row in posts_rows:
        post_ids.append(row["all_posts_id"])
        #logging.debug("find_blog_posts()"+"row"+": "+repr(row))
    logging.debug("find_blog_posts()"+"post_ids"+": "+repr(post_ids))
    return post_ids


# Blogs metadata table
def insert_user_into_db(session,info_dict,sanitized_username,sanitized_blog_url):
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

def update_last_saved(session,info_dict,sanitized_blog_url):
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
    sanitized_username = "jessicaanner"
    find_blog_posts(session,sanitized_username)


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
