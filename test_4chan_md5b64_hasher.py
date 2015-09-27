#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     27/09/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import os

from utils import *

def test_hasher():
    # Define test data
    filename_hash_pairs = [
        ("1443324560044.png","jyIzTlcnP/YlilISOUXQMA=="),
    ]
    # Run tests
    logging.info("Running tests for hashes...")
    for filename, expected_hash in filename_hash_pairs:
        file_path = os.path.join("tests", "4chan_md5b64", filename)
        logging.debug("file_path:"+repr(file_path))
        logging.debug("expected_hash:"+repr(expected_hash))
        # Generate hashes
        md5b64_file_result = generate_md5b64_for_file(file_path)
        logging.debug("md5b64_file_result:"+repr(md5b64_file_result))
        with open(file_path, "rb") as f:
            file_data = f.read()
            md5b64_memory_result = generate_md5b64_for_memory(file_data)
        logging.debug("md5b64_memory_result:"+repr(md5b64_memory_result))
        # Compare hashes
        hashes_matched = (expected_hash == md5b64_file_result == md5b64_memory_result)
        logging.debug("hashes_matched:"+repr(hashes_matched))
        assert(hashes_matched)# Crash if mismatch
        continue
    logging.info("All tests completed.")
    return

def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","test_4chan_md5b6s_log.txt"))
        test_hasher()
        logging.info("Finished, exiting.")
        return

    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return


if __name__ == '__main__':
    main()
