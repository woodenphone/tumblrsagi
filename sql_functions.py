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


import mysql.connector
from utils import *

import config # User specific settings


def generate_insert_query(table_name,value_names):
    """Generate a SQL insert statement so all the statements can be made in one place
    NEVER LET THIS TOUCH OUTSIDE DATA!
    'INSERT INTO <TABLE_NAME> (<VALUE_NAME_1>, <VALUE_NAME_2>,...) %s, %s, ...);'
    """
    assert len(value_names) > 0
    value_names_with_backticks = []
    for value in value_names:
        assert(type(value) is type(""))
        value_names_with_backticks.append("`"+value+"`")
    query = (
    "INSERT INTO `"+table_name+"` (%s) VALUES (" % (", ".join(value_names_with_backticks),)# Values from dict
    +"%s, "*(len(value_names_with_backticks)-1)#values to insert
    +"%s);"
    )
    #logging.debug(repr(query))
    return query


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



def find_blog_posts(connection,blog_username):
    """Lookup a blog's posts in the DB and return a list of the IDs"""
    logging.warning("Posts lookup not implimented")# TODO FIXME
    return []



def lookup_field(connection,table,field,value):
    """Return a list of all rows matching the given table/field/value group
    If no rows match, return None
    ONLY set field through code, NEVER give field from outside data"""
    logging.warning("THIS IS HILARIOUSLY VULNERABLE TO INJECTION ATTACKS!")# I do not know why this isn't working, so fuck it i'll just use strings
    logging.debug("checking media for field: "+repr(field)+" and value: "+repr(value))
    cursor =  connection.cursor()# Grab a cursor
    check_query = "SELECT * FROM `"+table+"` WHERE "+field+" = '"+value+"';"# Lookup query THIS IS BAD AND SHOULD NOT BE KEPT!
    logging.debug(check_query)
    cursor.execute(check_query)
    # Store rows found in a list
    check_row_counter = 0
    rows = []
    for row in cursor:
        check_row_counter += 1
        #logging.debug("row: "+repr(row))
        rows.append(row)
    #logging.debug("rows: "+repr(rows))
    cursor.close()
    # Return rows if any are found
    if len(rows) > 0:
        return rows
    else:
        return None




def check_if_link_in_db(connection,media_url):
    """Lookup a URL in the media DB.
    Return True if any matches found; otherwise return False."""
    logging.debug("checking DB for media_url: "+repr(media_url))
    cursor =  connection.cursor()
    # Check for existing records for the file hash
    check_query = "SELECT * FROM `media` WHERE media_url = '%s';"
    logging.debug(check_query)
    cursor.execute(check_query)
    media_already_saved = False
    check_row_counter = 0
    for check_row in cursor:
        check_row_counter += 1
        logging.debug("check_row: "+repr(check_row))
        media_already_saved = True
    logging.debug("media_already_saved: "+repr(media_already_saved))
    cursor.close()
    return media_already_saved


def check_if_audio_in_db(connection,soundcloud_id=None):
    logging.debug("check_if_audio_in_db;soundcloud_id:"+repr(soundcloud_id))
    # Lookup video ID
    if soundcloud_id:
        soundcloud_rows = lookup_field(connection,"media","soundcloud_id",soundcloud_id)
        logging.debug("soundcloud_rows"+repr(soundcloud_rows))
        if soundcloud_rows:
            return soundcloud_rows[4]
    return None


def check_if_video_in_db(connection,media_url=None,youtube_id=None,sha512base64_hash=None,post_id=None):
    """Lookup videos in db return filepath to existing media if it exists, otherwise return None"""
    logging.debug("check_if_video_in_db"+repr(locals()))
    logging.warning("CODE VIDEO DB STUFF")# TODO FIXME
    cursor =  connection.cursor()
    # Lookup each field in the DB
    # Lookup hash
    if sha512base64_hash:
        hash_rows = lookup_field(connection,"media","sha512base64_hash",sha512base64_hash)
        if hash_rows:
            return hash_rows[4]
        hash_query = "SELECT * FROM `media` WHERE sha512base64_hash = '%s';"
        logging.debug("hash_query: "+repr(hash_query))
        cursor.execute(hash_query, (sha512base64_hash))
        preexisting_filepath = None
        for check_row in cursor:
            check_row_counter += 1
            logging.debug("check_row: "+repr(check_row))
            preexisting_filepath = True
        if preexisting_filepath:
            return preexisting_filepath
    # Lookup video ID
    if youtube_id:
        youtube_rows = lookup_field(connection,"media","youtube_video_id",youtube_id)
        if youtube_rows:
            return youtube_rows[4]
    # Lookup media URL
    if media_url:
        url_rows = lookup_field(connection,"media","media_url",media_url)
        if url_rows:
            return url_rows[4]
        media_url_query = "SELECT * FROM `media` WHERE media_url = '%s';"
        logging.debug(media_url_query)
        cursor.execute(media_url_query, (media_url))
        preexisting_filepath = None
        for check_row in cursor:
            check_row_counter += 1
            logging.debug("check_row: "+repr(check_row))
            preexisting_filepath = True
        if preexisting_filepath:
            return preexisting_filepath
    # If no field matches, return False
    logging.debug("No field matches, video not in DB")
    return None


def add_media_to_db(connection,
    media_url,
    sha512base64_hash,
    media_filename,
    time_of_retreival,
    extractor_used,
    youtube_yt_dl_info_json=None,
    tumblrvideo_yt_dl_info_json=None,
    youtube_video_id=None):
    """Insert media information for a URL into the DB"""

    cursor =  connection.cursor()
    logging.debug("media_filename: "+repr(media_filename))
    # Check for existing records for the file hash
    check_query = "SELECT * FROM `media` WHERE sha512base64_hash = '%s';"
    logging.debug(check_query)
    cursor.execute(check_query, (sha512base64_hash))
    check_row_counter = 0
    for check_row in cursor:
        check_row_counter += 1
        logging.debug("check_row: "+repr(check_row))
    media_already_saved = False# Was there a hash collission
    # Generate new row for the DB
    row_to_insert = {}
    row_to_insert["date_added"] = time_of_retreival
    row_to_insert["media_url"] = media_url
    row_to_insert["sha512base64_hash"] = sha512base64_hash
    row_to_insert["filename"] = media_filename
    row_to_insert["extractor_used"] = extractor_used
    # Image
    # Tumblr photos

    # Video
    # Tumblr video
    row_to_insert["tumblrvideo_yt_dl_info_json"] = tumblrvideo_yt_dl_info_json
    # Youtube video
    row_to_insert["youtube_yt_dl_info_json"] = youtube_yt_dl_info_json
    row_to_insert["youtube_video_id"] = youtube_video_id

    # Audio
    row_to_insert["filename"] = media_filename
    # Tumblr Audio
    if config.log_db_rows:
        logging.debug("row_to_insert: "+repr(row_to_insert))
    # Insert dict into DB
    fields = row_to_insert.keys()
    values = row_to_insert.values()
    insert_query = generate_insert_query(table_name="media",value_names=fields)
    logging.debug(repr(insert_query))
    insert_result = cursor.execute(insert_query, values)
    cursor.close()
    return media_already_saved # Tell the calling function if the media was already saved from another URL



def add_image_to_db(connection,media_url,sha512base64_hash,image_filename,time_of_retreival):
    """Insert media information for a URL into the DB"""
    cursor =  connection.cursor()
    logging.debug("image_filename: "+repr(image_filename))
    # Check for existing records for the file hash
    # SELECT * FROM `Content` WHERE title = 'bombshells.mp4' ORDER BY id LIMIT 1;
    #check_query = "SELECT * FROM `media` WHERE sha512base64_hash = %s ORDER BY primary_key LIMIT 1;"
    # "SELECT version FROM (story_metadata) WHERE id = %s ORDER BY version LIMIT 1"
    #check_query = "SELECT sha512base64_hash FROM (media) WHERE sha512base64_hash = %s ORDER BY primary_key LIMIT 1"
    check_query = "SELECT * FROM `media` WHERE sha512base64_hash = '%s';"
    #check_query = "SELECT * FROM `media` WHERE sha512base64_hash = '%s';" % sha512base64_hash # From #derpibooru
    logging.debug(check_query)
    cursor.execute(check_query, (sha512base64_hash))
    check_row_counter = 0
    for check_row in cursor:
        check_row_counter += 1
        logging.debug("check_row: "+repr(check_row))
    media_already_saved = False# Was there a hash collission
    # Insert new row for the new URL
    row_to_insert = {}
    row_to_insert["date_added"] = time_of_retreival
    row_to_insert["media_url"] = media_url
    row_to_insert["sha512base64_hash"] = sha512base64_hash
    row_to_insert["filename"] = image_filename
    #
    if config.log_db_rows:
        logging.debug("row_to_insert: "+repr(row_to_insert))
    # Insert dict into DB
    fields = row_to_insert.keys()
    values = row_to_insert.values()
    insert_query = generate_insert_query(table_name="media",value_names=fields)
    logging.debug(repr(insert_query))
    insert_result = cursor.execute(insert_query, values)
    cursor.close()
    return media_already_saved # Tell the calling function if the media was already saved from another URL










def main():
    pass

if __name__ == '__main__':
    main()
