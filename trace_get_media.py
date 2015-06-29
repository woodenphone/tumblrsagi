#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     29/06/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import sys
import trace
import get_media

def main():
    # http://stackoverflow.com/questions/29257856/log-call-stack-in-python
    # https://docs.python.org/2/library/trace.html
    # create a Trace object, telling it what to ignore, and whether to
    # do tracing or line-counting or both.
    tracer = trace.Trace(
        ignoredirs=[sys.prefix, sys.exec_prefix],
        trace=1,
        count=1)

    # run the new command using the given tracer
    tracer.run('get_media.main()')

    # make a report, placing output in the current directory
    r = tracer.results()
    r.write_results(show_missing=True, coverdir="cover")

if __name__ == '__main__':
    main()