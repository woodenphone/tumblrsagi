#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     29/04/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import sqlalchemy# Database library
from sqlalchemy.ext.declarative import declarative_base# Magic for ORM
from sqlalchemy.dialects.postgresql import JSON
import os
import logging
import utils # General utility functions


# SQLAlchemy table setup
Base = declarative_base()


# Twkr's new tables
class twkr_blogs(Base):
    """Class Info, functionality, purpose"""
    __tablename__ = "twkr_blogs"
    # Columns
    primary_key = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)# Is used only as primary key
    blog_username = sqlalchemy.Column(sqlalchemy.UnicodeText())#

    blog_id = sqlalchemy.Column(sqlalchemy.BigInteger) #
    blog_url = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    title = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    postcount = sqlalchemy.Column(sqlalchemy.BigInteger) #
    name = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    updated = sqlalchemy.Column(sqlalchemy.BigInteger) #
    description = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    ask = sqlalchemy.Column(sqlalchemy.Boolean())
    alive = sqlalchemy.Column(sqlalchemy.Boolean())



class twkr_posts(Base):
    """Class Info, functionality, purpose"""
    __tablename__ = "twkr_posts"
    # Columns
    # Local stuff
    primary_key = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)# Is used only as primary key
    date_saved = sqlalchemy.Column(sqlalchemy.BigInteger)# The unix time the post was saved

    post_id = sqlalchemy.Column(sqlalchemy.BigInteger) #

    blog_id = sqlalchemy.Column(sqlalchemy.BigInteger) #
    source_id = sqlalchemy.Column(sqlalchemy.BigInteger) #
    post_type = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    source_url = sqlalchemy.Column(sqlalchemy.UnicodeText())#



class twkr_posts_photo(Base):
    """Class Info, functionality, purpose"""
    __tablename__ = "twkr_posts_photo"
    # Columns
    # Local stuff
    primary_key = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)# Is used only as primary key

    #id = sqlalchemy.Column(sqlalchemy.BigInteger) #
    caption = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    url = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    order = sqlalchemy.Column(sqlalchemy.BigInteger) #
    md5 = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    post_id = sqlalchemy.Column(sqlalchemy.BigInteger) #



class twkr_posts_link(Base):
    """Class Info, functionality, purpose"""
    __tablename__ = "twkr_posts_link"
    # Columns
    # Local stuff
    primary_key = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)# Is used only as primary key

    #id = sqlalchemy.Column(sqlalchemy.BigInteger) #
    source_url = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    source_title = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    description = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    post_id = sqlalchemy.Column(sqlalchemy.BigInteger) #


class twkr_posts_answer(Base):
    """Class Info, functionality, purpose"""
    __tablename__ = "twkr_posts_answer"
    # Columns
    # Local stuff
    primary_key = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)# Is used only as primary key

    #id = sqlalchemy.Column(sqlalchemy.BigInteger) #
    asking_name = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    asking_url = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    question = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    answer = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    post_id = sqlalchemy.Column(sqlalchemy.BigInteger) #



class twkr_posts_text(Base):
    """Class Info, functionality, purpose"""
    __tablename__ = "twkr_posts_text"
    # Columns
    # Local stuff
    primary_key = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)# Is used only as primary key

    #id = sqlalchemy.Column(sqlalchemy.BigInteger) #
    title = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    body = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    post_id = sqlalchemy.Column(sqlalchemy.BigInteger) #



class twkr_posts_quote(Base):
    """Class Info, functionality, purpose"""
    __tablename__ = "twkr_posts_quote"
    # Columns
    # Local stuff
    primary_key = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)# Is used only as primary key

    #id = sqlalchemy.Column(sqlalchemy.BigInteger) #
    source_url = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    source_title = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    text = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    post_id = sqlalchemy.Column(sqlalchemy.BigInteger) #



class twkr_posts_chat(Base):
    """Class Info, functionality, purpose"""
    __tablename__ = "twkr_posts_chat"
    # Columns
    # Local stuff
    primary_key = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)# Is used only as primary key

    #id = sqlalchemy.Column(sqlalchemy.BigInteger) #
    title = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    body = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    dialogue_html = sqlalchemy.Column(sqlalchemy.UnicodeText())#
    dialogue_json = sqlalchemy.Column(sqlalchemy.dialects.postgresql.JSON(none_as_null=False))#
    post_id = sqlalchemy.Column(sqlalchemy.BigInteger) #




# /Twkr's new tables







def create_example_db():
    """Provide a DB session
    http://www.pythoncentral.io/introductory-tutorial-python-sqlalchemy/"""
    logging.debug("Opening DB connection")
    # add "echo=True" to see SQL being run
    engine = sqlalchemy.create_engine("postgresql://postgres:postgres@localhost/test", echo=True)
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
    utils.setup_logging(log_file_path=os.path.join("debug","tables-log.txt"))
    create_example_db()

if __name__ == '__main__':
    main()
