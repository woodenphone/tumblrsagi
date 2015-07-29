#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     11/06/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
# Libraries
import sqlalchemy
# This project
from utils import *
import config # User specific settings
import sql_functions
import image_handlers
from tables import *# Table definitions





def update_blog_avatar(session,blog_url):
    """Make sure the blog has the latest version of the avatar, and don't give it the default one
    this is too messy"""
    # -Avatar-
    # Get the ids for this user's avatar image at both small and large sizes
    avatar_media_id_query = sqlalchemy.select([twkr_blogs]).\
        where(twkr_blogs.blog_url == blog_url)
    avatar_media_id_rows = session.execute(avatar_media_id_query)
    avatar_media_id_row = avatar_media_id_rows.fetchone()
    small_avatar_media_id = avatar_media_id_row["user_thumbnail_64_media_id"]
    large_avatar_media_id = avatar_media_id_row["user_thumbnail_512_media_id"]
    blog_id = avatar_media_id_row["blog_id"]

    # Check if small avatar has changed
    # Get URL and hash of small avatar
    small_avatar_check_query = sqlalchemy.select([Media]).\
        where(Media.media_id == small_avatar_media_id)
    small_avatar_check_rows = session.execute(small_avatar_check_query)
    small_avatar_check_row = small_avatar_check_rows.fetchone()
    if small_avatar_check_row:
        old_small_avatar_url = small_avatar_check_row["media_url"]
        old_small_avatar_sha512base16_hash = small_avatar_check_row["sha512base16_hash"]
    else:
        old_small_avatar_url = None
        old_small_avatar_sha512base16_hash = None

    # Grab small avatar image from API
    current_small_avatar_api_url = "http://api.tumblr.com/v2/blog/"+blog_url+"/avatar"
    logging.debug("small_avatar_api_url:"+repr(current_small_avatar_api_url))
    current_small_avatar_request_tuple = getwithinfo(current_small_avatar_api_url)
    if current_small_avatar_request_tuple is None: # sometimes this 403s
        logging.error("Error loading avatar, skipping avatar update.")
        return
    current_small_avatar, small_avatar_info, small_avatar_request = current_small_avatar_request_tuple

    # Get values to compare from current small avatar
    current_small_avatar_real_url = small_avatar_request.geturl()
    current_small_avatar_sha512base16_hash = hash_file_data(current_small_avatar)
    logging.debug("small_avatar_api_url:"+repr(current_small_avatar_real_url))

    # Comapre URL and hash of the current small avatar with those from the DB
    if  (
        (old_small_avatar_url == current_small_avatar_real_url)
        and (old_small_avatar_sha512base16_hash == current_small_avatar_sha512base16_hash)
        ):
        # We have the latest avatar
        logging.debug("update_blog_avatar() Avatar does not need updating.")
        return

    # Make sure this isn't the default avatar (In case the account was deleted)
    # https://secure.assets.tumblr.com/images/default_avatar_64.png
    # https://secure.assets.tumblr.com/images/default_avatar/octahedron_open_64.png
    if ("default_avatar" in current_small_avatar_real_url) and config.skip_default_avatars:
        # Avatar is the default avatar!
        logging.debug("Blog avatar is default, not updating in case it was deleted.")
        return

    # Avatar is changed and not the default.
    # Our avatar is out of date if we get here
    logging.debug("update_blog_avatar() Avatar needs updating.")

    # Get actual URL for large avatar
    current_large_avatar_api_url = "http://api.tumblr.com/v2/blog/"+blog_url+"/avatar/512"
    large_avatar, large_avatar_info, large_avatar_request = getwithinfo(current_small_avatar_api_url)
    current_large_avatar_real_url = large_avatar_request.geturl()

    if (current_large_avatar_real_url != current_small_avatar_real_url):
        # Save large avatar
        current_large_avatar_media_id_list = image_handlers.download_image_link(
            session = session,
            media_url=current_large_avatar_real_url
            )
        if len(current_large_avatar_media_id_list) != 0:
            logging.debug("Updating large avatar record")
            current_large_avatar_media_id = current_large_avatar_media_id_list[0]
            # Update large avatar record
            update_statement = sqlalchemy.update(twkr_blogs).where(twkr_blogs.blog_id == blog_id).\
                values(user_thumbnail_512_media_id = current_large_avatar_media_id)
            session.execute(update_statement)
    else:
        logging.debug("URLS were the same for both 64x64 and 512x512 avatars! Only saving default 64x64")

    # Save small avatar
    current_small_avatar_media_id_list = image_handlers.download_image_link(
        session = session,
        media_url=current_small_avatar_real_url
        )
    if len(current_small_avatar_media_id_list) != 0:
        logging.debug("Updating small avatar record")
        current_small_avatar_media_id = current_small_avatar_media_id_list[0]
        # Update small avatar record
        update_statement = sqlalchemy.update(twkr_blogs).where(twkr_blogs.blog_id == blog_id).\
            values(user_thumbnail_64_media_id = current_small_avatar_media_id,)
        session.execute(update_statement)

    session.commit()
    return


def update_blog_background(session,blog_url):
    """Update the background image for a blog"""
    logging.debug("Updating background image for blog:"+repr(blog_url))
    # Load blog page
    blog_homepage_url = "http://"+blog_url+""
    page_html = get(blog_homepage_url)
    if not page_html:
        logging.error("Could not get page html, skipping background")
        return
    # Find URL of background image
    # background: #3b627e url('http://static.tumblr.com/c94205eb4c3de586041f1ad660c46caa/idxu2du/eIkno8wrk/tumblr_static_2xi0rehz8qg4owck0cso0os80.png') top left fixed repeat;
    # http://static.tumblr.com/c94205eb4c3de586041f1ad660c46caa/idxu2du/eIkno8wrk/tumblr_static_2xi0rehz8qg4owck0cso0os80.png
    background_image_regex = """background:\s+(?:\#\w+)\s+url\(["']([^\n"']+)["']"""
    background_image_search = re.search(background_image_regex, page_html, re.IGNORECASE|re.DOTALL)
    if background_image_search:
        background_image_url = background_image_search.group(1)
        logging.debug("update_blog_background() background_image_url:"+repr(background_image_url))
        # Save background image
        background_image_media_id_list = image_handlers.download_image_link(
            session = session,
            media_url=background_image_url
            )
        if len(background_image_media_id_list) == 0:# Handle failed downloads
            return
        background_image_media_id = background_image_media_id_list[0]
        # Update blog row with background image
        update_statement = sqlalchemy.update(twkr_blogs).where(twkr_blogs.blog_url == blog_url).\
            values(background_image_media_id = background_image_media_id,)
        session.execute(update_statement)
        return
    else:
        logging.debug("Could not find background image.")
        return


def update_blog_header_image(session,blog_url):
    logging.warning("Header images not yet implimented!")
    logging.debug("Updating header image")
    # Find header image link
    # Save header image
    # Update record for header image
    return


def update_blog_theme(session,blog_url):
    """Update all theme attributes for a blog"""
    logging.debug("update_blog_theme blog_url:"+repr(blog_url))
    # Update avatar for this blog
    update_blog_avatar(session,blog_url)
    # Update blog backgroun image
    update_blog_background(session,blog_url)
    # Update header image
    update_blog_header_image(session,blog_url)
    return



def debug():
    """Temp code for debug"""
    session = sql_functions.connect_to_db()
    blog_urls = [
    #"staff.tumblr.com",
    #"testsetsts2.tumblr.com",
    "lunarshinestore.tumblr.com",
    "atryl.tumblr.com",
    ]
    for blog_url in blog_urls:
        dummy_blog_id = sql_functions.add_blog(session,blog_url)
        logging.debug("dummy_blog_id: "+repr(dummy_blog_id))
        update_blog_theme(session,blog_url)
        continue
    return



def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","blog_themes_log.txt"))
        debug()
        logging.info("Finished, exiting.")
        pass
    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return

if __name__ == '__main__':
    main()
