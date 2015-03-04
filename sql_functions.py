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
    cursor =  connection.cursor()
    logging.debug(repr(locals()))
    row_to_insert = {} # TODO, Waiting on ATC for DB design # actually fuck waiting he can clean this up later
    # Local stuff
    row_to_insert["date_saved"] = get_current_unix_time()
    # All posts
    row_to_insert["all_posts_blog_name"] = post_dict["body"]
    row_to_insert["all_posts_id"] = post_dict["highlighted"]
    row_to_insert["all_posts_post_url"] = post_dict["reblog_key"]
    row_to_insert["all_posts_type"] = post_dict["format"]
    row_to_insert["all_posts_timestamp"] = post_dict["timestamp"]
    row_to_insert["all_posts_date"] = post_dict["note_count"]
    row_to_insert["all_posts_format"] = "FIXME"# post_dict["tags"]# FIXME
    row_to_insert["all_posts_reblog_key"] = post_dict["id"]
    row_to_insert["all_posts_tags"] = post_dict["post_url"]
    row_to_insert["all_posts_bookmarklet"] = (post_dict["bookmarklet"] if ("bookmarklet" in post_dict.keys()) else None)# Optional in api
    row_to_insert["all_posts_mobile"] = (post_dict["mobile"] if ("mobile" in post_dict.keys()) else None)# Optional in api
    row_to_insert["all_posts_source_url"] = (post_dict["source_url"] if ("source_url" in post_dict.keys()) else None)# Optional in api
    row_to_insert["all_posts_source_title"] = (post_dict["source_title"] if ("source_title" in post_dict.keys()) else None)# Optional in api
    row_to_insert["all_posts_liked"] = post_dict["title"]
    row_to_insert["all_posts_state"] = post_dict["type"]
    row_to_insert["all_posts_total_posts"] = post_dict["slug"]
    # Text posts
    if post_dict["type"] == "text":
        row_to_insert["text_title"] = post_dict["title"]
        row_to_insert["text_body"] = post_dict["body"]
    # Photo posts
    elif post_dict["type"] == "photo":
        row_to_insert["photo_photos"] = post_dict[""]
        row_to_insert["photo_caption"] = post_dict["caption"]
        row_to_insert["photo_width"] = post_dict["width"]
        row_to_insert["photo_height"] = post_dict["height"]
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
        row_to_insert["FIELD_NAME"] = post_dict[""]
    # Audio Posts
    elif post_dict["type"] == "audio":
        row_to_insert["FIELD_NAME"] = post_dict[""]
        row_to_insert["FIELD_NAME"] = post_dict[""]
        row_to_insert["FIELD_NAME"] = post_dict[""]
        row_to_insert["FIELD_NAME"] = post_dict[""]
        row_to_insert["FIELD_NAME"] = post_dict[""]
        row_to_insert["FIELD_NAME"] = post_dict[""]
        row_to_insert["FIELD_NAME"] = post_dict[""]
        row_to_insert["FIELD_NAME"] = post_dict[""]
        row_to_insert["FIELD_NAME"] = post_dict[""]
    # Video Posts
    elif post_dict["type"] == "video":
        row_to_insert["FIELD_NAME"] = post_dict[""]
        row_to_insert["FIELD_NAME"] = post_dict[""]
    # Answer Posts
    elif post_dict["type"] == "answer":
        row_to_insert["FIELD_NAME"] = post_dict[""]
        row_to_insert["FIELD_NAME"] = post_dict[""]
        row_to_insert["FIELD_NAME"] = post_dict[""]
        row_to_insert["FIELD_NAME"] = post_dict[""]
    else:
        logging.error("Unknown post type!")
        logging.error(repr(locals()))
        assert(False)
    # Insert dict into DB
    fields = row_to_insert.keys()
    values = row_to_insert.values()
    query = generate_insert_query(table_name="posts",value_names=fields)
    logging.debug(repr(query))
    result = cursor.execute(query, values)
    cursor.close()
    return




def add_image_to_db(connection,image_filename):
    pass










def main():
    pass

if __name__ == '__main__':
    main()
