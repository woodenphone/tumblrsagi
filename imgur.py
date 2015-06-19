#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     15/06/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import logging
import imgurpython# Imgur API

from utils import *
import sql_functions
import image_handlers
import config




def save_album(session,album_link):
    """Save the contents of an album"""
    # Extract album ID
    # http://imgur.com/a/AMibi#0
    album_id_search = re.search("""imgur.com/a/([a-zA-Z0-9]+)""", album_link, re.DOTALL)
    if album_id_search:
        album_id = album_id_search.group(1)
    else:
        logging.error("Could not parse album link! "+repr(album_link))
        assert(False)# we need to fix things if this happens
    # Load album from API
    client = imgurpython.ImgurClient(config.imgur_client_id, config.imgur_client_secret)
    album = client.get_album(album_id)
    # Download each image in the album
    media_id_list = []
    for image in album.images:
        media_url = image["link"]
        media_id_list += image_handlers.download_image_link(session,media_url)
    return media_id_list


def save_imgur_images(session,link):
    """Process a url and save the image ids from it"""
    # http://imgur.com/UQ1j8OT,2PvFmxV#1
    # Grab image ids
    # imgur.com/([a-zA-Z0-9,]+)
    image_id_search = re.search("""imgur.com/([a-zA-Z0-9,]+)""", link, re.DOTALL)
    if image_id_search:
        unprocessed_image_ids = image_id_search.group(1)
    else:
        logging.error("Could not parse image(s) link! "+repr(link))
        assert(False)# we need to fix things if this happens
    # Split image ids
    image_ids = unprocessed_image_ids.split(",")
    logging.debug("save_imgur_images() image_ids:"+repr(image_ids))
    # Initialise client
    client = imgurpython.ImgurClient(config.imgur_client_id, config.imgur_client_secret)
    # Process each image id
    media_id_list = []
    for image_id in image_ids:
        try:
            logging.debug("save_imgur_images() image_id:"+repr(image_id))
            image = client.get_image(image_id)
            media_url = image.link
            media_id_list += image_handlers.download_image_link(session,media_url)
        except imgurpython.ImgurClientError, err:
            logging.exception(err)
            logging.error("err:"+repr(err))
    return media_id_list



def save_imgur(session,link):
    """Save any imgur link"""
    logging.debug("Handling imgur link:"+repr(link))
    # Check if album
    # http://imgur.com/a/AMibi#0
    if "imgur.com/a/" in link:
        return save_album(session,link)
    # Check if multiple image ids in url
    return save_imgur_images(session,link)
    # Let us know if we fail to process a link


def debug():
    """For WIP, debug, ect function calls"""
    session = sql_functions.connect_to_db()
    print "foo"

    # Album
    album_media_id_list = save_album(
        session,
        album_link = "http://imgur.com/a/AMibi#0"
        )
    logging.debug("album_media_id_list:"+repr(album_media_id_list))

    # Multiple image link
    multiple_image_link_media_id_list = save_imgur(
        session,
        link = "http://imgur.com/UQ1j8OT,2PvFmxV#1"
        )
    logging.debug("multiple_image_link_media_id_list:"+repr(multiple_image_link_media_id_list))

    # Single image link
    single_image_link_media_id_list = save_imgur(
        session,
        link = "http://imgur.com/UQ1j8OT"
        )
    logging.debug("single_image_link_media_id_list:"+repr(single_image_link_media_id_list))

    logging.debug(repr(locals()))
    return


def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","imgur_handler_log.txt"))
        debug()
    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return


if __name__ == '__main__':
    main()
