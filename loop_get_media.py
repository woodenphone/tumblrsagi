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
    while True:
        get_media.main()
        time.sleep(config.get_media_restart_delay)


def main():
    loop()

if __name__ == '__main__':
    main()
