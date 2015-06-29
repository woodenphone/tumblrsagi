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
import sqlalchemy.dialects.postgresql # postgreSQL ORM (JSON, JSONB)

from utils import * # General utility functions


# SQLAlchemy table setup
Base = declarative_base()


# Twkr's new tables
class twkr_blogs(Base):
    """Class Info, functionality, purpose"""
    __tablename__ = "twkr_blogs"
    # Columns
    blog_id = sqlalchemy.Column(sqlalchemy.BigInteger, primary_key=True)# referenced by sub-tables
    blog_username = sqlalchemy.Column(sqlalchemy.UnicodeText())# UNUSED! REMOVE
    blog_url = sqlalchemy.Column(sqlalchemy.UnicodeText())# The URL fragment we use to ask the API for this blog, ex. "foo.tumblr.com"
    title = sqlalchemy.Column(sqlalchemy.UnicodeText())# Tumnlr API value
    postcount = sqlalchemy.Column(sqlalchemy.BigInteger)# Tumnlr API value
    name = sqlalchemy.Column(sqlalchemy.UnicodeText())# Tumnlr API value
    updated = sqlalchemy.Column(sqlalchemy.BigInteger) # Tumnlr API value for update time
    description = sqlalchemy.Column(sqlalchemy.UnicodeText())# Tumnlr API value for description
    ask = sqlalchemy.Column(sqlalchemy.Boolean())# Tumnlr API value
    alive = sqlalchemy.Column(sqlalchemy.Boolean())
    user_thumbnail_64_media_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("media.media_id")) # Local media ID for user's thumbnail
    user_thumbnail_512_media_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("media.media_id")) # Local media ID for user's thumbnail
    background_image_media_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("media.media_id")) # Local media ID for user's background image
    tags = sqlalchemy.Column(sqlalchemy.UnicodeText())# Comma seperated tags
    reasons_added = sqlalchemy.Column(sqlalchemy.dialects.postgresql.JSONB)# Why was this blog added? Populated initially by URLs in todo list ["url","URL",..]
    date_posts_last_saved  = sqlalchemy.Column(sqlalchemy.BigInteger)# Unix time of the last successful run



class twkr_posts(Base):
    """Class Info, functionality, purpose"""
    __tablename__ = "twkr_posts"
    # Columns
    # Local stuff
    post_id = sqlalchemy.Column(sqlalchemy.BigInteger(), primary_key=True)# referenced by sub-tables
    date_saved = sqlalchemy.Column(sqlalchemy.BigInteger())# The unix time the post was saved
    blog_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("twkr_blogs.blog_id")) #
    source_id = sqlalchemy.Column(sqlalchemy.BigInteger()) # ID number tumblr gave us for the post
    post_type = sqlalchemy.Column(sqlalchemy.SmallInteger()) # numerical identifier for what kind of post this is
    source_url = sqlalchemy.Column(sqlalchemy.UnicodeText()) # post_dict["post_url"]
    timestamp = sqlalchemy.Column(sqlalchemy.BigInteger()) # timestamp of post as given by API
    tags = sqlalchemy.Column(sqlalchemy.UnicodeText())# Comma seperated tags



class twkr_posts_photo(Base):
    """Class Info, functionality, purpose"""
    __tablename__ = "twkr_posts_photo"
    # Columns
    # Local stuff
    primary_key = sqlalchemy.Column(sqlalchemy.BigInteger(), primary_key=True)# Is used only as primary key
    caption = sqlalchemy.Column(sqlalchemy.UnicodeText())# photo["caption"]
    url = sqlalchemy.Column(sqlalchemy.UnicodeText())# photo["original_size"]["url"]
    order = sqlalchemy.Column(sqlalchemy.BigInteger()) # starting from 1 ex. 1, 2, 3...
    media_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("media.media_id")) # Local media ID
    post_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("twkr_posts.post_id")) # Local post ID


class twkr_posts_photo_text(Base):# Blame ATC
    """Class Info, functionality, purpose"""
    __tablename__ = "twkr_posts_photo_text"
    # Columns
    # Local stuff
    primary_key = sqlalchemy.Column(sqlalchemy.BigInteger(), primary_key=True)# Is used only as primary key
    caption = sqlalchemy.Column(sqlalchemy.UnicodeText())# post_dict["caption"]
    post_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("twkr_posts.post_id")) # Local post ID


class twkr_posts_link(Base):
    """Class Info, functionality, purpose"""
    __tablename__ = "twkr_posts_link"
    # Columns
    # Local stuff
    primary_key = sqlalchemy.Column(sqlalchemy.BigInteger(), primary_key=True)# Is used only as primary key
    source_url = sqlalchemy.Column(sqlalchemy.UnicodeText())# post_dict["url"]
    source_title = sqlalchemy.Column(sqlalchemy.UnicodeText())# post_dict["title"]
    description = sqlalchemy.Column(sqlalchemy.UnicodeText())# post_dict["description"]
    post_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("twkr_posts.post_id")) #


class twkr_posts_answer(Base):
    """Class Info, functionality, purpose"""
    __tablename__ = "twkr_posts_answer"
    # Columns
    # Local stuff
    primary_key = sqlalchemy.Column(sqlalchemy.BigInteger(), primary_key=True)# Is used only as primary key
    asking_name = sqlalchemy.Column(sqlalchemy.UnicodeText())# post_dict["asking_name"]
    asking_url = sqlalchemy.Column(sqlalchemy.UnicodeText())# post_dict["asking_url"]
    question = sqlalchemy.Column(sqlalchemy.UnicodeText())# post_dict["question"]
    answer = sqlalchemy.Column(sqlalchemy.UnicodeText())# post_dict["answer"]
    post_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("twkr_posts.post_id")) #



class twkr_posts_text(Base):
    """Class Info, functionality, purpose"""
    __tablename__ = "twkr_posts_text"
    # Columns
    # Local stuff
    primary_key = sqlalchemy.Column(sqlalchemy.BigInteger(), primary_key=True)# Is used only as primary key
    title = sqlalchemy.Column(sqlalchemy.UnicodeText())# post_dict["title"]
    body = sqlalchemy.Column(sqlalchemy.UnicodeText())# post_dict["body"]
    post_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("twkr_posts.post_id")) #



class twkr_posts_quote(Base):
    """Class Info, functionality, purpose"""
    __tablename__ = "twkr_posts_quote"
    # Columns
    # Local stuff
    primary_key = sqlalchemy.Column(sqlalchemy.BigInteger(), primary_key=True)# Is used only as primary key
    source_url = sqlalchemy.Column(sqlalchemy.UnicodeText())# post_dict["source_url"] (optional)
    source_title = sqlalchemy.Column(sqlalchemy.UnicodeText())# post_dict["source_title"] (optional)
    source = sqlalchemy.Column(sqlalchemy.UnicodeText())# post_dict["source"] source text (the guy who is being quoted)
    text = sqlalchemy.Column(sqlalchemy.UnicodeText())# post_dict["text"] text from whoever made this post
    post_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("twkr_posts.post_id")) #



class twkr_posts_chat(Base):
    """Class Info, functionality, purpose"""
    __tablename__ = "twkr_posts_chat"
    # Columns
    # Local stuff
    primary_key = sqlalchemy.Column(sqlalchemy.BigInteger(), primary_key=True)# Is used only as primary key
    title = sqlalchemy.Column(sqlalchemy.UnicodeText())# post_dict["title"]
    body = sqlalchemy.Column(sqlalchemy.UnicodeText())# post_dict["body"]
    dialogue_html = sqlalchemy.Column(sqlalchemy.UnicodeText())# None
    dialogue_json = sqlalchemy.Column(sqlalchemy.dialects.postgresql.JSONB(none_as_null=False))# json.dumps(post_dict["dialogue"])
    post_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("twkr_posts.post_id")) #



class twkr_post_reblog_trail(Base):# Blame ATC
    """Class Info, functionality, purpose"""
    __tablename__ = "twkr_post_reblog_trail"
    # Columns
    primary_key = sqlalchemy.Column(sqlalchemy.BigInteger(), primary_key=True)# Is used only as primary key
    post_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("twkr_posts.post_id")) #Local post id
    depth = sqlalchemy.Column(sqlalchemy.BigInteger())# Starting at 1 for the first reply, how deep is this?
    content = sqlalchemy.Column(sqlalchemy.UnicodeText())# ["response"]["posts"]["trail"][depth-1]["content']



class twkr_post_audio(Base):# Blame ATC
    """Class Info, functionality, purpose"""
    __tablename__ = "twkr_post_audio"
    # Columns
    primary_key = sqlalchemy.Column(sqlalchemy.BigInteger(), primary_key=True)# Is used only as primary key
    post_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("twkr_posts.post_id")) # Local post ID
    caption = sqlalchemy.Column(sqlalchemy.UnicodeText())# from API, beyond that uncertain
    artist = sqlalchemy.Column(sqlalchemy.UnicodeText())# Artist name
    track_name = sqlalchemy.Column(sqlalchemy.UnicodeText())# Track name
    album = sqlalchemy.Column(sqlalchemy.UnicodeText())# Name of the album
    audio_source_url = sqlalchemy.Column(sqlalchemy.UnicodeText())# from API, beyond that uncertain
    audio_type = sqlalchemy.Column(sqlalchemy.UnicodeText())# from API, beyond that uncertain
    source_title = sqlalchemy.Column(sqlalchemy.UnicodeText())# from API, beyond that uncertain
    album_art_url = sqlalchemy.Column(sqlalchemy.UnicodeText())# from API, beyond that uncertain



class twkr_post_video(Base):# Blame ATC
    """Class Info, functionality, purpose"""
    __tablename__ = "twkr_post_video"
    # Columns
    primary_key = sqlalchemy.Column(sqlalchemy.BigInteger(), primary_key=True)# Is used only as primary key
    post_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("twkr_posts.post_id")) # Local post ID
    caption = sqlalchemy.Column(sqlalchemy.UnicodeText())# from API, beyond that uncertain
    video_type = sqlalchemy.Column(sqlalchemy.UnicodeText())# from API, beyond that uncertain
    permalink_url = sqlalchemy.Column(sqlalchemy.UnicodeText())# from API, beyond that uncertain
    thumbnail_url = sqlalchemy.Column(sqlalchemy.UnicodeText())# from API, beyond that uncertain


# /Twkr's new tables



# Raw API data archive table
class RawPosts(Base):# Remove underscore after fixing all references
    """The raw post dicts for a blog
    Used to back up and stage posts
    Write-once Read-many"""
    __tablename__ = "raw_posts"
    # Columns
    # Local stuff
    primary_key = sqlalchemy.Column(sqlalchemy.BigInteger, primary_key=True)# Is used only as primary key
    version = sqlalchemy.Column(sqlalchemy.BigInteger) # The version of this post this row is associated with
    date_saved = sqlalchemy.Column(sqlalchemy.BigInteger)# The unix time the post was saved
    link_to_hash_dict = sqlalchemy.Column(sqlalchemy.dialects.postgresql.JSONB)# mapping of links in the post to hashes of associated media
    # Who does this post belong to?
    poster_username = sqlalchemy.Column(sqlalchemy.UnicodeText())# username for a blog, as given by the API "tsitra360"
    blog_domain = sqlalchemy.Column(sqlalchemy.UnicodeText())# domain for the blog"tsitra360.tumblr.com"
    # Post identity from the post
    all_posts_id = sqlalchemy.Column(sqlalchemy.BigInteger)# Number	The post's non-unique ID
    all_posts_post_url = sqlalchemy.Column(sqlalchemy.UnicodeText())# String	The location of the post
    all_posts_timestamp  = sqlalchemy.Column(sqlalchemy.BigInteger)# The API given timestamp
    # Full post API data
    raw_post_json = sqlalchemy.Column(sqlalchemy.dialects.postgresql.JSONB)# The post's section of the API, reencoded into JSON
    media_processed = sqlalchemy.Column(sqlalchemy.Boolean)# has media been processed for this post?


# Media tables
class Media(Base):
    """Class that defines the media table in the DB"""
    __tablename__ = "media"
    # Columns
    # Locally generated
    media_id = sqlalchemy.Column(sqlalchemy.BigInteger, primary_key=True)# associated with posts via association table
    date_added = sqlalchemy.Column(sqlalchemy.BigInteger)# The unix time the media was saved
    media_url = sqlalchemy.Column(sqlalchemy.UnicodeText())# Should have a constant length since it's a hash
    sha512base16_hash = sqlalchemy.Column(sqlalchemy.dialects.postgresql.CHAR(128))
    local_filename = sqlalchemy.Column(sqlalchemy.String(250))# Filename on local storage, file path is deterministically generated from this
    remote_filename = sqlalchemy.Column(sqlalchemy.UnicodeText())# Filename from original location (If any)
    file_extention = sqlalchemy.Column(sqlalchemy.String(25))# ex. png, jpeg
    extractor_used = sqlalchemy.Column(sqlalchemy.String(250))# internal name of the extractor used (function name of extractor)
    # Video and Audio use these
    yt_dl_info_json = sqlalchemy.Column(sqlalchemy.UnicodeText())
    video_id = sqlalchemy.Column(sqlalchemy.UnicodeText())# The ID of the video used by the originating site
    audio_id = sqlalchemy.Column(sqlalchemy.UnicodeText())# The ID of the audio used by the originating site
    annotations = sqlalchemy.Column(sqlalchemy.UnicodeText())



class media_associations(Base):
    """Tell a post what media it has saved"""
    __tablename__ = "media_associations"
    primary_key = sqlalchemy.Column(sqlalchemy.BigInteger(), primary_key=True)# Is used only as primary key
    post_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("twkr_posts.post_id")) # Local post ID
    media_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("media.media_id")) # Local media ID
# /Media
# Media Extractors

class handler_api_youtube(Base):#not yet used
    """Record which posts have been checked against which versions
    of the API youtube emebed media handler"""
    __tablename__ = "handler_api_youtube"
    primary_key = sqlalchemy.Column(sqlalchemy.BigInteger(), primary_key=True)
    blog_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("twkr_blogs.blog_id")) #
    extractor_version = sqlalchemy.Column(sqlalchemy.BigInteger)# Which is the highest version of the extractor that has been used on this post?
# /Media Extractors



# Admin tables
class meta_reports(Base):
    """Page reports.
    Most of the code relating to this is on the display side."""
    __tablename__ = "meta_reports"
    primary_key = sqlalchemy.Column(sqlalchemy.BigInteger(), primary_key=True)# Is used only as primary key
    url = sqlalchemy.Column(sqlalchemy.UnicodeText())
    email = sqlalchemy.Column(sqlalchemy.UnicodeText())
    comment = sqlalchemy.Column(sqlalchemy.UnicodeText())
    ip = sqlalchemy.Column(sqlalchemy.UnicodeText())
    time  = sqlalchemy.Column(sqlalchemy.BigInteger)

class meta_requests(Base):
    """Requests for new blogs to add to the archive.
    Most of the code relating to this is on the display side."""
    __tablename__ = "meta_requests"
    primary_key = sqlalchemy.Column(sqlalchemy.BigInteger(), primary_key=True)# Is used only as primary key
    url = sqlalchemy.Column(sqlalchemy.UnicodeText())
    email = sqlalchemy.Column(sqlalchemy.UnicodeText())
    comment = sqlalchemy.Column(sqlalchemy.UnicodeText())
    ip = sqlalchemy.Column(sqlalchemy.UnicodeText())
    time  = sqlalchemy.Column(sqlalchemy.BigInteger)
# /Admin tables



# Tables on the server we need to be able to handle
class vm_RawPosts(Base):# Live DB on server uses this
    """The raw post dicts for a blog
    Used to back up and stage posts
    Write-once Read-many"""
    __tablename__ = "vm_raw_posts"
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



class vm_Media(Base):# Live DB on server uses this
     """Class that defines the media table in the DB"""
     __tablename__ = "vm_media"
     # Columns
     # Locally generated
     primary_key = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)# Only used as a primary key
     date_added = sqlalchemy.Column(sqlalchemy.BigInteger)# The unix time the media was saved
     media_url = sqlalchemy.Column(sqlalchemy.UnicodeText())# Should have a constant length since it's a hash
     sha512base64_hash = sqlalchemy.Column(sqlalchemy.String(88))
     sha512base64_hash = sqlalchemy.Column(sqlalchemy.dialects.postgresql.CHAR(88))
     local_filename = sqlalchemy.Column(sqlalchemy.String(250))# Filename on local storage, file path is deterministically generated from this
     remote_filename = sqlalchemy.Column(sqlalchemy.UnicodeText())# Filename from original location (If any)
     file_extention = sqlalchemy.Column(sqlalchemy.String(25))# ex. png, jpeg
     extractor_used = sqlalchemy.Column(sqlalchemy.String(250))# internal name of the extractor used (function name of extractor)
     # Video and Audio use these
     yt_dl_info_json = sqlalchemy.Column(sqlalchemy.UnicodeText())
     video_id = sqlalchemy.Column(sqlalchemy.UnicodeText())# The ID of the video used by the originating site
     audio_id = sqlalchemy.Column(sqlalchemy.UnicodeText())# The ID of the audio used by the originating site
     annotations = sqlalchemy.Column(sqlalchemy.UnicodeText())
# /live server tables
# /SQLAlchemy table setup



def create_example_db_sqllite():
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

def create_example_db_postgres():
    """Provide a DB session
    http://www.pythoncentral.io/introductory-tutorial-python-sqlalchemy/"""
    logging.debug("Opening DB connection")
    # add "echo=True" to see SQL being run
    # postgresql://username:password@host/database_name
    engine = sqlalchemy.create_engine("postgresql://postgres:postgres@localhost/example", echo=True)
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
    create_example_db_postgres()

if __name__ == '__main__':
    main()
