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

from twkr_tables import *# Table definitions


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
# /General






# for twkr's new tables

def insert_one_post(session,post_dict,blog_id):# WIP
    """Insert a single post into Twkr's new postgres tables
    Only commit if all tables are set
    Return True if successful.
    """
    # Insert into twkr_posts table
    posts_dict = {}
    #posts_dict["field"] = "value" # Example of setting a field

    post_id = sqlalchemy.Column(sqlalchemy.BigInteger) # I don't know what this is TODO FIXME

    posts_dict["date_saved"] = get_current_unix_time() # Unix time to millisecond precision
    posts_dict["blog_id"] = blog_id # local ID number of the blog
    posts_dict["source_id"] = post_dict["id"] # ID number tumblr gave us for the post
    posts_dict["post_type"] = post_type #
    posts_dict["source_url"] = post_dict["post_url"] # using value the API gave us

    posts_row = twkr_posts(**posts_dict)
    session.add(post_row)

    # If photo, insert into posts_photo table
    if is_photo:
        posts_photo_dict = {}
        posts_photo_row = twkr_posts(**posts_photo_dict)
        session.add(posts_photo_row)

    # If link, insert into posts_link table
    if is_photo:
        posts_link_dict = {}
        posts_link_row = twkr_posts(**posts_link_dict)
        session.add(posts_link_row)

    # If answer, insert into posts_answer table
    if is_photo:
        posts_answer_dict = {}
        posts_answer_row = twkr_posts(**posts_answer_dict)
        session.add(posts_answer_row)

    # If text, insert into posts_text table
    if is_photo:
        posts_text_dict = {}
        posts_text_row = twkr_posts(**posts_text_dict)
        session.add(posts_text_row)

    # If quote, insert into posts_quote table
    if is_photo:
        posts_quote_dict = {}
        posts_quote_row = twkr_posts(**posts_quote_dict)
        session.add(posts_quote_row)

    # If chat, insert into posts_chat table
    if is_photo:
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
