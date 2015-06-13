#-------------------------------------------------------------------------------
# Name:        runner
# Purpose:
#
# Author:      User
#
# Created:     12/06/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import get_posts
import get_media




def loop():
    """Run post and media getters"""
    #






def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","runner_log.txt"))
        loop()
        logging.info("Finished, exiting.")
        pass
    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return

if __name__ == '__main__':
    main()
