#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     07/06/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#External
import sqlalchemy# Database  library
import os
# Project-local
from utils import * # General utility functions
import sql_functions# Database interaction
import config # Settings and configuration
from tables import *# Table definitions



def dump_posts(session,output_file_path=os.path.join("debug","raw_posts_dump.txt")):
    with open(output_file_path, "a") as f:
        posts_query = sqlalchemy.select([RawPosts]).\
            limit(1000)
        posts_rows = session.execute(posts_query)
        for posts_row in posts_rows:
            f.write(repr(posts_row["raw_post_json"])+"\n")
    return


def main():
    session = sql_functions.connect_to_db()
    dump_posts(
        session,
        output_file_path=os.path.join("debug","raw_posts_dump.txt")
        )

if __name__ == '__main__':
    main()
