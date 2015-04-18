#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     17/04/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------





import time
from threading import Thread
from threading import Lock
import multiprocessing

from main import *

def myfunc(i, mutex):
    mutex.acquire(1)
    time.sleep(1)
    print "Thread: %d" %i
    mutex.release()













def main():
    try:
        setup_logging(
        log_file_path=os.path.join("debug","threading_play-log.txt"),
        concise_log_file_path=os.path.join("debug","short-threading_play-log.txt")
        )
        # Program
        #classy_play()
        list_file_path="tumblr_todo_list.txt"
        blog_url_list = import_blog_list(list_file_path)


        mutex = Lock()
        for i in range(0,3):
            blog_url = blog_url_list[i]
            # save_blog(blog_url,max_pages=None)
            worker_1 = multiprocessing.Process(name='worker 1', target=save_blog)
            t = Thread(
                target=save_blog,
                args=(blog_url,1)
                )
            t.start()
            print "main loop %d" %i






        # /Program
        logging.info("Finished, exiting.")
        return

    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return

if __name__ == '__main__':
    main()
