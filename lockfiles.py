#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     01/07/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import os



class LockFileError(Exception):
    """Signaling exception for lockfiles"""



def start_lock(lock_file_path):
    """If lockfile exists, throw an exception, otherwise, create one"""
    lock_file_exists = os.path.exists(lock_file_path)
    if lock_file_exists:
        raise(LockFileError)
    else:
        create_lock(lock_file_path)
        return


def remove_lock(lock_file_path):
    """Delete a lockfile"""
    if os.path.exists(lock_file_path):
        os.remove(lock_file_path)


def create_lock(lock_file_path):
    """Create the lock file"""
    # Make sure folder exists
    try:
        dirname = os.path.dirname(lock_file_path)
        if len(dirname) != 0:
            os.makedirs(dirname)
    except:
        pass
    # Create the lock file
    with open(lock_file_path, "wb") as f:
        f.write("LOCKFILE")
    return


def test():
    lock_file_path = os.path.join("lockfiles", "test_lock.lock")
    #start_lock(lock_file_path)
    remove_lock(lock_file_path)


def main():
    test()

if __name__ == '__main__':
    main()
