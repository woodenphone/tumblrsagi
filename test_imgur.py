#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     16/06/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import unittest


from tables import *# Table definitions



def connect_to_test_database():
    """Create a throwaway database for testing"""
    logging.debug("Opening DB connection")
    # add "echo=True" to see SQL being run
    engine = sqlalchemy.create_engine(
        """sqlite://""",
        echo=config.echo_sql
        )
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


class test_saving_album(unittest.TestCase):
    """Test that saving an album works"""
    def test_album(self):
        session = connect_to_test_database()
        result = save_album(
        session,
        album_link = "http://imgur.com/a/AMibi#0"
        )







def main():
    unittest.main()

if __name__ == '__main__':
    main()
