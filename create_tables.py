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
# https://www.tumblr.com/docs/en/api/v2
TABLES['posts'] = (
    "CREATE TABLE `posts` ("
    # Local stuff
    "  `primary_key` int NOT NULL AUTO_INCREMENT,"# Is used only as primary key
    "  `version` int NOT NULL,"# The version of this post this row is associated with
    "  `date_saved` int NOT NULL,"# The unix time the post was saved
    # From API
    # All Post Types
    "  `blog_name` text NOT NULL,"#String	The short name used to uniquely identify a blog
    "  `id` int NOT NULL,"#Number	The post's unique ID
    "  `post_url` text NOT NULL,"#	String	The location of the post
    "  `type` text NOT NULL,"#String	The type of post	See the type request parameter
    "  `timestamp` text NOT NULL,"#	Number	The time of the post, in seconds since the epoch
    "  `date` text NOT NULL,"#	String	The GMT date and time of the post, as a string
    "  `format` text NOT NULL,"#String	The post format: html or markdown
    "  `reblog_key` text NOT NULL,"#	String	The key used to reblog this post	See the /post/reblog method
    "  `tags` text NOT NULL,"#Array (string)	Tags applied to the post
    "  `bookmarklet` bool,"#	Boolean	Indicates whether the post was created via the Tumblr bookmarklet	Exists only if true
    "  `mobile` bool,"#Boolean	Indicates whether the post was created via mobile/email publishing	Exists only if true
    "  `source_url` text NOT NULL,"#String	The URL for the source of the content (for quotes, reblogs, etc.)	Exists only if there's a content source
    "  `source_title` text NOT NULL,"#String	The title of the source site	Exists only if there's a content source
    "  `liked` bool,"#Boolean	Indicates if a user has already liked a post or not	Exists only if the request is fully authenticated with OAuth.
    "  `state` text NOT NULL,"# String	Indicates the current state of the post	States are published, queued, draft and private
    "  `total_posts` text NOT NULL,"#String	Indicates the current state of the post	States are published, queued, draft and private
    # Text Posts
    "  `title` text,"# 	String	The optional title of the post
    "  `body` text,"# 	String	The full post body
    # Photo posts
    "  `photos` text,"# Array	Photo objects with properties:
    "  `caption` text,"#	String	The user-supplied caption
    "  `width` int,"#	Number	The width of the photo or photoset
    "  `height` int,"#	Number	The height of the photo or photoset
    # Quote Posts
    "  `text` text,"# 	String	The text of the quote (can be modified by the user when posting)
    "  `source` text,"# 	String	Full HTML for the source of the quote
    # Link Posts
    "  `title` text,"#	String	The title of the page the link points to
    "  `url` text,"#	String	The link
    "  `description` text,"#	String	A user-supplied description
    # Chat Posts
    "  `title` text,"#String	The optional title of the post
    "  `body` text,"#String	The full chat body
    "  `dialogue` text,"#Array	Array of objects
    # Audio Posts
    "  `caption` text,"#	String	The user-supplied caption
    "  `player` text,"#String	HTML for embedding the audio player
    "  `plays` int,"#	Number	Number of times the audio post has been played
    "  `album_art` text,"#String	Location of the audio file's ID3 album art image
    "  `artist` text,"#String	The audio file's ID3 artist value
    "  `album` text,"#String	The audio file's ID3 album value
    "  `track_name` text,"#	String	The audio file's ID3 title value
    "  `track_number` int,"#Number	The audio file's ID3 track value
    "  `year` text,"#Number	The audio file's ID3 year value
    # Video Posts
    "  `caption` text,"#String	The user-supplied caption
    "  `player` text,"#Array of embed objects	Object fields within the array:
    # Answer Posts
    "  `asking_name` text,"#String	The blog name of the user asking the question
    "  `asking_url` text,"#	String	The blog URL of the user asking the question
    "  `question` text,"#	String	The question being asked
    "  `answer` text,"#String	The answer given
    #
    "  PRIMARY KEY (`primary_key`)"
    ") ENGINE=InnoDB")

# The metadata associated with a chapter, as given by the API page for a story
TABLES['blogs'] = (
    "CREATE TABLE `blogs` ("
    # Local stuff
    "  `primary_key` int NOT NULL AUTO_INCREMENT,"# Is used only as primary key
    "  `version` int NOT NULL,"# The version of this story this row is associated with
    "  `parent_story_id` int NOT NULL,"# The site-assigned ID for a story
    "  `chapter_number` int NOT NULL,"# Determined based on order chapters appear in API
    # From site
    "  `id` int NOT NULL,"# id is name used in API, referred to as story_id elsewhere to avoid confusion
    "  `link` text,"
    "  `title` text NOT NULL,"
    "  `views` int NOT NULL,"
    "  `words` int NOT NULL,"
    "  PRIMARY KEY (`primary_key`)"
    ") ENGINE=InnoDB")

# The text for an individual chapter, as given bu the chapter download links
TABLES['media'] = (
    "CREATE TABLE `media` ("
    # Local stuff
    "  `primary_key` int NOT NULL AUTO_INCREMENT,"# Is used only as primary key
    "  `version` int NOT NULL,"# The version of this story this row is associated with
    "  `date_added` int NOT NULL,"# Unix timestamp when row was added
    "  `url`  text NOT NULL,"# URL the media came from
    "  `hash_md5b64`  text NOT NULL,"# md5 file hash encoded in base 64
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
