#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     09/06/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import sqlalchemy

from utils import * # General utility functions
import sql_functions# Database interaction
from media_handlers import *# Media finding, extractiong, ect
from tables import *# Table definitions
import config # Settings and configuration






def reset_rows():
    """Reset processed flag to False"""
    session = sql_functions.connect_to_db()
    update_statement = sqlalchemy.update(RawPosts).where(RawPosts.media_processed == True).\
        values(media_processed = False)
    session.execute(update_statement)
    session.commit()
    return






def main():
    reset_rows()

if __name__ == '__main__':
    main()
