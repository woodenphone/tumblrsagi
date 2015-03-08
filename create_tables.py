#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     15/02/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# https://dev.mysql.com/doc/connector-python/en/connector-python-example-ddl.html


from __future__ import print_function

import mysql.connector
from mysql.connector import errorcode
import config# Settings




DB_NAME = config.sql_login["database"]

TABLES = {}
# The posts in a blog
# <type>_<api_field_name>
# https://www.tumblr.com/docs/en/api/v2
TABLES['posts'] = (
    "CREATE TABLE `posts` ("
    # Local stuff
    "  `primary_key` int NOT NULL AUTO_INCREMENT,"# Is used only as primary key
    "  `version` int NOT NULL,"# The version of this post this row is associated with
    "  `date_saved` int NOT NULL,"# The unix time the post was saved
    "  `processed_body` text,"# Text of the post after links have been processed
    # Missing from API docs
    "  `misc_slug` text,"#
    "  `misc_short_url` text,"#
    # From API
    # All Post Types
    "  `all_posts_blog_name` text NOT NULL,"#String	The short name used to uniquely identify a blog
    "  `all_posts_id` bigint NOT NULL,"#Number	The post's unique ID
    "  `all_posts_post_url` text NOT NULL,"#	String	The location of the post
    "  `all_posts_type` text NOT NULL,"#String	The type of post	See the type request parameter
    "  `all_posts_timestamp` text NOT NULL,"#	Number	The time of the post, in seconds since the epoch
    "  `all_posts_date` text NOT NULL,"#	String	The GMT date and time of the post, as a string
    "  `all_posts_format` text NOT NULL,"#String	The post format: html or markdown
    "  `all_posts_reblog_key` text,"#	String	The key used to reblog this post	See the /post/reblog method
    "  `all_posts_tags` text,"#Array (string)	Tags applied to the post
    "  `all_posts_bookmarklet` bool,"#	Boolean	Indicates whether the post was created via the Tumblr bookmarklet	Exists only if true
    "  `all_posts_mobile` bool,"#Boolean	Indicates whether the post was created via mobile/email publishing	Exists only if true
    "  `all_posts_source_url` text,"#String	The URL for the source of the content (for quotes, reblogs, etc.)	Exists only if there's a content source
    "  `all_posts_source_title` text,"#String	The title of the source site	Exists only if there's a content source
    "  `all_posts_liked` bool,"#Boolean	Indicates if a user has already liked a post or not	Exists only if the request is fully authenticated with OAuth.
    "  `all_posts_state` text NOT NULL,"# String	Indicates the current state of the post	States are published, queued, draft and private
    #"  `all_posts_total_posts` int,"#Number	The total number of post available for this request, useful for paginating through results
    # Text Posts
    "  `text_title` text,"# 	String	The optional title of the post
    "  `text_body` text,"# 	String	The full post body
    # Photo posts
    "  `photo_photos` text,"# Array	Photo objects with properties:
    "  `photo_caption` text,"#	String	The user-supplied caption
    "  `photo_width` int,"#	Number	The width of the photo or photoset
    "  `photo_height` int,"#	Number	The height of the photo or photoset
    # Quote Posts
    "  `quote_text` text,"# 	String	The text of the quote (can be modified by the user when posting)
    "  `quote_source` text,"# 	String	Full HTML for the source of the quote
    # Link Posts
    "  `link_title` text,"#	String	The title of the page the link points to
    "  `link_url` text,"#	String	The link
    "  `link_description` text,"#	String	A user-supplied description
    # Chat Posts
    "  `chat_title` text,"#String	The optional title of the post
    "  `chat_body` text,"#String	The full chat body
    "  `chat_dialogue` text,"#Array	Array of objects
    # Audio Posts
    "  `audio_caption` text,"#	String	The user-supplied caption
    "  `audio_player` text,"#String	HTML for embedding the audio player
    "  `audio_plays` int,"#	Number	Number of times the audio post has been played
    "  `audio_album_art` text,"#String	Location of the audio file's ID3 album art image
    "  `audio_artist` text,"#String	The audio file's ID3 artist value
    "  `audio_album` text,"#String	The audio file's ID3 album value
    "  `audio_track_name` text,"#	String	The audio file's ID3 title value
    "  `audio_track_number` int,"#Number	The audio file's ID3 track value
    "  `audio_year` int,"#Number	The audio file's ID3 year value
    # Video Posts
    "  `video_caption` text,"#String	The user-supplied caption
    "  `video_player` text,"#Array of embed objects	Object fields within the array:
    # Answer Posts
    "  `answer_asking_name` text,"#String	The blog name of the user asking the question
    "  `answer_asking_url` text,"#	String	The blog URL of the user asking the question
    "  `answer_question` text,"#	String	The question being asked
    "  `answer_answer` text,"#String	The answer given
    #
    "  PRIMARY KEY (`primary_key`)"
    ") ENGINE=InnoDB")


# Blogs
#https://www.tumblr.com/docs/en/api/v2
TABLES['blogs'] = (
    "CREATE TABLE `blogs` ("
    # Local stuff
    "  `primary_key` int NOT NULL AUTO_INCREMENT,"# Is used only as primary key
    "  `date_last_saved` int,"# Unix time of date last saved
    # From /info, documented
    "  `info_title` text,"#String	The display title of the blog	Compare name
    "  `info_posts` int,"#Number	The total number of posts to this blog
    "  `info_name` text,"#String	The short blog name that appears before tumblr.com in a standard blog hostname (and before the domain in a custom blog hostname)	Compare title
    "  `info_updated` bigint,"#	Number	The time of the most recent post, in seconds since the epoch
    "  `info_description` text,"#String	You guessed it! The blog's description
    "  `info_ask` bool,"#Boolean	Indicates whether the blog allows questions
    "  `info_ask_anon` bool,"#	Boolean	Indicates whether the blog allows anonymous questions	Returned only if ask is true
    "  `info_likes` int,"#Number	Number of likes for this user	Returned only if this is the user's primary blog and sharing of likes is enabled
    # From /info, undocumented
    "  `info_is_nsfw` bool,"
    "  `info_share_likes` bool,"
    "  `info_url` bool,"
    "  `info_ask_page_title` text,"
    #
    "  PRIMARY KEY (`primary_key`)"
    ") ENGINE=InnoDB")


# The text for an individual chapter, as given bu the chapter download links
TABLES['media'] = (
    "CREATE TABLE `media` ("
    # Local stuff
    "  `primary_key` int NOT NULL AUTO_INCREMENT,"# Is used only as primary key
    "  `date_added` int NOT NULL,"# Unix timestamp when row was added
    "  `media_url`  text NOT NULL,"# URL the media came from
    "  `sha512base64_hash`  text NOT NULL,"#
    "  `filename`  text NOT NULL,"#
    #
    "  PRIMARY KEY (`primary_key`)"
    ") ENGINE=InnoDB")


# Does nothing.
TABLES['goggles'] = (
    "CREATE TABLE `goggles` ("
    # Local stuff
    "  `primary_key` int NOT NULL AUTO_INCREMENT,"# Is used only as primary key
    "  `version` int NOT NULL,"# Unused
    "  `wearer` text,"# Unused
    "  `left_lens` text,"# Unused
    "  `right_lens` text,"# Unused
    "  `strap_size` text,"# Unused
    #
    "  PRIMARY KEY (`primary_key`)"
    ") ENGINE=InnoDB")


def setup_max_size(connection):
    cursor =  connection.cursor()
    query = (
    "set global net_buffer_length=1000000;"
    "set global max_allowed_packet=1000000000;"
    )
    result = cursor.execute(query)
    return





def create_database(cursor):
    try:
        cursor.execute(
            "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(DB_NAME))
    except mysql.connector.Error as err:
        print("Failed creating database: {}".format(err))
        exit(1)













def main():
    cnx = mysql.connector.connect(**config.sql_login)
    cursor = cnx.cursor()
    try:
        cnx.database = DB_NAME
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            create_database(cursor)
            cnx.database = DB_NAME
        else:
            print(err)
            exit(1)



    for name, ddl in TABLES.iteritems():
        try:
            print("Creating table {}: ".format(name), end='')
            cursor.execute(ddl)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print("already exists.")
            print(err.msg)
        else:
            print("OK")

    cursor.close()
    #setup_max_size(cnx)
    cnx.close()


if __name__ == '__main__':
    main()
