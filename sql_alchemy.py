#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     17/03/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import sqlalchemy
import sqlobject

class media(sqlobject.SQLObject):
    media_url = sqlobject.StringCol()


def main():
    pass

if __name__ == '__main__':
    main()
