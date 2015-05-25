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

# http://docs.sqlalchemy.org/en/latest/dialects/postgresql.html
# http://docs.sqlalchemy.org/en/latest/core/type_basics.html
import sqlalchemy# Database library
from sqlalchemy.ext.declarative import declarative_base# Magic for ORM
import sqlalchemy.dialects.postgresql # postgreSQL ORM (JSON, JSONB)

from utils import * # General utility functions
from tables import *# Moved everything there


def main():
    setup_logging(log_file_path=os.path.join("debug","twkr_tables-log.txt"))
    create_example_db_postgres()

if __name__ == '__main__':
    main()

assert(False)# We have stopped using this module
