#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     28/03/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------


# Libraries
import sqlalchemy
import subprocess# For video and some audio downloads
import urllib# For encoding audio urls
import re
import logging
# This project
from utils import *
from sql_functions import Media
import sql_functions
import config # User settings


def handle_tumblr_videos(session,post_dict):
    """Download tumblr-hosted videos from video posts
    https://github.com/rg3/youtube-dl/blob/master/docs/supportedsites.md
    https://github.com/rg3/youtube-dl/"""
    logging.debug("Processing tumblr video")
    video_page = post_dict["post_url"]
    logging.debug("post_dict"+repr(post_dict))
    post_id = str(post_dict["id"])
    logging.debug("video_page: "+repr(video_page))
    logging.debug("post_id: "+repr(post_id))
    # Check if video is already saved
    video_page_query = sqlalchemy.select([Media]).where(Media.media_url == video_page)
    video_page_rows = session.execute(video_page_query)
    video_page_row = video_page_rows.fetchone()
    if video_page_row:
        preexisting_filename = video_page_row["filename"]
        sha512base64_hash = video_page_row["sha512base64_hash"]
        return {"tumblr_video_embed":sha512base64_hash}
    # Load video
    # Form command to run
    # Define arguments. see this url for help
    # https://github.com/rg3/youtube-dl
    program_path = os.path.join("youtube-dl","youtube-dl.exe")
    assert(os.path.exists(program_path))
    ignore_errors = "-i"
    safe_filenames = "--restrict-filenames"
    output_arg = "-o"
    info_json_arg = "--write-info-json"
    description_arg ="--write-description"
    output_dir = os.path.join(config.root_path,"temp")
    output_template = os.path.join(output_dir, post_id+".%(ext)s")
    # "youtube-dl.exe -i --restrict-filenames -o --write-info-json --write-description"
    command = [program_path, ignore_errors, safe_filenames, info_json_arg, description_arg, output_arg, output_template, video_page]
    logging.debug("command: "+repr(command))
    # Call youtube-dl
    command_result = subprocess.call(command)
    logging.debug("command_result: "+repr(command_result))
    # Fail if bad exit code
    if command_result != 0:
        logging.error("Command did not return correct exit code! (Normal exit is 0)")
        return {}
    time_of_retreival = get_current_unix_time()
    # Verify download worked
    # Read info JSON file
    expected_info_path = os.path.join(output_dir, post_id+".info.json")
    info_json = read_file(expected_info_path)
    yt_dl_info_dict = json.loads(info_json)
    logging.debug("yt_dl_info_dict: "+repr(yt_dl_info_dict))
    # Grab file path
    media_temp_filepath = yt_dl_info_dict["_filename"]
    media_temp_filename = os.path.basename(media_temp_filepath)
    logging.debug("media_temp_filepath: "+repr(media_temp_filepath))
    # Check that video file given in info JSON exists
    assert(os.path.exists(media_temp_filepath))
    # Generate hash for media file
    file_data = read_file(media_temp_filepath)
    sha512base64_hash = hash_file_data(file_data)
    # Decide where to put the file
    # Check if hash is in media DB
    hash_check_row_dict = sql_functions.check_if_hash_in_db(session,sha512base64_hash)
    if hash_check_row_dict:
        media_already_saved = True
        preexisting_filename = hash_check_row_dict["filename"]
    else:
        preexisting_filename = None
    # Deal with temp file (Move or delete)
    if preexisting_filename:
        # Delete duplicate file if media is already saved
        logging.info("Deleting duplicate video file: "+repr(media_temp_filepath))
        os.remove(media_temp_filepath)
        os.remove(expected_info_path)
        final_media_filepath = preexisting_filename
    else:
        # Move file to media DL location
        logging.info("Moving video to final location")
        # Generate output filepath
        file_ext = media_temp_filename.split(".")[-1]
        filename = str(time_of_retreival)+file_ext
        final_media_filepath = generate_media_file_path_timestamp(root_path=config.root_path,filename=filename)
        # Move file to final location
        move_file(media_temp_filepath,final_media_filepath)
        assert(os.path.exists(final_media_filepath))

    # Add video to DB
    new_media_row = Media(
    media_url=video_page,
    sha512base64_hash=sha512base64_hash,
    filename=filename,
    date_added=time_of_retreival,
    extractor_used="tumblr_video_embed",
    tumblrvideo_yt_dl_info_json=info_json
    )
    session.add(new_media_row)
    session.commit()
    return {"tumblr_video_embed":sha512base64_hash}


def crop_youube_id(url):
    video_id_regex ="""youtube.com/(?:embed/)?(?:watch\?v=)?([a-zA-Z0-9]+)"""
    video_id_search = re.search(video_id_regex, url, re.IGNORECASE|re.DOTALL)
    if video_id_search:
        video_id = video_id_search.group(1)
        logging.debug("Extracted id: "+repr(video_id)+" from url: "+repr(url))
        return video_id
    else:
        return


def handle_youtube_video(session,post_dict):
    """Download youtube videos from video posts
    https://github.com/rg3/youtube-dl/blob/master/docs/supportedsites.md
    https://github.com/rg3/youtube-dl/"""
    logging.debug("Processing youtube video")
    logging.debug("post_dict"+repr(post_dict))
    assert(post_dict["type"] == u"video")# Ensure calling code isn't broken
    assert(post_dict["video_type"] == u"youtube")# Ensure calling code isn't broken
    video_page = post_dict["post_url"]
    post_id = str(post_dict["id"])
    logging.debug("video_page: "+repr(video_page))
    logging.debug("post_id: "+repr(post_id))
    # Extract youtube links from video field
    # ex. https://www.youtube.com/embed/lGIEmH3BoyA
    video_items = post_dict["player"]
    youtube_urls = []
    for video_item in video_items:
        # Get a youtube URL
        embed_code = video_item["embed_code"]
        # Skip if no embed code to process (Known to happen) "u'player': [{u'embed_code': False, u'width': 250},"
        if embed_code:
            logging.debug("embed_code: "+repr(embed_code))
            embed_url_regex ="""src=["']([^?"']+)\?"""
            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
            if embed_url_search:
                embed_url = embed_url_search.group(1)
                youtube_urls.append(embed_url)
        continue
    # Check if videos are already saved
    new_youtube_urls = []
    for youtube_url in youtube_urls:
        youtube_video_id = crop_youube_id(youtube_url)
        # Look up ID in DB
        video_page_query = sqlalchemy.select([Media]).where(Media.youtube_video_id == youtube_video_id)
        video_page_rows = session.execute(video_page_query)
        video_page_row = video_page_rows.fetchone()
        if video_page_row:
            logging.debug("Skipping previously saved video: "+repr(video_page_row))
        else:
            new_youtube_urls.append(youtube_url)
        continue

    # Prevent duplicates from the same post
    new_youtube_urls = uniquify(new_youtube_urls)

    # Download videos if there are any
    if len(new_youtube_urls) > 0:
        # Download each new video
        for new_youtube_url in new_youtube_urls:
            logging.debug("new_youtube_url: "+repr(new_youtube_url))
            # Form command to run
            # Define arguments. see this url for help
            # https://github.com/rg3/youtube-dl
            program_path = os.path.join("youtube-dl","youtube-dl.exe")
            assert(os.path.exists(program_path))
            ignore_errors = "-i"
            safe_filenames = "--restrict-filenames"
            output_arg = "-o"
            info_json_arg = "--write-info-json"
            description_arg ="--write-description"
            output_dir = os.path.join(config.root_path,"temp")
            output_template = os.path.join(output_dir, post_id+".%(ext)s")
            # "youtube-dl.exe -i --restrict-filenames -o --write-info-json --write-description"
            command = [program_path, ignore_errors, safe_filenames, info_json_arg, description_arg, output_arg, output_template, new_youtube_url]
            logging.debug("command: "+repr(command))
            # Call youtube-dl
            command_result = subprocess.call(command)
            logging.debug("command_result: "+repr(command_result))
            time_of_retreival = get_current_unix_time()
            # Verify download worked
            # Read info JSON file
            expected_info_path = os.path.join(output_dir, post_id+".info.json")
            info_exists = os.path.exists(expected_info_path)
            if not info_exists:
                logging.error("Info file not found!")
                logging.error(repr(locals()))
            info_json = read_file(expected_info_path)
            yt_dl_info_dict = json.loads(info_json)
            logging.debug("yt_dl_info_dict: "+repr(yt_dl_info_dict))
            # Grab file path
            media_temp_filepath = yt_dl_info_dict["_filename"]
            media_temp_filename = os.path.basename(media_temp_filepath)
            logging.debug("media_temp_filepath: "+repr(media_temp_filepath))
            # Check that video file given in info JSON exists
            assert(os.path.exists(media_temp_filepath))
            # Generate hash for media file
            file_data = read_file(media_temp_filepath)
            sha512base64_hash = hash_file_data(file_data)
            # Decide where to put the file

            # Check if hash is in media DB
            video_page_row = sql_functions.check_if_hash_in_db(session,sha512base64_hash)
            if video_page_row:
                # If media already saved, delete temp file and use old entry's data
                filename = video_page_row["filename"]
                logging.debug("Skipping previously saved video: "+repr(video_page_row))
                # Delete duplicate file if media is already saved
                logging.info("Deleting duplicate video file: "+repr(media_temp_filepath))
                os.remove(media_temp_filepath)
                os.remove(expected_info_path)
                continue
            else:
                # If media not in DB, move temp file to permanent location
                # Move file to media DL location
                logging.info("Moving video to final location")
                # Generate output filepath
                file_ext = media_temp_filename.split(".")[-1]
                filename = str(time_of_retreival)+"."+file_ext
                final_media_filepath = generate_media_file_path_timestamp(root_path=config.root_path,filename=filename)
                # Move file to final location
                move_file(media_temp_filepath,final_media_filepath)
                assert(os.path.exists(final_media_filepath))

            # Add video to DB
            new_media_row = Media(
            media_url=new_youtube_url,
            sha512base64_hash=sha512base64_hash,
            filename=filename,
            date_added=time_of_retreival,
            extractor_used="youtube_embed",
            youtube_yt_dl_info_json=info_json
            )
            session.add(new_media_row)
            session.commit()
            continue

        logging.debug("Finished downloading youtube embeds")
        return {"youtube_embed":sha512base64_hash}
    else:
        return {}


def handle_vine_videos(session,post_dict):
    """Handle downloading of vine videos
    https://github.com/rg3/youtube-dl/blob/master/docs/supportedsites.md"""
    logging.debug("post_dict"+repr(post_dict))
    post_id = str(post_dict["id"])
    # Extract video links from post dict
    video_items = post_dict["player"]
    vine_urls = []
    for video_item in video_items:
        embed_code = video_item["embed_code"]
        # u'<iframe class="vine-embed" src="https://vine.co/v/hjWIUFOYD31/embed/simple"width="500" height="500" frameborder="0"></iframe><script async src="//platform.vine.co/static/scripts/embed.js" charset="utf-8"></script>'
        # https://vine.co/v/hjWIUFOYD31
        if embed_code:
            # Process links so YT-DL can understand them
            logging.debug("embed_code: "+repr(embed_code))
            embed_url_regex ="""src=["']([^?"']+)"""
            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
            if embed_url_search:
                embed_url = embed_url_search.group(1)
                vine_urls.append(embed_url)
        continue

    # Deduplicate links
    vine_urls = uniquify(vine_urls)
    logging.debug("vine_urls: "+repr(vine_urls))
    download_urls = []
    # Skip IDs that have already been done
    for vine_url in vine_urls:
        # Extract video ID
        # https://vine.co/v/hjWIUFOYD31/embed/simple -> hjWIUFOYD31
        id_regex ="""vine.co/v/([a-zA-Z0-9]+)/?"""
        id_search = re.search(id_regex, vine_url, re.IGNORECASE|re.DOTALL)
        if id_search:
            # Look up ID in media DB
            video_id = id_search.group(1)
            logging.debug("video_id: "+repr(video_id))
            video_page_query = sqlalchemy.select([Media]).where(Media.media_url == vine_url)
            video_page_rows = session.execute(video_page_query)
            video_page_row = video_page_rows.fetchone()
            if video_page_row:
                logging.debug("Skipping previously saved video: "+repr(video_page_row))
                continue
        download_urls.append(vine_url)
        continue
    logging.debug("download_urls: "+repr(download_urls))
    # Send video URLs to YT-DL
    if len(download_urls) > 0:
        # Download each new video
        for download_url in download_urls:
            logging.debug("download_url: "+repr(download_url))
            # Form command to run
            # Define arguments. see this url for help
            # https://github.com/rg3/youtube-dl
            program_path = os.path.join("youtube-dl","youtube-dl.exe")
            assert(os.path.exists(program_path))
            ignore_errors = "-i"
            safe_filenames = "--restrict-filenames"
            output_arg = "-o"
            info_json_arg = "--write-info-json"
            description_arg ="--write-description"
            output_dir = os.path.join(config.root_path,"temp")
            output_template = os.path.join(output_dir, post_id+".%(ext)s")
            # "youtube-dl.exe -i --restrict-filenames -o --write-info-json --write-description"
            command = [program_path, ignore_errors, safe_filenames, info_json_arg, description_arg, output_arg, output_template, download_url]
            logging.debug("command: "+repr(command))
            # Call youtube-dl
            command_result = subprocess.call(command)
            logging.debug("command_result: "+repr(command_result))
            time_of_retreival = get_current_unix_time()
            # Verify download worked
            # Read info JSON file
            expected_info_path = os.path.join(output_dir, post_id+".info.json")
            info_exists = os.path.exists(expected_info_path)
            if not info_exists:
                logging.error("Info file not found!")
                logging.error(repr(locals()))
            info_json = read_file(expected_info_path)
            yt_dl_info_dict = json.loads(info_json)
            logging.debug("yt_dl_info_dict: "+repr(yt_dl_info_dict))
            # Grab file path
            media_temp_filepath = yt_dl_info_dict["_filename"]
            media_temp_filename = os.path.basename(media_temp_filepath)
            logging.debug("media_temp_filepath: "+repr(media_temp_filepath))
            # Check that video file given in info JSON exists
            assert(os.path.exists(media_temp_filepath))
            # Generate hash for media file
            file_data = read_file(media_temp_filepath)
            sha512base64_hash = hash_file_data(file_data)
            # Decide where to put the file

            # Check if hash is in media DB
            video_page_row = sql_functions.check_if_hash_in_db(session,sha512base64_hash)
            if video_page_row:
                # If media already saved, delete temp file and use old entry's data
                filename = video_page_row["filename"]
                logging.debug("Skipping previously saved video: "+repr(video_page_row))
                # Delete duplicate file if media is already saved
                logging.info("Deleting duplicate video file: "+repr(media_temp_filepath))
                os.remove(media_temp_filepath)
                os.remove(expected_info_path)
                continue
            else:
                # If media not in DB, move temp file to permanent location
                # Move file to media DL location
                logging.info("Moving video to final location")
                # Generate output filepath
                file_ext = media_temp_filename.split(".")[-1]
                filename = str(time_of_retreival)+"."+file_ext
                final_media_filepath = generate_media_file_path_timestamp(root_path=config.root_path,filename=filename)
                # Move file to final location
                move_file(media_temp_filepath,final_media_filepath)
                assert(os.path.exists(final_media_filepath))

            # Add video to DB
            new_media_row = Media(
            media_url=download_url,
            sha512base64_hash=sha512base64_hash,
            filename=filename,
            date_added=time_of_retreival,
            extractor_used="vine_embed",
            vine_yt_dl_info_json=info_json,
            )
            session.add(new_media_row)
            session.commit()
            continue

        logging.debug("Finished downloading youtube embeds")
        return {"vine_embed":sha512base64_hash}
    else:
        return {}


def handle_video_posts(session,post_dict):
    """Decide which video functions to run"""
    # Check if post is a video post
    if post_dict["type"] != u"video":
        return {}
    logging.debug("Post is video")
    # Youtube
    if post_dict["video_type"] == u"youtube":
        logging.debug("Post is youtube")
        return handle_youtube_video(session,post_dict)
    # Tumblr
    elif post_dict["video_type"] == u"tumblr":
        logging.debug("Post is tumblr video")
        return handle_tumblr_videos(session,post_dict)
    # Vine
    elif post_dict["video_type"] == u"vine":
        logging.debug("Post is vine video")
        return handle_vine_videos(session,post_dict)
    else:
        logging.error("Unknown video type!")
        logging.error("locals(): "+repr(locals()))
        assert(False)
    return {}



def main():
    pass

if __name__ == '__main__':
    main()
