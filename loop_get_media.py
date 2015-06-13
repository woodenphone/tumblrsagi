#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     13/06/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import time

import get_media
import config


def loop():
    """Run in a loop forever"""
    print "Starting loop for get_media"
    while True:
        print "calling get_media.main()"
        get_media.main()
        print "finished get_media.main()"
        time.sleep(config.get_media_restart_delay)
        continue



def main():
    loop()

if __name__ == '__main__':
    main()
