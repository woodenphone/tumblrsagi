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
from sqlalchemy.ext.declarative import declarative_base

from utils import *

import config # User specific settings

Base = declarative_base()

# SQLAlchemy table setup
class Blogs(Base):
    """Class that defines the Blog meta table in the DB"""
    __tablename__ = "media"
    # Columns
    # Locally generated
    primary_key = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)# Is used only as primary key
    date_added = sqlalchemy.Column(sqlalchemy.Integer)# Unix time of date first added to table
    date_last_saved = sqlalchemy.Column(sqlalchemy.Integer)# Unix time of date last saved
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
    __tablename__ = "media"
    # Columns
    # Locally generated
    primary_key = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    date_added = sqlalchemy.Column(sqlalchemy.Integer)
    media_url = sqlalchemy.Column(sqlalchemy.String())
    sha512base64_hash = sqlalchemy.Column(sqlalchemy.String(250))
    filename = sqlalchemy.Column(sqlalchemy.String(250))
    extractor_used = sqlalchemy.Column(sqlalchemy.String(250))
    # Youtube
    youtube_yt_dl_info_json = sqlalchemy.Column(sqlalchemy.String())
    youtube_video_id = sqlalchemy.Column(sqlalchemy.String(250))
    # Tubmlr video
    tumblrvideo_yt_dl_info_json = sqlalchemy.Column(sqlalchemy.String())
    # Tumblr audio
    tumblraudio_album_art = sqlalchemy.Column(sqlalchemy.String())
    tumblraudio_artist = sqlalchemy.Column(sqlalchemy.String())
    # SoundCloud audio embeds
    soundcloud_id = sqlalchemy.Column(sqlalchemy.String())

class Posts(Base):
    """The posts in a blog
    <type>_<api_field_name>
    https://www.tumblr.com/docs/en/api/v2"""
    __tablename__ = "posts"
    # Columns
    # Local stuff
    primary_key = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)# Is used only as primary key
    version = sqlalchemy.Column(sqlalchemy.BigInteger) # The version of this post this row is associated with
    date_saved = sqlalchemy.Column(sqlalchemy.BigInteger)# The unix time the post was saved
    link_to_hash_dict = sqlalchemy.Column(sqlalchemy.String())# mapping of links in the post to hashes of associated media
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


# Media
def check_if_hash_in_db(session,sha512base64_hash):
    """Check if a hash is in the media DB
    Return a dict of the first found row if it is, otherwise return None"""
    hash_query = sqlalchemy.select([Media]).where(Media.sha512base64_hash == sha512base64_hash)
    hash_rows = session.execute(hash_query)
    hash_row = hash_rows.fetchone()
    if hash_row:
        hash_row_dict = row2dict(hash_row)
        return hash_row_dict
    else:
        return None


##def row2dict(row):
##    """Torn a SQLAlchemy row into a dict
##    http://stackoverflow.com/questions/1958219/convert-sqlalchemy-row-object-to-python-dict"""
##    return {c.name: getattr(row, c.name) for c in row.__table__.columns}
row2dict = lambda r: dict(r.items())

def check_if_media_url_in_DB(session,media_url):
    """Check if a URL is in the media DB
    Return a dict of the first found row if it is, otherwise return None"""
    media_url_query = sqlalchemy.select([Media]).where(Media.media_url == media_url)
    media_url_rows = session.execute(media_url_query)
    media_url_row = media_url_rows.fetchone()
    if media_url_row:
        media_url_row_dict = row2dict(media_url_row)
        return media_url_row_dict
    else:
        return None

# Posts
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

def find_blog_posts(connection,blog_username):
    """Lookup a blog's posts in the DB and return a list of the IDs"""
    logging.warning("Posts lookup not implimented")# TODO FIXME
    return []
# Blogs metadata table

def add_blog_to_db(connection,info_dict):
    """Insert blog info into the DB"""
    cursor =  connection.cursor()
    logging.debug("info_dict: "+repr(info_dict))
    row_to_insert = {} # TODO, Waiting on ATC for DB design # actually fuck waiting he can clean this up later
    # Local stuff
    row_to_insert["date_last_saved"] = get_current_unix_time()
    # from /info, documented
    row_to_insert["info_title"] = info_dict["title"]
    row_to_insert["info_posts"] = info_dict["posts"]
    row_to_insert["info_name"] = info_dict["name"]
    row_to_insert["info_updated"] = info_dict["updated"]
    row_to_insert["info_description"] = info_dict["description"]
    row_to_insert["info_ask"] = info_dict["ask"]
    row_to_insert["info_ask_anon"] = info_dict["ask_anon"]
    row_to_insert["info_likes"] = info_dict["likes"]
    # from /info, undocumented
    row_to_insert["info_is_nsfw"] = (info_dict["is_nsfw"] if ("is_nsfw" in info_dict.keys()) else None)# Undocumented
    row_to_insert["info_share_likes"] = (info_dict["share_likes"] if ("share_likes" in info_dict.keys()) else None)# Undocumented
    row_to_insert["info_url"] = (info_dict["url"] if ("url" in info_dict.keys()) else None)# Undocumented
    row_to_insert["info_ask_page_title"] = (info_dict["ask_page_title"] if ("ask_page_title" in info_dict.keys()) else None)# Undocumented
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







def main():
    pass

if __name__ == '__main__':
    main()
