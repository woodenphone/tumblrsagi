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


from utils import * # General utility functions
import sql_functions# Database interaction
from media_handlers import *# Media finding, extractiong, ect
import config # Settings and configuration
from tables import *# Table definitions


def drop_tables():
    """Drop all tables except for media and rawposts"""
    session = sql_functions.connect_to_db()
    Base.metadata.drop_all()


def main():
    drop_tables()

if __name__ == '__main__':
    main()
