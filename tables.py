#-------------------------------------------------------------------------------
# Name:        tables
# Purpose:  define the database for SQLAlchemy
#
# Author:      User
#
# Created:     08/04/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import sqlalchemy# Database library
from sqlalchemy.ext.declarative import declarative_base# Magic for ORM

from utils import * # General utility functions


# SQLAlchemy table setup
Base = declarative_base()

# Blogs metadata table
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
    poster_username = sqlalchemy.Column(sqlalchemy.UnicodeText())# username for a blog, as given by the API "tsitra360"
    blog_domain = sqlalchemy.Column(sqlalchemy.UnicodeText())# domain for the blog"tsitra360.tumblr.com"
    # From /info, documented
    info_title = sqlalchemy.Column(sqlalchemy.UnicodeText())#String	The display title of the blog	Compare name
    info_posts = sqlalchemy.Column(sqlalchemy.UnicodeText())#Number	The total number of posts to this blog
    info_name = sqlalchemy.Column(sqlalchemy.UnicodeText())#String	The short blog name that appears before tumblr.com in a standard blog hostname (and before the domain in a custom blog hostname)	Compare title
    info_updated = sqlalchemy.Column(sqlalchemy.UnicodeText())#	Number	The time of the most recent post, in seconds since the epoch
    info_description = sqlalchemy.Column(sqlalchemy.UnicodeText())#String	You guessed it! The blog's description
    info_ask = sqlalchemy.Column(sqlalchemy.Boolean())#Boolean	Indicates whether the blog allows questions
    info_ask_anon = sqlalchemy.Column(sqlalchemy.Boolean())#	Boolean	Indicates whether the blog allows anonymous questions	Returned only if ask is true
    info_likes = sqlalchemy.Column(sqlalchemy.UnicodeText())#Number	Number of likes for this user	Returned only if this is the user's primary blog and sharing of likes is enabled
    # From /info, undocumented
    info_is_nsfw = sqlalchemy.Column(sqlalchemy.Boolean())
    info_share_likes = sqlalchemy.Column(sqlalchemy.Boolean())
    info_url = sqlalchemy.Column(sqlalchemy.Boolean())
    info_ask_page_title = sqlalchemy.Column(sqlalchemy.UnicodeText())


# Media tables
class Media(Base):
    """Class that defines the media table in the DB"""
    #__table_args__ = {'useexisting': True}# Magic to fix some sort of import problem?
    __tablename__ = "media"
    # Columns
    # Locally generated
    primary_key = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    date_added = sqlalchemy.Column(sqlalchemy.BigInteger)
    media_url = sqlalchemy.Column(sqlalchemy.UnicodeText())
    sha512base64_hash = sqlalchemy.Column(sqlalchemy.String(250))
    local_filename = sqlalchemy.Column(sqlalchemy.String(250))# Filename on local storage, file path is deterministically generated from this
    remote_filename = sqlalchemy.Column(sqlalchemy.UnicodeText())# Filename from original location (If any)
    file_extention = sqlalchemy.Column(sqlalchemy.String(250))# ex. .png, .jpeg
    extractor_used = sqlalchemy.Column(sqlalchemy.String(250))# internal name of the extractor used
    # Video and Audio use these
    yt_dl_info_json = sqlalchemy.Column(sqlalchemy.UnicodeText())
    video_id = sqlalchemy.Column(sqlalchemy.UnicodeText())
    audio_id = sqlalchemy.Column(sqlalchemy.UnicodeText())
    annotations = sqlalchemy.Column(sqlalchemy.UnicodeText())


# /Media

# Posts tables
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
    link_to_hash_dict = sqlalchemy.Column(sqlalchemy.UnicodeText())# mapping of links in the post to hashes of associated media
    # Who does this post belong to?
    poster_username = sqlalchemy.Column(sqlalchemy.UnicodeText())# username for a blog, as given by the API "tsitra360"
    blog_domain = sqlalchemy.Column(sqlalchemy.UnicodeText())# domain for the blog"tsitra360.tumblr.com"
    # Missing from API docs
    misc_slug = sqlalchemy.Column(sqlalchemy.UnicodeText())
    misc_short_url = sqlalchemy.Column(sqlalchemy.UnicodeText())
    # From API
    # All Post Types
    all_posts_blog_name = sqlalchemy.Column(sqlalchemy.UnicodeText())# String	The short name used to uniquely identify a blog
    all_posts_id = sqlalchemy.Column(sqlalchemy.BigInteger)# Number	The post's unique ID
    all_posts_post_url = sqlalchemy.Column(sqlalchemy.UnicodeText())# String	The location of the post
    all_posts_type = sqlalchemy.Column(sqlalchemy.UnicodeText())#String	The type of post	See the type request parameter
    all_posts_timestamp = sqlalchemy.Column(sqlalchemy.UnicodeText())#	Number	The time of the post, in seconds since the epoch
    all_posts_date = sqlalchemy.Column(sqlalchemy.UnicodeText())#	String	The GMT date and time of the post, as a string
    all_posts_format = sqlalchemy.Column(sqlalchemy.UnicodeText())#String	The post format: html or markdown
    all_posts_reblog_key = sqlalchemy.Column(sqlalchemy.UnicodeText())#	String	The key used to reblog this post	See the /post/reblog method
    all_posts_tags = sqlalchemy.Column(sqlalchemy.UnicodeText())#Array (string)	Tags applied to the post
    all_posts_bookmarklet = sqlalchemy.Column(sqlalchemy.Boolean())#	Boolean	Indicates whether the post was created via the Tumblr bookmarklet	Exists only if true
    all_posts_mobile = sqlalchemy.Column(sqlalchemy.Boolean())#Boolean	Indicates whether the post was created via mobile/email publishing	Exists only if true
    all_posts_source_url = sqlalchemy.Column(sqlalchemy.UnicodeText())#String	The URL for the source of the content (for quotes, reblogs, etc.)	Exists only if there's a content source
    all_posts_source_title = sqlalchemy.Column(sqlalchemy.UnicodeText())#String	The title of the source site	Exists only if there's a content source
    all_posts_liked = sqlalchemy.Column(sqlalchemy.Boolean())#Boolean	Indicates if a user has already liked a post or not	Exists only if the request is fully authenticated with OAuth.
    all_posts_state = sqlalchemy.Column(sqlalchemy.UnicodeText())# String	Indicates the current state of the post	States are published, queued, draft and private
    # Text Posts
    text_title = sqlalchemy.Column(sqlalchemy.UnicodeText())#String	The optional title of the post
    text_body = sqlalchemy.Column(sqlalchemy.UnicodeText())#String	The full post body
    # Photo posts
    photo_photos = sqlalchemy.Column(sqlalchemy.UnicodeText())# Array	Photo objects with properties:
    photo_caption = sqlalchemy.Column(sqlalchemy.UnicodeText())#	String	The user-supplied caption
    photo_width = sqlalchemy.Column(sqlalchemy.BigInteger)#	Number	The width of the photo or photoset
    photo_height = sqlalchemy.Column(sqlalchemy.BigInteger)#	Number	The height of the photo or photoset
    # Quote Posts
    quote_text = sqlalchemy.Column(sqlalchemy.UnicodeText())# 	String	The text of the quote (can be modified by the user when posting)
    quote_source = sqlalchemy.Column(sqlalchemy.UnicodeText())# 	String	Full HTML for the source of the quote
    # Link Posts
    link_title = sqlalchemy.Column(sqlalchemy.UnicodeText())#	String	The title of the page the link points to
    link_url = sqlalchemy.Column(sqlalchemy.UnicodeText())#	String	The link
    link_description = sqlalchemy.Column(sqlalchemy.UnicodeText())#	String	A user-supplied description
    # Chat Posts
    chat_title = sqlalchemy.Column(sqlalchemy.UnicodeText())
    chat_body = sqlalchemy.Column(sqlalchemy.UnicodeText())
    chat_dialogue = sqlalchemy.Column(sqlalchemy.UnicodeText())
    # Audio Posts
    audio_caption = sqlalchemy.Column(sqlalchemy.UnicodeText())
    audio_player = sqlalchemy.Column(sqlalchemy.UnicodeText())
    audio_plays = sqlalchemy.Column(sqlalchemy.BigInteger)
    audio_album_art = sqlalchemy.Column(sqlalchemy.UnicodeText())
    audio_artist = sqlalchemy.Column(sqlalchemy.UnicodeText())
    audio_album = sqlalchemy.Column(sqlalchemy.UnicodeText())
    audio_track_name = sqlalchemy.Column(sqlalchemy.UnicodeText())
    audio_track_number = sqlalchemy.Column(sqlalchemy.BigInteger)
    audio_year = sqlalchemy.Column(sqlalchemy.BigInteger)
    # Video Posts
    video_caption = sqlalchemy.Column(sqlalchemy.UnicodeText())
    video_player = sqlalchemy.Column(sqlalchemy.UnicodeText())
    # Answer Posts
    answer_asking_name = sqlalchemy.Column(sqlalchemy.UnicodeText())
    answer_asking_url = sqlalchemy.Column(sqlalchemy.UnicodeText())
    answer_question = sqlalchemy.Column(sqlalchemy.UnicodeText())
    answer_answer = sqlalchemy.Column(sqlalchemy.UnicodeText())

class RawPosts(Base):
    """The raw post dicts for a blog"""
    __tablename__ = "raw_posts"
    # Columns
    # Local stuff
    primary_key = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)# Is used only as primary key
    version = sqlalchemy.Column(sqlalchemy.BigInteger) # The version of this post this row is associated with
    date_saved = sqlalchemy.Column(sqlalchemy.BigInteger)# The unix time the post was saved
    link_to_hash_dict = sqlalchemy.Column(sqlalchemy.UnicodeText())# mapping of links in the post to hashes of associated media
    # Who does this post belong to?
    poster_username = sqlalchemy.Column(sqlalchemy.UnicodeText())# username for a blog, as given by the API "tsitra360"
    blog_domain = sqlalchemy.Column(sqlalchemy.UnicodeText())# domain for the blog"tsitra360.tumblr.com"
    # Post identity from the post
    all_posts_id = sqlalchemy.Column(sqlalchemy.BigInteger)# Number	The post's unique ID
    all_posts_post_url = sqlalchemy.Column(sqlalchemy.UnicodeText())# String	The location of the post
    # Full post API data
    raw_post_json = sqlalchemy.Column(sqlalchemy.UnicodeText())# The post's section of the API, reencoded into JSON
    processed_post_json = sqlalchemy.Column(sqlalchemy.UnicodeText())# The post's section of the API, reencoded into JSON, after we've fucked with it
# /SQLAlchemy table setup


def create_example_db():
    """Provide a DB session
    http://www.pythoncentral.io/introductory-tutorial-python-sqlalchemy/"""
    logging.debug("Opening DB connection")
    # add "echo=True" to see SQL being run
    engine = sqlalchemy.create_engine("sqlite:///tables_example.sqllite", echo=True)
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
    session.commit()

    logging.debug("Example DB created")
    return


def main():
    setup_logging(log_file_path=os.path.join("debug","tables-log.txt"))
    create_example_db()

if __name__ == '__main__':
    main()
