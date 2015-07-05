#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     05/07/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------



import sqlalchemy
from sqlalchemy import update

from multiprocessing.dummy import Pool as ThreadPool

import lockfiles # MutEx lockfiles
from utils import * # General utility functions
import sql_functions# Database interaction
from media_handlers import *# Media finding, extractiong, ect
import config # Settings and configuration
from tables import RawPosts



def add_skip(session,primary_key):
    """Set skip to true"""
    print "adding skip..."
    update_statement = update(RawPosts).\
        where(RawPosts.primary_key == primary_key).\
        values(skip_processing = True)
    session.execute(update_statement)
    session.commit()
    return

def confirm_skip(session):
    print "Confirming skip..."
    posts_query = sqlalchemy.select([RawPosts]).\
        where((RawPosts.skip_processing == True)).\
        limit(1000)
    post_rows = session.execute(posts_query)
    for post_row in post_rows:
        print post_row

    return



def main():
    session = sql_functions.connect_to_db()
    add_skip(session,primary_key=1548538L)
    confirm_skip(session)


if __name__ == '__main__':
    main()
