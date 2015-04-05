#-------------------------------------------------------------------------------
# Name:        tornado_play
# Purpose: learn to use tornado so we can impliment it
#
# Author:      User
#
# Created:     04/04/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from tornado import httpclient










def handle_request(response):
    print "handle"
    if response.error:
        print "Error:", response.error
    else:
        print response.body

http_client = httpclient.AsyncHTTPClient()
http_client.fetch("http://www.google.com/", handle_request)




print "done"





















def main():
    pass

if __name__ == '__main__':
    main()
