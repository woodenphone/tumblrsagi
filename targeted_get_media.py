#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     20/04/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import get_media


def main():
    # Check and create lockfiles OUTSIDE trt / except block to ensure it is
    # not removed on lock-related crash
    lock_file_path = os.path.join(config.lockfile_dir, "get_media.lock")
    lockfiles.start_lock(lock_file_path)
    try:
        setup_logging(
            log_file_path=os.path.join("debug","targeted_get_media_log.txt"),
            )
        # Program
        #process_one_thousand_posts_media()
        logging.info("Please enter blog domain to force processing for")
        blog_domain = raw_input("Blog domain?")
        get_media.mt_process_posts(target_blog=blog_domain)
        # /Program
        logging.info("Finished, exiting.")
        return

    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    finally:
        # Remove lockfile even if we crashed
        lockfiles.remove_lock(lock_file_path)
    return

if __name__ == '__main__':
    main()
