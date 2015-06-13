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

import get_posts
import config


def loop():
    """Run in a loop forever"""
    print "Starting loop for get_posts"
    while True:
        print "calling get_posts.main()"
        get_posts.main()
        print "finished get_posts.main()"
        time.sleep(config.get_posts_restart_delay)
        continue


def main():
    loop()

if __name__ == '__main__':
    main()
