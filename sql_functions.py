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
    logging.debug("sql_functions.lookup_media_hash() media_url_row:"+repr(media_url_row))
    if media_url_row:
        return media_url_row
    else:
        return None


# Raw Posts
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
    row_to_insert["all_posts_timestamp"] = raw_post_dict["timestamp"]
    # Full post reencoded into JSON
    row_to_insert["raw_post_json"] = raw_post_dict
    row_to_insert["processed_post_json"] = processed_post_dict
    logging.debug("row_to_insert:"+repr(row_to_insert))

    post_row = RawPosts(**row_to_insert)
    session.add(post_row)
    session.commit()
    read_post(session,post_url = raw_post_dict["post_url"])
    return


def read_post(session,post_url):
    posts_query = sqlalchemy.select([RawPosts]).\
        where(RawPosts.all_posts_post_url == post_url)
    posts_rows = session.execute(posts_query)
    post_ids = []
    for row in posts_rows:
        logging.debug("row in db:"+repr(row))
    return


def find_blog_posts(session,sanitized_username):# TODO Replace this with one that gives timestamps as well
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


def get_timestamp_of_last_post(session,blog_domain):
    """Look up the timestamp for the most recent post for this blog
    If timestamp exists return it, otherwise return 0"""
    # Grab the highest timestamp for this blog
    timestamp_query = sqlalchemy.select([RawPosts]).\
        where(RawPosts.blog_domain == blog_domain).\
        order_by(RawPosts.all_posts_timestamp.desc())
    timestamp_rows = session.execute(timestamp_query)
    timestamp_row = timestamp_rows.fetchone()
    if timestamp_row:
        return timestamp_row["all_posts_timestamp"]
    else:
        return 0
# /Raw Posts



# Posts for website and stuff
def map_post_type(post_type_string):
    """Map API post types to integers for faster DB stuff"""
    string_to_int_table = {
        u"text":1,
        u"photo":2,
        u"quote":3,
        u"link":4,
        u"chat":5,
        u"audio":6,
        u"video":7,
        u"answer":8,
        }
    return string_to_int_table[post_type_string]

def reverse_map_post_type(type_id):
    int_to_string_table = {
        1: u'text',
        2: u'photo',
        3: u'quote',
        4: u'link',
        5: u'chat',
        6: u'audio',
        7: u'video',
        8: u'answer'
         }
    return int_to_string_table[type_id]


def insert_post_media_associations(session,post_id,media_hash_dict):
    # Find associations already in the db for this post and skip them
    new_media_hashes = {}# {link:hash}
    for media_url in media_hash_dict.keys():# {link:hash}
        media_hash = media_hash_dict[media_url]
        select_hash_query = sqlalchemy.select([media_associations]).\
            where(media_associations.sha512base64_hash == media_hash).\
            where(media_associations.post_id == post_id)
        select_hash_rows = session.execute(select_hash_query)
        select_hash_row = select_hash_rows.fetchone()
        if select_hash_row:
            logging.debug("Skipping duplicate association: "+repr(media_hash))
        else:
            new_media_hashes[media_url] = media_hash
        continue

    # Add entries to the post-media association table
    for new_media_url in new_media_hashes:
        new_media_hash = new_media_hashes[new_media_url]
        # Ensure hash is valid
        assert(len(new_media_hash) == 88)# Hash is constant length

        # Ensure the hash is actually in the Media table
        verify_hash_query = sqlalchemy.select([Media]).\
            where(Media.sha512base64_hash == new_media_hash)
        verify_hash_rows = session.execute(verify_hash_query)
        verify_hash_row = verify_hash_rows.fetchone()
        logging.debug("Media row associated with this hash:"+repr(verify_hash_row))
        verify_hash = verify_hash_row["sha512base64_hash"]
        if verify_hash:
            # Insert hash
            media_association_row = media_associations(
                post_id = post_id,
                sha512base64_hash = new_media_hash
                )
            session.add(media_association_row)
            continue
        else:
            # The hash we were given is not in the Media table!
            # Make a fuss if the value is not in the media DB
            logging.error("Hash was not found in the Media table! Somethign is wrong!")
            logging.error(repr(locals()))
            raise ValueError
    return


def insert_one_post(session,post_dict,blog_id,media_hash_dict):# WIP
    """Insert a single post into Twkr's new postgres tables
    Only commit if all tables are set
    Return True if successful.
    """
    assert(type(post_dict) is type({}))
    #assert(type(blog_id) is type(1))
    assert(type(media_hash_dict) is type({}))
    # Generate a unique ID for the post
    #post_id = get_current_unix_time()#post_dict["id"]# I don't trust this but it's good enough for testing
    logging.warning("Fix post_id! Unsafe for primary key")

    # Insert into twkr_posts table
    posts_dict = {}
    #posts_dict["field"] = "value" # Example of setting a field
    #posts_dict["post_id"] = post_id
    posts_dict["date_saved"] = get_current_unix_time() # Unix time to millisecond precision
    posts_dict["blog_id"] = blog_id # local ID number of the blog
    posts_dict["source_id"] = post_dict["id"] # ID number tumblr gave us for the post
    posts_dict["post_type"] = map_post_type(post_dict["type"]) #
    posts_dict["source_url"] = post_dict["post_url"] # using value the API gave us
    posts_dict["timestamp"] = post_dict["timestamp"] # using value the API gave us

    posts_row = twkr_posts(**posts_dict)
    session.add(posts_row)

    logging.debug("committing post row")
    session.commit()# We have to commit this first for some reason?
    post_id = posts_row.post_id
    print post_id

    # Add entries to the post-media association table
    logging.debug("adding media associations")
    insert_post_media_associations(session,post_id,media_hash_dict)

    # If photo, insert into posts_photo table
    if (post_dict["type"] == "photo"):
        logging.debug("posts_photo")
        # Add each photo to a row in the photos table
        photos = post_dict["photos"]
        photo_num = 0
        for photo in photos:
            photo_num += 1
            photo_url = photo["original_size"]["url"]
            posts_photo_dict = {}

            posts_photo_dict["caption"] = photo["caption"]
            posts_photo_dict["url"] = photo_url
            posts_photo_dict["order"] = photo_num
            posts_photo_dict["sha512b64"] = "FIXME"#post_dict["links"][photo_url]
            posts_photo_dict["post_id"] = post_id

            posts_photo_row = twkr_posts_photo(**posts_photo_dict)
            session.add(posts_photo_row)
            #session.commit()

    # If link, insert into posts_link table
    if (post_dict["type"] == "link"):
        logging.debug("posts_link")
        posts_link_dict = {}

        posts_link_dict["source_url"] = post_dict["url"]
        posts_link_dict["source_title"] = post_dict["title"]
        posts_link_dict["description"] = post_dict["description"]
        posts_link_dict["post_id"] = post_id

        posts_link_row = twkr_posts_link(**posts_link_dict)
        session.add(posts_link_row)

    # If answer, insert into posts_answer table
    if (post_dict["type"] == "answer"):
        logging.debug("posts_answer")
        posts_answer_dict = {}

        posts_answer_dict["asking_name"] = post_dict["asking_name"]
        posts_answer_dict["asking_url"] = post_dict["asking_url"]
        posts_answer_dict["question"] = post_dict["question"]
        posts_answer_dict["answer"] = post_dict["answer"]
        posts_answer_dict["post_id"] = post_id

        posts_answer_row = twkr_posts_answer(**posts_answer_dict)
        session.add(posts_answer_row)

    # If text, insert into posts_text table
    if (post_dict["type"] == "text"):
        logging.debug("posts_text")
        posts_text_dict = {}

        posts_text_dict["title"] = post_dict["title"]
        posts_text_dict["body"] = post_dict["body"]
        posts_text_dict["post_id"] = post_id

        posts_text_row = twkr_posts_text(**posts_text_dict)
        session.add(posts_text_row)

    # If quote, insert into posts_quote table
    if (post_dict["type"] == "quote"):
        logging.debug("posts_quote")
        posts_quote_dict = {}

        posts_quote_dict["source_url"] = post_dict["source_url"]
        posts_quote_dict["source_title"] = post_dict["source_title"]
        posts_quote_dict["text"] = post_dict["text"]
        posts_quote_dict["post_id"] = post_id

        posts_quote_row = twkr_posts_quote(**posts_quote_dict)
        session.add(posts_quote_row)

    # If chat, insert into posts_chat table
    if (post_dict["type"] == "chat"):
        logging.debug("posts_chat")
        posts_chat_dict = {}

        posts_chat_dict["title"] = post_dict["title"]
        posts_chat_dict["body"] = post_dict["body"]
        posts_chat_dict["dialogue_html"] = None
        posts_chat_dict["dialogue_json"] = json.dumps(post_dict["dialogue"])
        posts_chat_dict["post_id"] = post_id

        posts_chat_row = twkr_posts_chat(**posts_chat_dict)
        session.add(posts_chat_row)

    # Commit once ALL rows for this post are input
    session.commit()
    return True
# /Posts

# Blogs table
def add_blog(session,blog_url):
    """Make sure a blog is in the twkr_blogs table
    return the internal ID number assigned to that blog"""
    logging.debug("making sure blog is in db: "+repr(blog_url))

    # Check if blog is already in DB, if it is return the id
    blog_id_query = sqlalchemy.select([twkr_blogs.blog_id]).where(twkr_blogs.blog_url == blog_url)
    blog_id_rows = session.execute(blog_id_query)
    blog_id_row = blog_id_rows.fetchone()
    if blog_id_row:
        blog_id = blog_id_row["blog_id"]
        logging.debug("blog_id: "+repr(blog_id))
        return blog_id
    else:
        # If blog is not in DB, create a record for it and return the ID
        # Create entry
        blog_dict = {}
        blog_dict["blog_url"] = blog_url
        blogs_row = twkr_blogs(**blog_dict)
        session.add(blogs_row)
        session.commit()

        # Return blog entry
        return add_blog(session,blog_url)
# /Blogs table

def debug():
    """Temp code for debug"""
    session = connect_to_db()

    dummy_blog_id = add_blog(session,blog_url="staff.tumblr.com")
    logging.debug("dummy_blog_id: "+repr(dummy_blog_id))
    return

    # Try each type of post to see what happens
##        u"text":1,
##        u"photo":2,
##        u"quote":3,
##        u"link":4,
##        u"chat":5,
##        u"audio":6,
##        u"video":7,
##        u"answer":8,
    # u"text":1,
    text_post_dict = {u'body': u'<p>It\u2019s been almost two years since we <a href="http://staff.tumblr.com/post/19785116691/policy-update">last updated</a> Tumblr\u2019s terms and policies. A lot has happened since then!</p>\n<p>To make sure these documents fully reflect our product and philosophies, and are as understandable and up-to-date as they can be, our Legal and Policy teams have taken the last few weeks (and a tremendous amount of care) to update our <a href="http://www.tumblr.com/policy/drafts/terms_of_service">Terms of Service</a>, <a href="http://www.tumblr.com/policy/drafts/privacy">Privacy Policy</a>, and <a href="http://www.tumblr.com/policy/drafts/community">Community Guidelines</a>.</p>\n<p>There are a fair number of changes, so we insist you read them all for yourself. Some notable updates include:</p>\n<ul><li>Cleanup to make all of the documents more readable</li>\n<li>Updates to reflect changes to our products over the last two years</li>\n<li>Information about how we work with our new parent company, Yahoo</li>\n<li>Credits for open source projects</li>\n<li>Some language that makes it easier for U.S. government organizations to blog on Tumblr</li>\n<li>An attribution policy reminding people not to be jerks</li>\n<li>Updated annotations (!)</li>\n</ul><p>You can review the drafts via the links above. You can also see every change, letter for letter, on <a href="https://github.com/tumblr/policy/compare/2cfe3c8668...adfff367b5#files_bucket">GitHub</a> (minus the plain English annotations).</p>\n<p>We\u2019re planning to officially launch the new terms soon and we\u2019d really love to hear any questions or concerns. Please write to <a href="mailto:policy@tumblr.com">policy@tumblr.com</a>.</p>', u'highlighted': [], u'reblog_key': u'FejUhHDh', u'format': u'html', u'timestamp': 1390592400, u'note_count': 15210, u'tags': [], u'id': 74407154392L, u'post_url': u'http://staff.tumblr.com/post/74407154392/its-been-almost-two-years-since-we-last-updated', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#FFFFFF', u'header_bounds': 0, u'title_font': u'Gibson', u'link_color': u'#56BC8A', u'header_image_focused': u'http://static.tumblr.com/10e607f9b9b4c588d1cbd6c9f8b564d9/3hpyv0p/nFBnlgttl/tumblr_static_1sssiwavcjs0gs4cggwsok040_2048_v2.gif', u'show_description': True, u'show_header_image': True, u'header_stretch': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://static.tumblr.com/10e607f9b9b4c588d1cbd6c9f8b564d9/3hpyv0p/nFBnlgttl/tumblr_static_1sssiwavcjs0gs4cggwsok040_2048_v2.gif', u'avatar_shape': u'square', u'show_avatar': False, u'background_color': u'#37475c', u'header_image': u'http://static.tumblr.com/10e607f9b9b4c588d1cbd6c9f8b564d9/3hpyv0p/nFBnlgttl/tumblr_static_1sssiwavcjs0gs4cggwsok040.gif'}, u'name': u'staff'}, u'content': u'<p>It\u2019s been almost two years since we <a href="http://staff.tumblr.com/post/19785116691/policy-update">last updated</a> Tumblr\u2019s terms and policies. A lot has happened since then!</p>\n<p>To make sure these documents fully reflect our product and philosophies, and are as understandable and up-to-date as they can be, our Legal and Policy teams have taken the last few weeks (and a tremendous amount of care) to update our <a href="http://www.tumblr.com/policy/drafts/terms_of_service">Terms of Service</a>, <a href="http://www.tumblr.com/policy/drafts/privacy">Privacy Policy</a>, and <a href="http://www.tumblr.com/policy/drafts/community">Community Guidelines</a>.</p>\n<p>There are a fair number of changes, so we insist you read them all for yourself. Some notable updates include:</p>\n<ul><li>Cleanup to make all of the documents more readable</li>\n<li>Updates to reflect changes to our products over the last two years</li>\n<li>Information about how we work with our new parent company, Yahoo</li>\n<li>Credits for open source projects</li>\n<li>Some language that makes it easier for U.S. government organizations to blog on Tumblr</li>\n<li>An attribution policy reminding people not to be jerks</li>\n<li>Updated annotations (!)</li>\n</ul><p>You can review the drafts via the links above. You can also see every change, letter for letter, on <a href="https://github.com/tumblr/policy/compare/2cfe3c8668...adfff367b5#files_bucket">GitHub</a> (minus the plain English annotations).</p>\n<p>We\u2019re planning to officially launch the new terms soon and we\u2019d really love to hear any questions or concerns. Please write to <a href="mailto:policy@tumblr.com">policy@tumblr.com</a>.</p>', u'post': {u'id': u'74407154392'}, u'is_root_item': True, u'is_current_item': True}], u'state': u'published', u'reblog': {u'tree_html': u''}, u'short_url': u'http://tmblr.co/ZE5Fby15J0nBO', u'date': u'2014-01-24 19:40:00 GMT', u'title': None, u'type': u'text', u'slug': u'its-been-almost-two-years-since-we-last-updated', u'blog_name': u'staff'}
    insert_one_post(
        session = session,
        post_dict = text_post_dict,
        blog_id = dummy_blog_id,
        media_hash_list = ["dummy_text_sha512base64_hash"]
        )

    # u"photo":2,
    photo_post_dict = {u'highlighted': [], u'image_permalink': u'http://staff.tumblr.com/image/81595826875', u'reblog_key': u'BU1z20aM', u'featured_in_tag': [u'Design'], u'format': u'html', u'timestamp': 1396544484, u'note_count': 23321, u'tags': [], u'trail': [], u'id': 81595826875L, u'post_url': u'http://staff.tumblr.com/post/81595826875', u'caption': u'', u'state': u'published', u'reblog': {u'tree_html': u''}, u'short_url': u'http://tmblr.co/ZE5Fby1B-VOAx', u'date': u'2014-04-03 17:01:24 GMT', u'photos': [{u'caption': u'', u'original_size': {u'url': u'http://38.media.tumblr.com/5f867e24acdf8365d34875acf489810a/tumblr_n3gr4l2Wtf1qz8q0ho1_500.gif', u'width': 500, u'height': 634}, u'alt_sizes': [{u'url': u'http://38.media.tumblr.com/5f867e24acdf8365d34875acf489810a/tumblr_n3gr4l2Wtf1qz8q0ho1_500.gif', u'width': 500, u'height': 634}, {u'url': u'http://38.media.tumblr.com/5f867e24acdf8365d34875acf489810a/tumblr_n3gr4l2Wtf1qz8q0ho1_400.gif', u'width': 400, u'height': 507}, {u'url': u'http://38.media.tumblr.com/5f867e24acdf8365d34875acf489810a/tumblr_n3gr4l2Wtf1qz8q0ho1_250.gif', u'width': 250, u'height': 317}, {u'url': u'http://38.media.tumblr.com/5f867e24acdf8365d34875acf489810a/tumblr_n3gr4l2Wtf1qz8q0ho1_100.gif', u'width': 100, u'height': 127}, {u'url': u'http://33.media.tumblr.com/5f867e24acdf8365d34875acf489810a/tumblr_n3gr4l2Wtf1qz8q0ho1_75sq.gif', u'width': 75, u'height': 75}]}], u'type': u'photo', u'slug': u'', u'blog_name': u'staff'}
    insert_one_post(
        session = session,
        post_dict = photo_post_dict,
        blog_id = dummy_blog_id,
        media_hash_list = ["dummy_photo_sha512base64_hash"]
        )

    # u"quote":3,
    quote_post_dict = {u'highlighted': [], u'source_title': u'news10.net', u'reblog_key': u'c6ueXgOR', u'format': u'html', u'timestamp': 1379703264, u'note_count': 23519, u'tags': [], u'id': 61775600495L, u'post_url': u'http://staff.tumblr.com/post/61775600495/the-majority-of-workers-waste-their-time-on', u'source': u'<p><a href="http://www.news10.net/news/article/257238/2/Forbes-64-of-employees-are-wasting-time-at-work">Forbes: 64% of employees wasting time at work</a></p>\n<p>Num! Ber! One!<br/>Num! Ber! One!</p>', u'state': u'published', u'text': u'The majority of workers waste their time on Tumblr, followed by Facebook, Twitter, Instagram, and SnapChat.', u'short_url': u'http://tmblr.co/ZE5FbyvY7Djl', u'date': u'2013-09-20 18:54:24 GMT', u'reblog': {u'tree_html': u''}, u'source_url': u'http://www.news10.net/news/article/257238/2/Forbes-64-of-employees-are-wasting-time-at-work', u'type': u'quote', u'slug': u'the-majority-of-workers-waste-their-time-on', u'blog_name': u'staff'}
    insert_one_post(
        session = session,
        post_dict = quote_post_dict,
        blog_id = dummy_blog_id,
        media_hash_list = ["dummy_quote_sha512base64_hash"]
        )

    # u"link":4,
    link_post_dict  ={u'reblog_key': u'dFsxQKez', u'short_url': u'http://tmblr.co/ZE5Fby15ewm82', u'excerpt': None, u'id': 74774675970L, u'post_url': u'http://staff.tumblr.com/post/74774675970/vote-for-the-best-tumblr-of-the-year-shorty', u'author': None, u'tags': [], u'link_image': u'http://33.media.tumblr.com/tumblr_mzv7r7gTeQ1qz8q0h_og.png', u'highlighted': [], u'state': u'published', u'reblog': {u'tree_html': u''}, u'type': u'link', u'description': u'<p>Do you love a blog? Okay, how hard do you love it? If you love it truly, madly, deeply, you will nominate it for the annual Shorty Award for Tumblr of the Year.</p>\n<p>Nominees are now being accepted, and the winner will be honored at the official ceremony this April in New York City!</p>', u'featured_in_tag': [u'Design', u'Advertising'], u'format': u'html', u'timestamp': 1390867778, u'note_count': 1839, u'photos': [{u'caption': u'', u'original_size': {u'url': u'http://33.media.tumblr.com/tumblr_mzv7r7gTeQ1qz8q0h_og.png', u'width': 200, u'height': 200}, u'alt_sizes': []}], u'date': u'2014-01-28 00:09:38 GMT', u'slug': u'vote-for-the-best-tumblr-of-the-year-shorty', u'blog_name': u'staff', u'publisher': u'shortyawards.com', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#FFFFFF', u'header_bounds': 0, u'title_font': u'Gibson', u'link_color': u'#56BC8A', u'header_image_focused': u'http://static.tumblr.com/10e607f9b9b4c588d1cbd6c9f8b564d9/3hpyv0p/nFBnlgttl/tumblr_static_1sssiwavcjs0gs4cggwsok040_2048_v2.gif', u'show_description': True, u'show_header_image': True, u'header_stretch': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://static.tumblr.com/10e607f9b9b4c588d1cbd6c9f8b564d9/3hpyv0p/nFBnlgttl/tumblr_static_1sssiwavcjs0gs4cggwsok040_2048_v2.gif', u'avatar_shape': u'square', u'show_avatar': False, u'background_color': u'#37475c', u'header_image': u'http://static.tumblr.com/10e607f9b9b4c588d1cbd6c9f8b564d9/3hpyv0p/nFBnlgttl/tumblr_static_1sssiwavcjs0gs4cggwsok040.gif'}, u'name': u'staff'}, u'content': u'<p>Do you love a blog? Okay, how hard do you love it? If you love it truly, madly, deeply, you will nominate it for the annual Shorty Award for Tumblr of the Year.</p>\n<p>Nominees are now being accepted, and the winner will be honored at the official ceremony this April in New York City!</p>', u'post': {u'id': u'74774675970'}, u'is_root_item': True, u'is_current_item': True}], u'url': u'http://shortyawards.com/category/6th/tumblr', u'title': u'Vote for the "Best Tumblr of the Year" Shorty Award'}
    insert_one_post(
        session = session,
        post_dict = link_post_dict,
        blog_id = dummy_blog_id,
        media_hash_list = ["dummy_link_sha512base64_hash"]
        )

    # u"chat":5,
    chat_post_dict = {u'body': u"Hair: What hair color looks best on you and what's your natural color?\nSkin: Do you tan easily?\nEyes: What is your favorite show to watch?\nNose: What is your favorite perfume/candle fragrance?\nMouth: Do you want to kiss anyone right now?\nTongue: What was in your last meal?\nWindpipe: Do you sing?\nNeck: Do you wear necklaces?\nEars: How many piercings do you have (if any)?\nCheeks: Do you blush easily?\nWrists: Have you ever broken a bone?\nHands: Are you an artist/writer?\nFingers: Do you play an instrument?\nHeart: Are you in love? If so, does the one you love know?\nLungs: Do you smoke cigarettes?\nChest: Are your maternal/parental instincts strong?\nStomach: Do you feel confident in your body image?\nBack: Are you a virgin?\nHips: Do you like to dance?\nThighs: Has anyone ever called you fat or ugly?\nKnees: Have you ever cheated on someone?\nAnkles: Have you ever been arrested?\nFeet: Favorite pair of shoes?\nBrain: Anything you want to ask", u'highlighted': [], u'dialogue': [{u'phrase': u"What hair color looks best on you and what's your natural color?", u'name': u'Hair', u'label': u'Hair:'}, {u'phrase': u'Do you tan easily?', u'name': u'Skin', u'label': u'Skin:'}, {u'phrase': u'What is your favorite show to watch?', u'name': u'Eyes', u'label': u'Eyes:'}, {u'phrase': u'What is your favorite perfume/candle fragrance?', u'name': u'Nose', u'label': u'Nose:'}, {u'phrase': u'Do you want to kiss anyone right now?', u'name': u'Mouth', u'label': u'Mouth:'}, {u'phrase': u'What was in your last meal?', u'name': u'Tongue', u'label': u'Tongue:'}, {u'phrase': u'Do you sing?', u'name': u'Windpipe', u'label': u'Windpipe:'}, {u'phrase': u'Do you wear necklaces?', u'name': u'Neck', u'label': u'Neck:'}, {u'phrase': u'How many piercings do you have (if any)?', u'name': u'Ears', u'label': u'Ears:'}, {u'phrase': u'Do you blush easily?', u'name': u'Cheeks', u'label': u'Cheeks:'}, {u'phrase': u'Have you ever broken a bone?', u'name': u'Wrists', u'label': u'Wrists:'}, {u'phrase': u'Are you an artist/writer?', u'name': u'Hands', u'label': u'Hands:'}, {u'phrase': u'Do you play an instrument?', u'name': u'Fingers', u'label': u'Fingers:'}, {u'phrase': u'Are you in love? If so, does the one you love know?', u'name': u'Heart', u'label': u'Heart:'}, {u'phrase': u'Do you smoke cigarettes?', u'name': u'Lungs', u'label': u'Lungs:'}, {u'phrase': u'Are your maternal/parental instincts strong?', u'name': u'Chest', u'label': u'Chest:'}, {u'phrase': u'Do you feel confident in your body image?', u'name': u'Stomach', u'label': u'Stomach:'}, {u'phrase': u'Are you a virgin?', u'name': u'Back', u'label': u'Back:'}, {u'phrase': u'Do you like to dance?', u'name': u'Hips', u'label': u'Hips:'}, {u'phrase': u'Has anyone ever called you fat or ugly?', u'name': u'Thighs', u'label': u'Thighs:'}, {u'phrase': u'Have you ever cheated on someone?', u'name': u'Knees', u'label': u'Knees:'}, {u'phrase': u'Have you ever been arrested?', u'name': u'Ankles', u'label': u'Ankles:'}, {u'phrase': u'Favorite pair of shoes?', u'name': u'Feet', u'label': u'Feet:'}, {u'phrase': u'Anything you want to ask', u'name': u'Brain', u'label': u'Brain:'}], u'source_title': u'goodbyebenedict', u'reblog_key': u'nkIanbaM', u'format': u'html', u'timestamp': 1426909760, u'note_count': 1148774, u'tags': [], u'id': 114188519623L, u'post_url': u'http://bigponiesinc.tumblr.com/post/114188519623/ask-me-about-my-body', u'state': u'published', u'short_url': u'http://tmblr.co/ZNohWm1gMAeZ7', u'date': u'2015-03-21 03:49:20 GMT', u'title': u'Ask me about my body. (\xac\u203f\xac)', u'source_url': u'http://goodbyebenedict.tumblr.com/post/47433081091', u'type': u'chat', u'slug': u'ask-me-about-my-body', u'blog_name': u'bigponiesinc'}
    insert_one_post(
        session = session,
        post_dict = chat_post_dict,
        blog_id = dummy_blog_id,
        media_hash_list = []
        )

    # audio 6
    bandcamp_post_dict = {u'reblog_key': u'AbxPRz4A', u'short_url': u'http://tmblr.co/ZE5FbyhlEyOo', u'audio_url': u'http://popplers5.bandcamp.com/download/track?enc=mp3-128&fsig=ca33bbe78b527483940c050bd627a33d&id=2851867171&nl=1&stream=1&ts=1428792368.0', u'player': u'<iframe class="bandcamp_audio_player" width="500" height="120" src="http://bandcamp.com/EmbeddedPlayer/size=medium/bgcol=ffffff/linkcol=0687f5/notracklist=true/transparent=true/track=2851867171/" allowtransparency="true" frameborder="0"></iframe>', u'id': 46963344946, u'album': u'Hunter Hunted - EP', u'post_url': u'http://staff.tumblr.com/post/46963344946/listen-up-our-audio-player-just-got-super-rad', u'source_title': u'Bandcamp', u'tags': [u'hunter hunted', u'keep together', u'music on tumblr', u'bands on tumblr'], u'highlighted': [], u'state': u'published', u'track_name': u'Keep Together', u'type': u'audio', u'featured_in_tag': [u'Music', u'Design'], u'format': u'html', u'timestamp': 1364937324, u'note_count': 5105, u'source_url': u'http://hunterhuntedmusic.bandcamp.com/track/keep-together', u'date': u'2013-04-02 21:15:24 GMT', u'plays': 110209, u'slug': u'listen-up-our-audio-player-just-got-super-rad', u'album_art': u'http://31.media.tumblr.com/tumblr_mkn8sgrMDN1qz8q0h_dSDeaHscmUuv4sl8epf8mAC32IU_cover.jpg', u'blog_name': u'staff', u'is_external': True, u'artist': u'Hunter Hunted', u'caption': u'<p>Listen up: our audio player just got super rad!</p>\n<ul><li><span>Fancy new audio visualizer</span></li>\n<li><span>Bigger album art</span></li>\n<li><span>Click and drag to skip around</span></li>\n</ul><p>Hit play and happy listening!</p>', u'audio_type': u'bandcamp', u'audio_source_url': u'http://popplers5.bandcamp.com/download/track?enc=mp3-128&fsig=ca33bbe78b527483940c050bd627a33d&id=2851867171&nl=1&stream=1&ts=1428792368.0', u'embed': u'<iframe class="bandcamp_audio_player" width="100%" height="120" src="http://bandcamp.com/EmbeddedPlayer/size=medium/bgcol=ffffff/linkcol=0687f5/notracklist=true/transparent=true/track=2851867171/" allowtransparency="true" frameborder="0"></iframe>'}
    insert_one_post(
        session = session,
        post_dict = bandcamp_post_dict,
        blog_id = dummy_blog_id,
        media_hash_list = []
        )

    # video 7
    video_post_dict = {u'reblog_key': u'5VvbpiMU', u'video_url': u'http://vt.tumblr.com/tumblr_n22yhozyhf1qz8q0h.mp4', u'reblog': {u'tree_html': u''}, u'thumbnail_width': 720, u'player': [{u'width': 250, u'embed_code': u'\n<video  id=\'embed-5545b5404d38f208480212\' class=\'crt-video crt-skin-default\' width=\'250\' height=\'166\' poster=\'http://media.tumblr.com/tumblr_n22yhozyhf1qz8q0h_frame1.jpg\' preload=\'none\' data-crt-video data-crt-options=\'{"duration":53,"hdUrl":false,"filmstrip":{"url":"http:\\/\\/25.media.tumblr.com\\/previews\\/tumblr_n22yhozyhf1qz8q0h_filmstrip.jpg","width":"200","height":"134"}}\' >\n    <source src="http://api.tumblr.com/video_file/78875723128/tumblr_n22yhozyhf1qz8q0h" type="video/mp4">\n</video>\n'}, {u'width': 400, u'embed_code': u'\n<video  id=\'embed-5545b5404da06666687965\' class=\'crt-video crt-skin-default\' width=\'400\' height=\'266\' poster=\'http://media.tumblr.com/tumblr_n22yhozyhf1qz8q0h_frame1.jpg\' preload=\'none\' data-crt-video data-crt-options=\'{"duration":53,"hdUrl":false,"filmstrip":{"url":"http:\\/\\/25.media.tumblr.com\\/previews\\/tumblr_n22yhozyhf1qz8q0h_filmstrip.jpg","width":"200","height":"134"}}\' >\n    <source src="http://api.tumblr.com/video_file/78875723128/tumblr_n22yhozyhf1qz8q0h" type="video/mp4">\n</video>\n'}, {u'width': 500, u'embed_code': u'\n<video  id=\'embed-5545b5404e166096811803\' class=\'crt-video crt-skin-default\' width=\'500\' height=\'333\' poster=\'http://media.tumblr.com/tumblr_n22yhozyhf1qz8q0h_frame1.jpg\' preload=\'none\' data-crt-video data-crt-options=\'{"duration":53,"hdUrl":false,"filmstrip":{"url":"http:\\/\\/25.media.tumblr.com\\/previews\\/tumblr_n22yhozyhf1qz8q0h_filmstrip.jpg","width":"200","height":"134"}}\' >\n    <source src="http://api.tumblr.com/video_file/78875723128/tumblr_n22yhozyhf1qz8q0h" type="video/mp4">\n</video>\n'}], u'duration': 53, u'id': 78875723128L, u'post_url': u'http://staff.tumblr.com/post/78875723128/operators-are-standing-by-call-now-thank-you', u'tags': [u'features'], u'highlighted': [], u'state': u'published', u'short_url': u'http://tmblr.co/ZE5Fby19TN0Lu', u'html5_capable': True, u'type': u'video', u'format': u'html', u'timestamp': 1394225635, u'note_count': 1438, u'video_type': u'tumblr', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#FFFFFF', u'header_bounds': 0, u'title_font': u'Gibson', u'link_color': u'#56BC8A', u'header_image_focused': u'http://static.tumblr.com/10e607f9b9b4c588d1cbd6c9f8b564d9/3hpyv0p/nFBnlgttl/tumblr_static_1sssiwavcjs0gs4cggwsok040_2048_v2.gif', u'show_description': True, u'show_header_image': True, u'header_stretch': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://static.tumblr.com/10e607f9b9b4c588d1cbd6c9f8b564d9/3hpyv0p/nFBnlgttl/tumblr_static_1sssiwavcjs0gs4cggwsok040_2048_v2.gif', u'avatar_shape': u'square', u'show_avatar': False, u'background_color': u'#37475c', u'header_image': u'http://static.tumblr.com/10e607f9b9b4c588d1cbd6c9f8b564d9/3hpyv0p/nFBnlgttl/tumblr_static_1sssiwavcjs0gs4cggwsok040.gif'}, u'name': u'staff'}, u'content': u'<p>Operators are standing by. <a href="http://tumblr.com/settings/account">Call now!</a></p>\n<p><em>(Thank you, <a class="tumblelog" href="http://tmblr.co/m75Dmwi6xWV_PQIiRtNSswQ">Jonny</a> and <a class="tumblelog" href="http://tmblr.co/mbmuHBE8CENpM7ix2H5jBfQ">Zack</a>)</em></p>', u'post': {u'id': u'78875723128'}, u'is_root_item': True, u'is_current_item': True}], u'date': u'2014-03-07 20:53:55 GMT', u'thumbnail_height': 480, u'slug': u'operators-are-standing-by-call-now-thank-you', u'blog_name': u'staff', u'caption': u'<p>Operators are standing by. <a href="http://tumblr.com/settings/account">Call now!</a></p>\n<p><em>(Thank you, <a class="tumblelog" href="http://tmblr.co/m75Dmwi6xWV_PQIiRtNSswQ">Jonny</a> and <a class="tumblelog" href="http://tmblr.co/mbmuHBE8CENpM7ix2H5jBfQ">Zack</a>)</em></p>', u'thumbnail_url': u'http://media.tumblr.com/tumblr_n22yhozyhf1qz8q0h_frame1.jpg'}
    insert_one_post(
        session = session,
        post_dict = video_post_dict,
        blog_id = dummy_blog_id,
        media_hash_list = []
        )

    # answer 8
    answer_post_dict = {u'highlighted': [], u'asking_url': None, u'reblog_key': u'O3UPhQYC', u'format': u'html', u'asking_name': u'Anonymous', u'timestamp': 1430518955, u'note_count': 43253, u'tags': [], u'question': u'lauren will you tell us a story', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'header_full_height': 1226, u'title_color': u'#8f1e03', u'header_bounds': u'87,647,433,31', u'title_font': u'Courier New', u'link_color': u'#ffdd00', u'header_image_focused': u'http://static.tumblr.com/cafca27bb4f69629bf936818efb44e6f/88apzkd/fEXnhmx2i/tumblr_static_tumblr_static_983gvr4ppg4cgkgcs8c8owk4o_focused_v3.png', u'show_description': True, u'header_full_width': 677, u'header_focus_width': 616, u'header_stretch': True, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://static.tumblr.com/cafca27bb4f69629bf936818efb44e6f/88apzkd/h29nhmx2f/tumblr_static_983gvr4ppg4cgkgcs8c8owk4o_2048_v2.png', u'avatar_shape': u'circle', u'show_avatar': True, u'header_focus_height': 346, u'background_color': u'#f38321', u'header_image': u'http://static.tumblr.com/cafca27bb4f69629bf936818efb44e6f/88apzkd/h29nhmx2f/tumblr_static_983gvr4ppg4cgkgcs8c8owk4o.png'}, u'name': u'iguanamouth'}, u'content': u'<p>ok heres something</p><p>around a year ago someone asked me to draw <a href="http://iguanamouth.tumblr.com/post/82902281208/draw-danny-devito-as-a-kitty">danny devito as a kitty</a>, spawning this terrible terrible image\xa0</p><figure data-orig-width="500" data-orig-height="406" class="tmblr-full"><img src="https://41.media.tumblr.com/d7549754fd8c427d3393eb702939652f/tumblr_inline_nnld4fWtJH1qmoaae_540.png" alt="image" data-orig-width="500" data-orig-height="406"></figure><p>time passes. a lot of time passes. then two months ago i get an email from a group of people called <a href="https://www.facebook.com/fpoafm">FPOAFM</a> doing a pottery installation event, and theyre going around gathering artwork from artists to put onto cups and dishes to sell,, in exchange for a few pieces with the artists work on them</p><p>and i said SURE you can use some of my stuff \u2026 . but in exchange.\u2026 <b>\xa0i want something with kitty devito on it. </b>i dont care if you put it on anything else, but one item that i get in return has to have this cat man abomination</p><p>i give them my address and a few images and months pass. i forget about it. THEN literally two days ago i get this big package on my doorstep, and INSIDE OF IT\u2026. is the holy grail</p><p>in addition to <a href="https://40.media.tumblr.com/cdd10d787d5bd9c4ab797fca37671cb0/tumblr_nneimxvAoS1rhtthso2_r3_1280.png">two</a> <a href="https://40.media.tumblr.com/7e01bf6e04497f0c9da80ed0b83cc3df/tumblr_nneimxvAoS1rhtthso3_r2_540.png">plates</a> is this incredible porcelain cup with the fabled kitty devito on it, proudly grinning his terrible cat grin</p><figure data-orig-width="800" data-orig-height="885" class="tmblr-full"><img src="https://41.media.tumblr.com/aca0ef3ca89612a513ef9143a439b48d/tumblr_inline_nnldwbZNR91qmoaae_540.png" alt="image" data-orig-width="800" data-orig-height="885"></figure><p>the thing that pushes this cup into the Far Reaches of Awful isnt just the image stamped on it. its that it is one hundred percent made from a mold of a styrofoam cup</p><figure data-orig-width="800" data-orig-height="600" class="tmblr-full"><img src="https://40.media.tumblr.com/7ce202e1b1877d34c0211876cdbb575e/tumblr_inline_nnleakjIpO1qmoaae_540.png" alt="image" data-orig-width="800" data-orig-height="600"></figure><p>its finger presses on the rim, those little lines going around</p><figure data-orig-width="800" data-orig-height="600" class="tmblr-full"><img src="https://36.media.tumblr.com/75f6a2b06915bac6aec356d18f226a47/tumblr_inline_nnleefM9Ty1qmoaae_540.png" alt="image" data-orig-width="800" data-orig-height="600"></figure><p>and all this jargon on the bottom, right under the glaze. the amount of effort that went into reproducing this styrofoam cup is incredible and i can stick it in my shelf and drink soup from it at four in the morning with danny devitos smug cat face looking out over everything i do, forever. follow your dreams</p>', u'post': {u'id': u'117728731307'}, u'is_root_item': True}, {u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#FFFFFF', u'header_bounds': 0, u'title_font': u'Gibson', u'link_color': u'#56BC8A', u'header_image_focused': u'http://static.tumblr.com/10e607f9b9b4c588d1cbd6c9f8b564d9/3hpyv0p/nFBnlgttl/tumblr_static_1sssiwavcjs0gs4cggwsok040_2048_v2.gif', u'show_description': True, u'show_header_image': True, u'header_stretch': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://static.tumblr.com/10e607f9b9b4c588d1cbd6c9f8b564d9/3hpyv0p/nFBnlgttl/tumblr_static_1sssiwavcjs0gs4cggwsok040_2048_v2.gif', u'avatar_shape': u'square', u'show_avatar': False, u'background_color': u'#37475c', u'header_image': u'http://static.tumblr.com/10e607f9b9b4c588d1cbd6c9f8b564d9/3hpyv0p/nFBnlgttl/tumblr_static_1sssiwavcjs0gs4cggwsok040.gif'}, u'name': u'staff'}, u'content': u'<p>Have a follow-your-dreams weekend, Tumblr.</p>', u'post': {u'id': u'117887933455'}, u'is_current_item': True}], u'id': 117887933455L, u'post_url': u'http://staff.tumblr.com/post/117887933455/lauren-will-you-tell-us-a-story', u'answer': u'<p><a class="tumblr_blog" href="http://iguanamouth.tumblr.com/post/117728731307/lauren-will-you-tell-us-a-story">iguanamouth</a>:</p>\n\n<blockquote><p>ok heres something</p><p>around a year ago someone asked me to draw <a href="http://iguanamouth.tumblr.com/post/82902281208/draw-danny-devito-as-a-kitty">danny devito as a kitty</a>, spawning this terrible terrible image\xa0</p><figure data-orig-width="500" data-orig-height="406" class="tmblr-full"><img src="https://41.media.tumblr.com/d7549754fd8c427d3393eb702939652f/tumblr_inline_nnld4fWtJH1qmoaae_540.png" alt="image" data-orig-width="500" data-orig-height="406"/></figure><p>time passes. a lot of time passes. then two months ago i get an email from a group of people called <a href="https://www.facebook.com/fpoafm">FPOAFM</a> doing a pottery installation event, and theyre going around gathering artwork from artists to put onto cups and dishes to sell,, in exchange for a few pieces with the artists work on them</p><p>and i said SURE you can use some of my stuff \u2026 . but in exchange.\u2026 <b>\xa0i want something with kitty devito on it. </b>i dont care if you put it on anything else, but one item that i get in return has to have this cat man abomination</p><p>i give them my address and a few images and months pass. i forget about it. THEN literally two days ago i get this big package on my doorstep, and INSIDE OF IT\u2026. is the holy grail</p><p>in addition to <a href="https://40.media.tumblr.com/cdd10d787d5bd9c4ab797fca37671cb0/tumblr_nneimxvAoS1rhtthso2_r3_1280.png">two</a> <a href="https://40.media.tumblr.com/7e01bf6e04497f0c9da80ed0b83cc3df/tumblr_nneimxvAoS1rhtthso3_r2_540.png">plates</a> is this incredible porcelain cup with the fabled kitty devito on it, proudly grinning his terrible cat grin</p><figure data-orig-width="800" data-orig-height="885" class="tmblr-full"><img src="https://41.media.tumblr.com/aca0ef3ca89612a513ef9143a439b48d/tumblr_inline_nnldwbZNR91qmoaae_540.png" alt="image" data-orig-width="800" data-orig-height="885"/></figure><p>the thing that pushes this cup into the Far Reaches of Awful isnt just the image stamped on it. its that it is one hundred percent made from a mold of a styrofoam cup</p><figure data-orig-width="800" data-orig-height="600" class="tmblr-full"><img src="https://40.media.tumblr.com/7ce202e1b1877d34c0211876cdbb575e/tumblr_inline_nnleakjIpO1qmoaae_540.png" alt="image" data-orig-width="800" data-orig-height="600"/></figure><p>its finger presses on the rim, those little lines going around</p><figure data-orig-width="800" data-orig-height="600" class="tmblr-full"><img src="https://36.media.tumblr.com/75f6a2b06915bac6aec356d18f226a47/tumblr_inline_nnleefM9Ty1qmoaae_540.png" alt="image" data-orig-width="800" data-orig-height="600"/></figure><p>and all this jargon on the bottom, right under the glaze. the amount of effort that went into reproducing this styrofoam cup is incredible and i can stick it in my shelf and drink soup from it at four in the morning with danny devitos smug cat face looking out over everything i do, forever. follow your dreams</p></blockquote><p><p>Have a follow-your-dreams weekend, Tumblr.</p></p>', u'state': u'published', u'reblog': {u'tree_html': u'<p><a class="tumblr_blog" href="http://iguanamouth.tumblr.com/post/117728731307/lauren-will-you-tell-us-a-story">iguanamouth</a>:</p><blockquote><p>ok heres something</p><p>around a year ago someone asked me to draw <a href="http://iguanamouth.tumblr.com/post/82902281208/draw-danny-devito-as-a-kitty">danny devito as a kitty</a>, spawning this terrible terrible image\xa0</p><figure data-orig-width="500" data-orig-height="406" class="tmblr-full"><img src="https://41.media.tumblr.com/d7549754fd8c427d3393eb702939652f/tumblr_inline_nnld4fWtJH1qmoaae_540.png" alt="image" data-orig-width="500" data-orig-height="406"/></figure><p>time passes. a lot of time passes. then two months ago i get an email from a group of people called <a href="https://www.facebook.com/fpoafm">FPOAFM</a> doing a pottery installation event, and theyre going around gathering artwork from artists to put onto cups and dishes to sell,, in exchange for a few pieces with the artists work on them</p><p>and i said SURE you can use some of my stuff \u2026 . but in exchange.\u2026 <b>\xa0i want something with kitty devito on it. </b>i dont care if you put it on anything else, but one item that i get in return has to have this cat man abomination</p><p>i give them my address and a few images and months pass. i forget about it. THEN literally two days ago i get this big package on my doorstep, and INSIDE OF IT\u2026. is the holy grail</p><p>in addition to <a href="https://40.media.tumblr.com/cdd10d787d5bd9c4ab797fca37671cb0/tumblr_nneimxvAoS1rhtthso2_r3_1280.png">two</a> <a href="https://40.media.tumblr.com/7e01bf6e04497f0c9da80ed0b83cc3df/tumblr_nneimxvAoS1rhtthso3_r2_540.png">plates</a> is this incredible porcelain cup with the fabled kitty devito on it, proudly grinning his terrible cat grin</p><figure data-orig-width="800" data-orig-height="885" class="tmblr-full"><img src="https://41.media.tumblr.com/aca0ef3ca89612a513ef9143a439b48d/tumblr_inline_nnldwbZNR91qmoaae_540.png" alt="image" data-orig-width="800" data-orig-height="885"/></figure><p>the thing that pushes this cup into the Far Reaches of Awful isnt just the image stamped on it. its that it is one hundred percent made from a mold of a styrofoam cup</p><figure data-orig-width="800" data-orig-height="600" class="tmblr-full"><img src="https://40.media.tumblr.com/7ce202e1b1877d34c0211876cdbb575e/tumblr_inline_nnleakjIpO1qmoaae_540.png" alt="image" data-orig-width="800" data-orig-height="600"/></figure><p>its finger presses on the rim, those little lines going around</p><figure data-orig-width="800" data-orig-height="600" class="tmblr-full"><img src="https://36.media.tumblr.com/75f6a2b06915bac6aec356d18f226a47/tumblr_inline_nnleefM9Ty1qmoaae_540.png" alt="image" data-orig-width="800" data-orig-height="600"/></figure><p>and all this jargon on the bottom, right under the glaze. the amount of effort that went into reproducing this styrofoam cup is incredible and i can stick it in my shelf and drink soup from it at four in the morning with danny devitos smug cat face looking out over everything i do, forever. follow your dreams</p></blockquote>'}, u'short_url': u'http://tmblr.co/ZE5Fby1jognmF', u'date': u'2015-05-01 22:22:35 GMT', u'type': u'answer', u'slug': u'lauren-will-you-tell-us-a-story', u'blog_name': u'staff'}
    insert_one_post(
        session = session,
        post_dict = answer_post_dict,
        blog_id = dummy_blog_id,
        media_hash_list = []
        )
    return



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
