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
from sql_functions import connect_to_db
import config # User specific settings

from twkr_tables import *# Table definitions



# for twkr's new tables

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


def insert_one_post(session,post_dict,blog_id):# WIP
    """Insert a single post into Twkr's new postgres tables
    Only commit if all tables are set
    Return True if successful.
    """

    # Generate a unique ID for the post
    post_id = post_dict["id"]# I don't trust this but it's good enough for testing

    # Insert into twkr_posts table
    posts_dict = {}
    #posts_dict["field"] = "value" # Example of setting a field
    posts_dict["post_id"] = post_id
    posts_dict["date_saved"] = get_current_unix_time() # Unix time to millisecond precision
    posts_dict["blog_id"] = blog_id # local ID number of the blog
    posts_dict["source_id"] = post_dict["id"] # ID number tumblr gave us for the post
    posts_dict["post_type"] = map_post_type(post_dict["type"]) #
    posts_dict["source_url"] = post_dict["post_url"] # using value the API gave us
    posts_dict["timestamp"] = post_dict["timestamp"] # using value the API gave us

    posts_row = twkr_posts(**posts_dict)
    print "1"# DEBUG
    print "2"# DEBUG
    print "3"# DEBUG
    session.add(posts_row)
    print "1"# DEBUG
    print "2"# DEBUG
    print "3"# DEBUG

    # If photo, insert into posts_photo table
    if False:
        posts_photo_dict = {}
        posts_photo_row = twkr_posts(**posts_photo_dict)
        session.add(posts_photo_row)

    # If link, insert into posts_link table
    if False:
        posts_link_dict = {}
        posts_link_row = twkr_posts(**posts_link_dict)
        session.add(posts_link_row)

    # If answer, insert into posts_answer table
    if False:
        posts_answer_dict = {}
        posts_answer_row = twkr_posts(**posts_answer_dict)
        session.add(posts_answer_row)

    # If text, insert into posts_text table
    if True:
        posts_text_dict = {}
        posts_text_dict["body"] = post_dict["body"]
        posts_text_dict["post_id"] = post_id

        posts_text_row = twkr_posts_text(**posts_text_dict)
        session.add(posts_text_row)

    # If quote, insert into posts_quote table
    if False:
        posts_quote_dict = {}
        posts_quote_row = twkr_posts(**posts_quote_dict)
        session.add(posts_quote_row)

    # If chat, insert into posts_chat table
    if False:
        posts_chat_dict = {}
        posts_chat_row = twkr_posts(**posts_chat_dict)
        session.add(posts_chat_row)

    # Commit once ALL rows for this post are input
    session.commit()
    return True

# /for twkr's new tables



def debug():
    """Temp code for debug"""
    session = connect_to_db()

    # Insert a text post
    text_post_dict
    insert_one_post(
        session = session,
        post_dict = text_post_dict,
        blog_id = 1
        )

    # Insert an audio post
    bandcamp_post_dict = {u'reblog_key': u'AbxPRz4A', u'short_url': u'http://tmblr.co/ZE5FbyhlEyOo', u'audio_url': u'http://popplers5.bandcamp.com/download/track?enc=mp3-128&fsig=ca33bbe78b527483940c050bd627a33d&id=2851867171&nl=1&stream=1&ts=1428792368.0', u'player': u'<iframe class="bandcamp_audio_player" width="500" height="120" src="http://bandcamp.com/EmbeddedPlayer/size=medium/bgcol=ffffff/linkcol=0687f5/notracklist=true/transparent=true/track=2851867171/" allowtransparency="true" frameborder="0"></iframe>', u'id': 46963344946, u'album': u'Hunter Hunted - EP', u'post_url': u'http://staff.tumblr.com/post/46963344946/listen-up-our-audio-player-just-got-super-rad', u'source_title': u'Bandcamp', u'tags': [u'hunter hunted', u'keep together', u'music on tumblr', u'bands on tumblr'], u'highlighted': [], u'state': u'published', u'track_name': u'Keep Together', u'type': u'audio', u'featured_in_tag': [u'Music', u'Design'], u'format': u'html', u'timestamp': 1364937324, u'note_count': 5105, u'source_url': u'http://hunterhuntedmusic.bandcamp.com/track/keep-together', u'date': u'2013-04-02 21:15:24 GMT', u'plays': 110209, u'slug': u'listen-up-our-audio-player-just-got-super-rad', u'album_art': u'http://31.media.tumblr.com/tumblr_mkn8sgrMDN1qz8q0h_dSDeaHscmUuv4sl8epf8mAC32IU_cover.jpg', u'blog_name': u'staff', u'is_external': True, u'artist': u'Hunter Hunted', u'caption': u'<p>Listen up: our audio player just got super rad!</p>\n<ul><li><span>Fancy new audio visualizer</span></li>\n<li><span>Bigger album art</span></li>\n<li><span>Click and drag to skip around</span></li>\n</ul><p>Hit play and happy listening!</p>', u'audio_type': u'bandcamp', u'audio_source_url': u'http://popplers5.bandcamp.com/download/track?enc=mp3-128&fsig=ca33bbe78b527483940c050bd627a33d&id=2851867171&nl=1&stream=1&ts=1428792368.0', u'embed': u'<iframe class="bandcamp_audio_player" width="100%" height="120" src="http://bandcamp.com/EmbeddedPlayer/size=medium/bgcol=ffffff/linkcol=0687f5/notracklist=true/transparent=true/track=2851867171/" allowtransparency="true" frameborder="0"></iframe>'}
    insert_one_post(
        session = session,
        post_dict = bandcamp_post_dict,
        blog_id = 1
        )
    # Insert a video post

    return



def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","twkr_sql_functions-log.txt"))
        debug()
        logging.info("Finished, exiting.")
        pass
    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return

if __name__ == '__main__':
    main()
