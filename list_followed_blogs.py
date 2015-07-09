#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     09/07/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import pytumblr# Tumblr official API lib

from utils import * # General utility functions
import config # Settings and configuration


def list_followed():
# Authenticate via OAuth
    client = pytumblr.TumblrRestClient(
      *config.pytumblr_connection_strings
    )

    # Make the request
    client.info()

    # Grab the list of followed blogs
    output_list = []
    offset = -20
    while True:
        offset += 20
        # Grab new page of items
        followed = client.following(limit=10000,offset=20)

        # Stop if finished
        number_followed = followed["total_blogs"]
        logging.debug("number_followed: "+repr(number_followed)+" , offset: "+repr(offset))
        if number_followed < offset:
            break
        followed_blogs = followed["blogs"]



        # Add this page's items to output list
        for followed_blog in followed_blogs:
            output_list.append(followed_blog["url"])

        logging.debug("len(output_list): "+repr(len(output_list)))
        continue

    # Make sure we got everything
    #assert(len(output_list) == number_followed)

    # Save to file
    appendlist(
        output_list,
        list_file_path="followed_blogs_list.txt",
        initial_text="# List of followde blog URLs.\n"
        )
    return


def main():
    try:
        setup_logging(
            log_file_path=os.path.join("debug","list_followed_blogs_log.txt"),
            )
        # Program
        list_followed()
        # /Program
        logging.info("Finished, exiting.")
        return

    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return

if __name__ == '__main__':
    main()
