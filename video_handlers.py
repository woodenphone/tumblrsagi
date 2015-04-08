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
from yt_dl_common import *
from utils import *
#from sql_functions import Media
from tables import *# This module only has the table classes
import sql_functions
import config # User settings


##def handle_tumblr_videos(session,post_dict):# OLD TABLES
##    """Download tumblr-hosted videos from video posts
##    https://github.com/rg3/youtube-dl/blob/master/docs/supportedsites.md
##    https://github.com/rg3/youtube-dl/"""
##    logging.debug("Processing tumblr video")
##    video_page = post_dict["post_url"]
##    logging.debug("post_dict"+repr(post_dict))
##    post_id = str(post_dict["id"])
##    logging.debug("video_page: "+repr(video_page))
##    logging.debug("post_id: "+repr(post_id))
##
##    # Check if video is already saved
##    video_page_query = sqlalchemy.select([Media]).where(Media.media_url == video_page)
##    video_page_rows = session.execute(video_page_query)
##    video_page_row = video_page_rows.fetchone()
##    if video_page_row:
##        preexisting_filename = video_page_row["filename"]
##        sha512base64_hash = video_page_row["sha512base64_hash"]
##        return {"tumblr_video_embed":sha512base64_hash}
##
##    # Load video
##    # Form command to run
##    # Define arguments. see this url for help
##    # https://github.com/rg3/youtube-dl
##    program_path = config.youtube_dl_path
##    assert(os.path.exists(program_path))
##    ignore_errors = "-i"
##    safe_filenames = "--restrict-filenames"
##    output_arg = "-o"
##    info_json_arg = "--write-info-json"
##    description_arg ="--write-description"
##    output_dir = os.path.join(config.root_path,"temp")
##    output_template = os.path.join(output_dir, post_id+".%(ext)s")
##    # "youtube-dl.exe -i --restrict-filenames -o --write-info-json --write-description"
##    command = [program_path, ignore_errors, safe_filenames, info_json_arg, description_arg, output_arg, output_template, video_page]
##    logging.debug("command: "+repr(command))
##    # Call youtube-dl
##    command_result = subprocess.call(command)
##    logging.debug("command_result: "+repr(command_result))
##    # Fail if bad exit code
##    if command_result != 0:
##        logging.error("Command did not return correct exit code! (Normal exit is 0)")
##        return {}
##    time_of_retreival = get_current_unix_time()
##
##    # Verify download worked
##    # Read info JSON file
##    expected_info_path = os.path.join(output_dir, post_id+".info.json")
##    info_json = read_file(expected_info_path)
##    yt_dl_info_dict = json.loads(info_json)
##    logging.debug("yt_dl_info_dict: "+repr(yt_dl_info_dict))
##    # Grab file path
##    media_temp_filepath = yt_dl_info_dict["_filename"]
##    media_temp_filename = os.path.basename(media_temp_filepath)
##    logging.debug("media_temp_filepath: "+repr(media_temp_filepath))
##    # Check that video file given in info JSON exists
##    assert(os.path.exists(media_temp_filepath))
##
##    # Generate hash for media file
##    file_data = read_file(media_temp_filepath)
##    sha512base64_hash = hash_file_data(file_data)
##
##    # Decide where to put the file
##    # Check if hash is in media DB
##    hash_check_row_dict = sql_functions.check_if_hash_in_db(session,sha512base64_hash)
##    if hash_check_row_dict:
##        media_already_saved = True
##        preexisting_filename = hash_check_row_dict["local_filename"]
##    else:
##        preexisting_filename = None
##
##    # Deal with temp file (Move or delete)
##    if preexisting_filename:
##        # Delete duplicate file if media is already saved
##        logging.info("Deleting duplicate video file: "+repr(media_temp_filepath))
##        os.remove(media_temp_filepath)
##        filename = preexisting_filename
##    else:
##        # Move file to media DL location
##        logging.info("Moving video to final location")
##        # Generate output filepath
##        file_ext = media_temp_filename.split(".")[-1]
##        filename = str(time_of_retreival)+file_ext
##        final_media_filepath = generate_media_file_path_timestamp(root_path=config.root_path,filename=filename)
##        # Move file to final location
##        move_file(media_temp_filepath,final_media_filepath)
##        assert(os.path.exists(final_media_filepath))
##
##    # Remove info file
##    os.remove(expected_info_path)
##
##    # Add video to DB
##    new_media_row = Media(
##        media_url=video_page,
##        sha512base64_hash=sha512base64_hash,
##        local_filename=filename,
##        date_added=time_of_retreival,
##        extractor_used="tumblr_video_embed",
##        tumblrvideo_yt_dl_info_json=info_json
##        )
##    session.add(new_media_row)
##    session.commit()
##    return {"tumblr_video_embed":sha512base64_hash}


def crop_youtube_id(url):
    video_id_regex ="""youtube.com/(?:embed/)?(?:watch\?v=)?([a-zA-Z0-9]+)"""
    video_id_search = re.search(video_id_regex, url, re.IGNORECASE|re.DOTALL)
    if video_id_search:
        video_id = video_id_search.group(1)
        logging.debug("Extracted id: "+repr(video_id)+" from url: "+repr(url))
        return video_id
    else:
        return


##def handle_youtube_video(session,post_dict):# OLD TABLE
##    """Download youtube videos from video posts
##    https://github.com/rg3/youtube-dl/blob/master/docs/supportedsites.md
##    https://github.com/rg3/youtube-dl/"""
##    logging.debug("Processing youtube video")
##    logging.debug("post_dict"+repr(post_dict))
##    assert(post_dict["type"] == u"video")# Ensure calling code isn't broken
##    assert(post_dict["video_type"] == u"youtube")# Ensure calling code isn't broken
##    video_page = post_dict["post_url"]
##    post_id = str(post_dict["id"])
##    logging.debug("video_page: "+repr(video_page))
##    logging.debug("post_id: "+repr(post_id))
##
##    # Extract youtube links from video field
##    # ex. https://www.youtube.com/embed/lGIEmH3BoyA
##    video_items = post_dict["player"]
##    youtube_urls = []
##    for video_item in video_items:
##        # Get a youtube URL
##        embed_code = video_item["embed_code"]
##        # Skip if no embed code to process (Known to happen) "u'player': [{u'embed_code': False, u'width': 250},"
##        if embed_code:
##            logging.debug("embed_code: "+repr(embed_code))
##            embed_url_regex ="""src=["']([^?"']+)\?"""
##            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
##            if embed_url_search:
##                embed_url = embed_url_search.group(1)
##                youtube_urls.append(embed_url)
##        continue
##
##    # Check if videos are already saved
##    new_youtube_urls = []
##    for youtube_url in youtube_urls:
##        youtube_video_id = crop_youtube_id(youtube_url)
##        # Look up ID in DB
##        video_page_query = sqlalchemy.select([Media]).where(Media.youtube_video_id == youtube_video_id)
##        video_page_rows = session.execute(video_page_query)
##        video_page_row = video_page_rows.fetchone()
##        if video_page_row:
##            logging.debug("Skipping previously saved video: "+repr(video_page_row))
##        else:
##            new_youtube_urls.append(youtube_url)
##        continue
##
##    # Prevent duplicates from the same post
##    new_youtube_urls = uniquify(new_youtube_urls)
##
##    # Download videos if there are any
##    if len(new_youtube_urls) > 0:
##        # Download each new video
##        for new_youtube_url in new_youtube_urls:
##            logging.debug("new_youtube_url: "+repr(new_youtube_url))
##            # Form command to run
##            # Define arguments. see this url for help
##            # https://github.com/rg3/youtube-dl
##            program_path = config.youtube_dl_path
##            assert(os.path.exists(program_path))
##            ignore_errors = "-i"
##            safe_filenames = "--restrict-filenames"
##            output_arg = "-o"
##            info_json_arg = "--write-info-json"
##            description_arg ="--write-description"
##            output_dir = os.path.join(config.root_path,"temp")
##            output_template = os.path.join(output_dir, post_id+".%(ext)s")
##            # "youtube-dl.exe -i --restrict-filenames -o --write-info-json --write-description"
##            command = [program_path, ignore_errors, safe_filenames, info_json_arg, description_arg, output_arg, output_template, new_youtube_url]
##            logging.debug("command: "+repr(command))
##            # Call youtube-dl
##            command_result = subprocess.call(command)
##            logging.debug("command_result: "+repr(command_result))
##            time_of_retreival = get_current_unix_time()
##            # Verify download worked
##            # Read info JSON file
##            expected_info_path = os.path.join(output_dir, post_id+".info.json")
##            info_exists = os.path.exists(expected_info_path)
##            if not info_exists:
##                logging.error("Info file not found!")
##                logging.error(repr(locals()))
##            info_json = read_file(expected_info_path)
##            yt_dl_info_dict = json.loads(info_json)
##            logging.debug("yt_dl_info_dict: "+repr(yt_dl_info_dict))
##            # Grab file path
##            media_temp_filepath = yt_dl_info_dict["_filename"]
##            media_temp_filename = os.path.basename(media_temp_filepath)
##            logging.debug("media_temp_filepath: "+repr(media_temp_filepath))
##            # Check that video file given in info JSON exists
##            assert(os.path.exists(media_temp_filepath))
##            # Generate hash for media file
##            file_data = read_file(media_temp_filepath)
##            sha512base64_hash = hash_file_data(file_data)
##            # Decide where to put the file
##
##            # Check if hash is in media DB
##            video_page_row = sql_functions.check_if_hash_in_db(session,sha512base64_hash)
##            if video_page_row:
##                # If media already saved, delete temp file and use old entry's data
##                filename = video_page_row["local_filename"]
##                logging.debug("Skipping previously saved video: "+repr(video_page_row))
##                # Delete duplicate file if media is already saved
##                logging.info("Deleting duplicate video file: "+repr(media_temp_filepath))
##                os.remove(media_temp_filepath)
##            else:
##                # If media not in DB, move temp file to permanent location
##                # Move file to media DL location
##                logging.info("Moving video to final location")
##                # Generate output filepath
##                file_ext = media_temp_filename.split(".")[-1]
##                filename = str(time_of_retreival)+"."+file_ext
##                final_media_filepath = generate_media_file_path_timestamp(root_path=config.root_path,filename=filename)
##                # Move file to final location
##                move_file(media_temp_filepath,final_media_filepath)
##                assert(os.path.exists(final_media_filepath))
##
##            # Remove info file
##            os.remove(expected_info_path)
##
##            # Add video to DB
##            new_media_row = Media(
##                media_url=new_youtube_url,
##                sha512base64_hash=sha512base64_hash,
##                local_filename=filename,
##                date_added=time_of_retreival,
##                extractor_used="youtube_embed",
##                youtube_yt_dl_info_json=info_json
##                )
##            session.add(new_media_row)
##            session.commit()
##            continue
##
##        logging.debug("Finished downloading youtube embeds")
##        return {"youtube_embed":sha512base64_hash}
##    else:
##        return {}


##def handle_vine_videos(session,post_dict):# OLD TABLE
##    """Handle downloading of vine videos
##    https://github.com/rg3/youtube-dl/blob/master/docs/supportedsites.md"""
##    logging.debug("post_dict"+repr(post_dict))
##    post_id = str(post_dict["id"])
##
##    # Extract video links from post dict
##    video_items = post_dict["player"]
##    vine_urls = []
##    for video_item in video_items:
##        embed_code = video_item["embed_code"]
##        # u'<iframe class="vine-embed" src="https://vine.co/v/hjWIUFOYD31/embed/simple"width="500" height="500" frameborder="0"></iframe><script async src="//platform.vine.co/static/scripts/embed.js" charset="utf-8"></script>'
##        # https://vine.co/v/hjWIUFOYD31
##        if embed_code:
##            # Process links so YT-DL can understand them
##            logging.debug("embed_code: "+repr(embed_code))
##            embed_url_regex ="""src=["']([^?"']+)"""
##            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
##            if embed_url_search:
##                embed_url = embed_url_search.group(1)
##                vine_urls.append(embed_url)
##        continue
##
##    # Deduplicate links
##    vine_urls = uniquify(vine_urls)
##    logging.debug("vine_urls: "+repr(vine_urls))
##
##    download_urls = []
##    # Skip IDs that have already been done
##    for vine_url in vine_urls:
##        # Extract video ID
##        # https://vine.co/v/hjWIUFOYD31/embed/simple -> hjWIUFOYD31
##        id_regex ="""vine.co/v/([a-zA-Z0-9]+)/?"""
##        id_search = re.search(id_regex, vine_url, re.IGNORECASE|re.DOTALL)
##        if id_search:
##            # Look up ID in media DB
##            video_id = id_search.group(1)
##            logging.debug("video_id: "+repr(video_id))
##            video_page_query = sqlalchemy.select([Media]).where(Media.media_url == vine_url)
##            video_page_rows = session.execute(video_page_query)
##            video_page_row = video_page_rows.fetchone()
##            if video_page_row:
##                logging.debug("Skipping previously saved video: "+repr(video_page_row))
##                continue
##        download_urls.append(vine_url)
##        continue
##    logging.debug("download_urls: "+repr(download_urls))
##
##    # Send video URLs to YT-DL
##    if len(download_urls) > 0:
##        # Download each new video
##        for download_url in download_urls:
##            logging.debug("download_url: "+repr(download_url))
##
##            # Form command to run
##            # Define arguments. see this url for help
##            # https://github.com/rg3/youtube-dl
##            program_path = config.youtube_dl_path
##            assert(os.path.exists(program_path))
##            ignore_errors = "-i"
##            safe_filenames = "--restrict-filenames"
##            output_arg = "-o"
##            info_json_arg = "--write-info-json"
##            description_arg ="--write-description"
##            output_dir = os.path.join(config.root_path,"temp")
##            output_template = os.path.join(output_dir, post_id+".%(ext)s")
##            # "youtube-dl.exe -i --restrict-filenames -o --write-info-json --write-description"
##            command = [program_path, ignore_errors, safe_filenames, info_json_arg, description_arg, output_arg, output_template, download_url]
##            logging.debug("command: "+repr(command))
##            # Call youtube-dl
##            command_result = subprocess.call(command)
##            logging.debug("command_result: "+repr(command_result))
##            time_of_retreival = get_current_unix_time()
##
##            # Verify download worked
##            # Read info JSON file
##            expected_info_path = os.path.join(output_dir, post_id+".info.json")
##            info_exists = os.path.exists(expected_info_path)
##            if not info_exists:
##                logging.error("Info file not found!")
##                logging.error(repr(locals()))
##            info_json = read_file(expected_info_path)
##            yt_dl_info_dict = json.loads(info_json)
##            logging.debug("yt_dl_info_dict: "+repr(yt_dl_info_dict))
##            # Grab file path
##            media_temp_filepath = yt_dl_info_dict["_filename"]
##            media_temp_filename = os.path.basename(media_temp_filepath)
##            logging.debug("media_temp_filepath: "+repr(media_temp_filepath))
##            # Check that video file given in info JSON exists
##            assert(os.path.exists(media_temp_filepath))
##            # Generate hash for media file
##            file_data = read_file(media_temp_filepath)
##            sha512base64_hash = hash_file_data(file_data)
##            # Decide where to put the file
##
##            # Check if hash is in media DB
##            video_page_row = sql_functions.check_if_hash_in_db(session,sha512base64_hash)
##            if video_page_row:
##                # If media already saved, delete temp file and use old entry's data
##                filename = video_page_row["local_filename"]
##                logging.debug("Skipping previously saved video: "+repr(video_page_row))
##                # Delete duplicate file if media is already saved
##                logging.info("Deleting duplicate video file: "+repr(media_temp_filepath))
##                os.remove(media_temp_filepath)
##            else:
##                # If media not in DB, move temp file to permanent location
##                # Move file to media DL location
##                logging.info("Moving video to final location")
##                # Generate output filepath
##                file_ext = media_temp_filename.split(".")[-1]
##                filename = str(time_of_retreival)+"."+file_ext
##                final_media_filepath = generate_media_file_path_timestamp(root_path=config.root_path,filename=filename)
##                # Move file to final location
##                move_file(media_temp_filepath,final_media_filepath)
##                assert(os.path.exists(final_media_filepath))
##
##            # Remove info file
##            os.remove(expected_info_path)
##
##            # Add video to DB
##            new_media_row = Media(
##                media_url=download_url,
##                sha512base64_hash=sha512base64_hash,
##                local_filename=filename,
##                date_added=time_of_retreival,
##                extractor_used="vine_embed",
##                vine_yt_dl_info_json=info_json,
##                )
##            session.add(new_media_row)
##            session.commit()
##            continue
##
##        logging.debug("Finished downloading youtube embeds")
##        return {"vine_embed":sha512base64_hash}
##    else:
##        return {}


##def handle_vimeo_videos(session,post_dict):# OLD TABLE
##    """Handle downloading of vimeo videos
##    https://github.com/rg3/youtube-dl/blob/master/docs/supportedsites.md"""
##    logging.debug("post_dict"+repr(post_dict))
##    post_id = str(post_dict["id"])
##    # Extract video links from post dict
##    video_items = post_dict["player"]
##    vimeo_urls = []
##    for video_item in video_items:
##        embed_code = video_item["embed_code"]
##        # u'<iframe src="https://player.vimeo.com/video/118912193?title=0&byline=0&portrait=0" width="250" height="156" frameborder="0" title="Hyperfast Preview - Mai (Patreon Process Videos)" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>'
##        # https://player.vimeo.com/video/118912193?
##        if embed_code:
##            # Process links so YT-DL can understand them
##            logging.debug("embed_code: "+repr(embed_code))
##            embed_url_regex ="""src=["']([^?"']+)"""
##            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
##            if embed_url_search:
##                embed_url = embed_url_search.group(1)
##                vimeo_urls.append(embed_url)
##        continue
##
##    # Deduplicate links
##    vimeo_urls = uniquify(vimeo_urls)
##    logging.debug("vimeo_urls: "+repr(vimeo_urls))
##
##    download_urls = []
##    # Skip IDs that have already been done
##    for vimeo_url in vimeo_urls:
##        video_page_query = sqlalchemy.select([Media]).where(Media.media_url == vimeo_url)
##        video_page_rows = session.execute(video_page_query)
##        video_page_row = video_page_rows.fetchone()
##        if video_page_row:
##            logging.debug("Skipping previously saved video: "+repr(video_page_row))
##            continue
##        download_urls.append(vimeo_url)
##        continue
##    logging.debug("download_urls: "+repr(download_urls))
##
##    # Send video URLs to YT-DL
##    if len(download_urls) > 0:
##        # Download each new video
##        for download_url in download_urls:
##            logging.debug("download_url: "+repr(download_url))
##            # Form command to run
##            # Define arguments. see this url for help
##            # https://github.com/rg3/youtube-dl
##            program_path = config.youtube_dl_path
##            assert(os.path.exists(program_path))
##            ignore_errors = "-i"
##            safe_filenames = "--restrict-filenames"
##            output_arg = "-o"
##            info_json_arg = "--write-info-json"
##            description_arg ="--write-description"
##            output_dir = os.path.join(config.root_path,"temp")
##            output_template = os.path.join(output_dir, post_id+".%(ext)s")
##            # "youtube-dl.exe -i --restrict-filenames -o --write-info-json --write-description"
##            command = [program_path, ignore_errors, safe_filenames, info_json_arg, description_arg, output_arg, output_template, download_url]
##            logging.debug("command: "+repr(command))
##            # Call youtube-dl
##            command_result = subprocess.call(command)
##            logging.debug("command_result: "+repr(command_result))
##            time_of_retreival = get_current_unix_time()
##            # Verify download worked
##            # Read info JSON file
##            expected_info_path = os.path.join(output_dir, post_id+".info.json")
##            info_exists = os.path.exists(expected_info_path)
##            if not info_exists:
##                logging.error("Info file not found!")
##                logging.error(repr(locals()))
##            info_json = read_file(expected_info_path)
##            yt_dl_info_dict = json.loads(info_json)
##            logging.debug("yt_dl_info_dict: "+repr(yt_dl_info_dict))
##            # Grab file path
##            media_temp_filepath = yt_dl_info_dict["_filename"]
##            media_temp_filename = os.path.basename(media_temp_filepath)
##            logging.debug("media_temp_filepath: "+repr(media_temp_filepath))
##            # Check that video file given in info JSON exists
##            assert(os.path.exists(media_temp_filepath))
##            # Generate hash for media file
##            file_data = read_file(media_temp_filepath)
##            sha512base64_hash = hash_file_data(file_data)
##            # Decide where to put the file
##
##            # Check if hash is in media DB
##            video_page_row = sql_functions.check_if_hash_in_db(session,sha512base64_hash)
##            if video_page_row:
##                # If media already saved, delete temp file and use old entry's data
##                filename = video_page_row["local_filename"]
##                logging.debug("Skipping previously saved video: "+repr(video_page_row))
##                # Delete duplicate file if media is already saved
##                logging.info("Deleting duplicate video file: "+repr(media_temp_filepath))
##                os.remove(media_temp_filepath)
##            else:
##                # If media not in DB, move temp file to permanent location
##                # Move file to media DL location
##                logging.info("Moving video to final location")
##                # Generate output filepath
##                file_ext = media_temp_filename.split(".")[-1]
##                filename = str(time_of_retreival)+"."+file_ext
##                final_media_filepath = generate_media_file_path_timestamp(root_path=config.root_path,filename=filename)
##                # Move file to final location
##                move_file(media_temp_filepath,final_media_filepath)
##                assert(os.path.exists(final_media_filepath))
##
##            # Remove info file
##            os.remove(expected_info_path)
##
##            # Add video to DB
##            new_media_row = Media(
##                media_url=download_url,
##                sha512base64_hash=sha512base64_hash,
##                local_filename=filename,
##                date_added=time_of_retreival,
##                extractor_used="vimeo_embed",
##                vimeo_yt_dl_info_json=info_json,
##                )
##            session.add(new_media_row)
##            session.commit()
##            continue
##
##        logging.debug("Finished downloading vimeo embeds")
##        return {"vimeo_embed":sha512base64_hash}
##    else:
##        return {}


##def handle_imgur_videos(session,post_dict):# OLD TABLES
##    """This is where I plan to put code for imgur videos"""
##    logging.debug("post_dict"+repr(post_dict))
##
##    post_id = str(post_dict["id"])
##
##    # Extract video links from post dict
##    imgur_urls = []
##    video_items = post_dict["player"]
##    for video_item in video_items:
##        embed_code = video_item["embed_code"]
##        # u'<iframe class="imgur-embed" width="100%" height="720" frameborder="0" src="http://i.imgur.com/wSBlRyv.gifv#embed"></iframe>'
##        # http://i.imgur.com/wSBlRyv.gifv
##        if embed_code:
##            # Process links so YT-DL can understand them
##            logging.debug("embed_code: "+repr(embed_code))
##            embed_url_regex ="""src=["']([^?"'#]+)"""
##            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
##            if embed_url_search:
##                embed_url = embed_url_search.group(1)
##                imgur_urls.append(embed_url)
##        continue
##
##    # Deduplicate links
##    imgur_urls = uniquify(imgur_urls)
##    logging.debug("imgur_urls: "+repr(imgur_urls))
##
##    # Skip IDs that have already been done
##    download_urls = []
##    for imgur_url in imgur_urls:
##        video_page_query = sqlalchemy.select([Media]).where(Media.media_url == imgur_url)
##        video_page_rows = session.execute(video_page_query)
##        video_page_row = video_page_rows.fetchone()
##        if video_page_row:
##            logging.debug("Skipping previously saved video: "+repr(video_page_row))
##            continue
##        download_urls.append(imgur_url)
##        continue
##    logging.debug("download_urls: "+repr(download_urls))
##
##    # Send video URLs to YT-DL
##    if len(download_urls) > 0:
##        # Download each new video
##        for download_url in download_urls:
##            logging.debug("download_url: "+repr(download_url))
##            # Form command to run
##            # Define arguments. see this url for help
##            # https://github.com/rg3/youtube-dl
##            program_path = config.youtube_dl_path
##            assert(os.path.exists(program_path))
##            ignore_errors = "-i"
##            safe_filenames = "--restrict-filenames"
##            output_arg = "-o"
##            info_json_arg = "--write-info-json"
##            description_arg ="--write-description"
##            output_dir = os.path.join(config.root_path,"temp")
##            output_template = os.path.join(output_dir, post_id+".%(ext)s")
##            # "youtube-dl.exe -i --restrict-filenames -o --write-info-json --write-description"
##            command = [program_path, ignore_errors, safe_filenames, info_json_arg, description_arg, output_arg, output_template, download_url]
##            logging.debug("command: "+repr(command))
##            # Call youtube-dl
##            command_result = subprocess.call(command)
##            logging.debug("command_result: "+repr(command_result))
##            time_of_retreival = get_current_unix_time()
##            # Verify download worked
##            # Read info JSON file
##            expected_info_path = os.path.join(output_dir, post_id+".info.json")
##            info_exists = os.path.exists(expected_info_path)
##            if not info_exists:
##                logging.error("Info file not found!")
##                logging.error(repr(locals()))
##            info_json = read_file(expected_info_path)
##            yt_dl_info_dict = json.loads(info_json)
##            logging.debug("yt_dl_info_dict: "+repr(yt_dl_info_dict))
##            # Grab file path
##            media_temp_filepath = yt_dl_info_dict["_filename"]
##            media_temp_filename = os.path.basename(media_temp_filepath)
##            logging.debug("media_temp_filepath: "+repr(media_temp_filepath))
##            # Check that video file given in info JSON exists
##            assert(os.path.exists(media_temp_filepath))
##            # Generate hash for media file
##            file_data = read_file(media_temp_filepath)
##            sha512base64_hash = hash_file_data(file_data)
##            # Decide where to put the file
##
##            # Check if hash is in media DB
##            video_page_row = sql_functions.check_if_hash_in_db(session,sha512base64_hash)
##            if video_page_row:
##                # If media already saved, delete temp file and use old entry's data
##                filename = video_page_row["local_filename"]
##                logging.debug("Skipping previously saved video: "+repr(video_page_row))
##                # Delete duplicate file if media is already saved
##                logging.info("Deleting duplicate video file: "+repr(media_temp_filepath))
##                os.remove(media_temp_filepath)
##            else:
##                # If media not in DB, move temp file to permanent location
##                # Move file to media DL location
##                logging.info("Moving video to final location")
##                # Generate output filepath
##                file_ext = media_temp_filename.split(".")[-1]
##                filename = str(time_of_retreival)+"."+file_ext
##                final_media_filepath = generate_media_file_path_timestamp(root_path=config.root_path,filename=filename)
##                # Move file to final location
##                move_file(media_temp_filepath,final_media_filepath)
##                assert(os.path.exists(final_media_filepath))
##
##            # Remove info file
##            os.remove(expected_info_path)
##
##            # Add video to DB
##            new_media_row = Media(
##                media_url=download_url,
##                sha512base64_hash=sha512base64_hash,
##                local_filename=filename,
##                date_added=time_of_retreival,
##                extractor_used="imgur_video_embed",
##                imgur_video_yt_dl_info_json=info_json,
##                )
##            session.add(new_media_row)
##            session.commit()
##            continue
##
##        logging.debug("Finished downloading imgur_video embeds")
##        return {"imgur_video_embed":sha512base64_hash}
##    else:
##        return {}





##def handle_livestream_videos(session,post_dict):#OLD TABLES
##    """This is where I plan to put code for imgur videos"""
##    logging.debug("post_dict"+repr(post_dict))
##
##    post_id = str(post_dict["id"])
##
##    # Extract video links from post dict
##    livestream_urls = []
##    video_items = post_dict["player"]
##    for video_item in video_items:
##        embed_code = video_item["embed_code"]
##        # u'<iframe src="http://new.livestream.com/accounts/1249127/events/3464519/player?width=560&height=315&autoPlay=true&mute=false" width="250" height="140" frameborder="0" scrolling="no"> </iframe>'
##        # http://new.livestream.com/accounts/1249127/events/3464519/player?
##        if embed_code:
##            # Process links so YT-DL can understand them
##            logging.debug("embed_code: "+repr(embed_code))
##            embed_url_regex ="""src=["']([^?"'#]+)"""
##            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
##            if embed_url_search:
##                embed_url = embed_url_search.group(1)
##                livestream_urls.append(embed_url)
##        continue
##
##    # Deduplicate links
##    livestream_urls = uniquify(livestream_urls)
##    logging.debug("livestream_urls: "+repr(livestream_urls))
##
##    # Skip IDs that have already been done
##    download_urls = []
##    for livestream_url in livestream_urls:
##        video_page_query = sqlalchemy.select([Media]).where(Media.media_url == livestream_url)
##        video_page_rows = session.execute(video_page_query)
##        video_page_row = video_page_rows.fetchone()
##        if video_page_row:
##            logging.debug("Skipping previously saved video: "+repr(video_page_row))
##            continue
##        download_urls.append(livestream_url)
##        continue
##    logging.debug("download_urls: "+repr(download_urls))
##
##    # Send video URLs to YT-DL
##    if len(download_urls) > 0:
##        # Download each new video
##        for download_url in download_urls:
##            logging.debug("download_url: "+repr(download_url))
##
##            # Form command to run
##            # Define arguments. see this url for help
##            # https://github.com/rg3/youtube-dl
##            program_path = config.youtube_dl_path
##            assert(os.path.exists(program_path))
##            ignore_errors = "-i"
##            safe_filenames = "--restrict-filenames"
##            output_arg = "-o"
##            info_json_arg = "--write-info-json"
##            description_arg ="--write-description"
##            output_dir = os.path.join(config.root_path,"temp")
##            output_template = os.path.join(output_dir, post_id+".%(ext)s")
##            # "youtube-dl.exe -i --restrict-filenames -o --write-info-json --write-description"
##            command = [program_path, ignore_errors, safe_filenames, info_json_arg, description_arg, output_arg, output_template, download_url]
##            logging.debug("command: "+repr(command))
##            # Call youtube-dl
##            command_result = subprocess.call(command)
##            logging.debug("command_result: "+repr(command_result))
##            time_of_retreival = get_current_unix_time()
##
##            # Verify download worked
##            if command_result != 1:
##                logging.error("Command did not return 1, this means something went wrong.")
##                logging.error("Failed to save media: "+repr(download_url))
##                return {}
##            # Read info JSON file
##            expected_info_path = os.path.join(output_dir, post_id+".info.json")
##            info_exists = os.path.exists(expected_info_path)
##            if not info_exists:
##                logging.error("Info file not found!")
##                logging.error(repr(locals()))
##            info_json = read_file(expected_info_path)
##            yt_dl_info_dict = json.loads(info_json)
##            logging.debug("yt_dl_info_dict: "+repr(yt_dl_info_dict))
##
##            # Grab file path
##            media_temp_filepath = yt_dl_info_dict["_filename"]
##            media_temp_filename = os.path.basename(media_temp_filepath)
##            logging.debug("media_temp_filepath: "+repr(media_temp_filepath))
##
##            # Check that video file given in info JSON exists
##            if not os.path.exists(media_temp_filepath):
##                logging.error("Video file not found!")
##                logging.error("Failed to save media: "+repr(download_url))
##                return {}
##
##            # Generate hash for media file
##            file_data = read_file(media_temp_filepath)
##            sha512base64_hash = hash_file_data(file_data)
##            # Decide where to put the file
##
##            # Check if hash is in media DB
##            video_page_row = sql_functions.check_if_hash_in_db(session,sha512base64_hash)
##            if video_page_row:
##                # If media already saved, delete temp file and use old entry's data
##                filename = video_page_row["local_filename"]
##                logging.debug("Skipping previously saved video: "+repr(video_page_row))
##                # Delete duplicate file if media is already saved
##                logging.info("Deleting duplicate video file: "+repr(media_temp_filepath))
##                os.remove(media_temp_filepath)
##            else:
##                # If media not in DB, move temp file to permanent location
##                # Move file to media DL location
##                logging.info("Moving video to final location")
##                # Generate output filepath
##                file_ext = media_temp_filename.split(".")[-1]
##                filename = str(time_of_retreival)+"."+file_ext
##                final_media_filepath = generate_media_file_path_timestamp(root_path=config.root_path,filename=filename)
##                # Move file to final location
##                move_file(media_temp_filepath,final_media_filepath)
##                assert(os.path.exists(final_media_filepath))
##
##            # Remove info file
##            os.remove(expected_info_path)
##
##            # Add video to DB
##            new_media_row = Media(
##                media_url=download_url,
##                sha512base64_hash=sha512base64_hash,
##                local_filename=filename,
##                date_added=time_of_retreival,
##                extractor_used="livestream_video_embed",
##                livestream_yt_dl_info_json=info_json,
##                )
##            session.add(new_media_row)
##            session.commit()
##            continue
##
##        logging.debug("Finished downloading livestream_embed embeds")
##        return {"livestream_video_embed":sha512base64_hash}
##    else:
##        return {}






# updated for new tables and yt-dl wrapper
def handle_youtube_video(session,post_dict):# NEW TABLES
    """Download youtube videos from video posts
    https://github.com/rg3/youtube-dl/blob/master/docs/supportedsites.md
    https://github.com/rg3/youtube-dl/"""
    assert(post_dict["type"] == u"video")# Ensure calling code isn't broken
    assert(post_dict["video_type"] == u"youtube")# Ensure calling code isn't broken

    logging.debug("Processing youtube video")
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
    download_urls = []
    for youtube_url in youtube_urls:
        video_id = crop_youtube_id(youtube_url)
        # Look up ID in DB
        video_page_query = sqlalchemy.select([YoutubeVideo]).where(YoutubeVideo.video_id == video_id)
        video_page_rows = session.execute(video_page_query)
        video_page_row = video_page_rows.fetchone()
        if video_page_row:
            logging.debug("Skipping previously saved video: "+repr(video_page_row))
        else:
            download_urls.append(youtube_url)
        continue

    # Download videos if there are any
    combined_video_dict = run_yt_dl_multiple(
        session = session,
        post_dict = post_dict,
        table_class = YoutubeVideo,
        download_urls = download_urls,
        post_id = post_id,
        )
    return combined_video_dict


def handle_vimeo_videos(session,post_dict):# New table
    """Handle downloading of vimeo videos
    https://github.com/rg3/youtube-dl/blob/master/docs/supportedsites.md"""
    logging.debug("Processing vimeo videos")
    post_id = str(post_dict["id"])
    # Extract video links from post dict
    video_items = post_dict["player"]
    vimeo_urls = []
    for video_item in video_items:
        embed_code = video_item["embed_code"]
        # u'<iframe src="https://player.vimeo.com/video/118912193?title=0&byline=0&portrait=0" width="250" height="156" frameborder="0" title="Hyperfast Preview - Mai (Patreon Process Videos)" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>'
        # https://player.vimeo.com/video/118912193?
        if embed_code:
            # Process links so YT-DL can understand them
            logging.debug("embed_code: "+repr(embed_code))
            embed_url_regex ="""src=["']([^?"']+)"""
            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
            if embed_url_search:
                embed_url = embed_url_search.group(1)
                vimeo_urls.append(embed_url)
        continue

    # Deduplicate links
    vimeo_urls = uniquify(vimeo_urls)
    logging.debug("vimeo_urls: "+repr(vimeo_urls))

    # Skip IDs that have already been done
    download_urls = []
    for vimeo_url in vimeo_urls:
        video_page_query = sqlalchemy.select([VimeoVideo]).where(VimeoVideo.media_url == vimeo_url)
        video_page_rows = session.execute(video_page_query)
        video_page_row = video_page_rows.fetchone()
        if video_page_row:
            logging.debug("Skipping previously saved video: "+repr(video_page_row))
            continue
        download_urls.append(vimeo_url)
        continue
    logging.debug("download_urls: "+repr(download_urls))

    # Download videos if there are any
    combined_video_dict = run_yt_dl_multiple(
        session = session,
        post_dict = post_dict,
        table_class = VimeoVideo,
        download_urls = download_urls,
        post_id = post_id,
        )
    logging.debug("Finished downloading vimeo embeds")
    return combined_video_dict


def handle_imgur_videos(session,post_dict):# NEW TABLES
    """This is where I plan to put code for imgur videos"""
    logging.debug("Processing imgur videos")
    post_id = str(post_dict["id"])

    # Extract video links from post dict
    imgur_urls = []
    video_items = post_dict["player"]
    for video_item in video_items:
        embed_code = video_item["embed_code"]
        # u'<iframe class="imgur-embed" width="100%" height="720" frameborder="0" src="http://i.imgur.com/wSBlRyv.gifv#embed"></iframe>'
        # http://i.imgur.com/wSBlRyv.gifv
        if embed_code:
            # Process links so YT-DL can understand them
            logging.debug("embed_code: "+repr(embed_code))
            embed_url_regex ="""src=["']([^?"'#]+)"""
            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
            if embed_url_search:
                embed_url = embed_url_search.group(1)
                imgur_urls.append(embed_url)
        continue

    # Deduplicate links
    imgur_urls = uniquify(imgur_urls)
    logging.debug("imgur_urls: "+repr(imgur_urls))

    # Skip IDs that have already been done
    download_urls = []
    for imgur_url in imgur_urls:
        video_page_query = sqlalchemy.select([ImgurVideo]).where(ImgurVideo.media_url == imgur_url)
        video_page_rows = session.execute(video_page_query)
        video_page_row = video_page_rows.fetchone()
        if video_page_row:
            logging.debug("Skipping previously saved video: "+repr(video_page_row))
            continue
        download_urls.append(imgur_url)
        continue
    logging.debug("download_urls: "+repr(download_urls))

    # Download videos if there are any
    combined_video_dict = run_yt_dl_multiple(
        session = session,
        post_dict = post_dict,
        table_class = ImgurVideo,
        download_urls = download_urls,
        post_id = post_id,
        )
    logging.debug("Finished downloading imgur_video embeds")
    return combined_video_dict


def handle_vine_videos(session,post_dict):# New table
    """Handle downloading of vine videos
    https://github.com/rg3/youtube-dl/blob/master/docs/supportedsites.md"""
    logging.debug("Processing vine videos")
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

    # Skip URLs that have already been done
    download_urls = []
    for vine_url in vine_urls:
        # Extract video ID
        # https://vine.co/v/hjWIUFOYD31/embed/simple -> hjWIUFOYD31
        id_regex ="""vine.co/v/([a-zA-Z0-9]+)/?"""
        id_search = re.search(id_regex, vine_url, re.IGNORECASE|re.DOTALL)
        if id_search:
            # Look up ID in media DB
            video_id = id_search.group(1)
            logging.debug("video_id: "+repr(video_id))
            video_page_query = sqlalchemy.select([VineVideo]).where(VineVideo.media_url == vine_url)
            video_page_rows = session.execute(video_page_query)
            video_page_row = video_page_rows.fetchone()
            if video_page_row:
                logging.debug("Skipping previously saved video: "+repr(video_page_row))
                continue
        download_urls.append(vine_url)
        continue
    logging.debug("download_urls: "+repr(download_urls))

    # Download videos if there are any
    combined_video_dict = run_yt_dl_multiple(
        session = session,
        post_dict = post_dict,
        table_class = VineVideo,
        download_urls = download_urls,
        post_id = post_id,
        )
    logging.debug("Finished downloading Vine embeds")
    return combined_video_dict


def handle_tumblr_videos(session,post_dict):
    """Download tumblr-hosted videos from video posts
    https://github.com/rg3/youtube-dl/blob/master/docs/supportedsites.md
    https://github.com/rg3/youtube-dl/"""
    logging.debug("Processing tumblr video")
    video_page = post_dict["post_url"]
    post_id = str(post_dict["id"])
    logging.debug("video_page: "+repr(video_page))
    logging.debug("post_id: "+repr(post_id))

    # Check if video is already saved, return URL:Hash pair if it is
    video_page_query = sqlalchemy.select([TubmlrVideo]).where(TubmlrVideo.media_url == video_page)
    video_page_rows = session.execute(video_page_query)
    video_page_row = video_page_rows.fetchone()
    if video_page_row:
        preexisting_filename = video_page_row["filename"]
        sha512base64_hash = video_page_row["sha512base64_hash"]
        return {video_page:sha512base64_hash}

    download_urls = [video_page]
    # Download videos if there are any
    combined_video_dict = run_yt_dl_multiple(
        session = session,
        post_dict = post_dict,
        table_class = TubmlrVideo,
        download_urls = download_urls,
        post_id = post_id,
        )
    logging.debug("Finished downloading Tumblr embeds")
    return combined_video_dict


def handle_livestream_videos(session,post_dict):
    """This is where I plan to put code for imgur videos"""
    logging.debug("Processing livestream video")
    post_id = str(post_dict["id"])

    # Extract video links from post dict
    livestream_urls = []
    video_items = post_dict["player"]
    for video_item in video_items:
        embed_code = video_item["embed_code"]
        # u'<iframe src="http://new.livestream.com/accounts/1249127/events/3464519/player?width=560&height=315&autoPlay=true&mute=false" width="250" height="140" frameborder="0" scrolling="no"> </iframe>'
        # http://new.livestream.com/accounts/1249127/events/3464519/player?
        if embed_code:
            # Process links so YT-DL can understand them
            logging.debug("embed_code: "+repr(embed_code))
            embed_url_regex ="""src=["']([^?"'#]+)"""
            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
            if embed_url_search:
                embed_url = embed_url_search.group(1)
                livestream_urls.append(embed_url)
        continue

    # Deduplicate links
    livestream_urls = uniquify(livestream_urls)
    logging.debug("livestream_urls: "+repr(livestream_urls))

    # Skip IDs that have already been done
    download_urls = []
    for livestream_url in livestream_urls:
        video_page_query = sqlalchemy.select([Media]).where(Media.media_url == livestream_url)
        video_page_rows = session.execute(video_page_query)
        video_page_row = video_page_rows.fetchone()
        if video_page_row:
            logging.debug("Skipping previously saved video: "+repr(video_page_row))
            continue
        download_urls.append(livestream_url)
        continue
    logging.debug("download_urls: "+repr(download_urls))

    # Download videos if there are any
    combined_video_dict = run_yt_dl_multiple(
        session = session,
        post_dict = post_dict,
        table_class = LivestreamVideo,
        download_urls = download_urls,
        post_id = post_id,
        )
    logging.debug("Finished downloading Tumblr embeds")
    return combined_video_dict



def handle_video_posts(session,post_dict):
    """Decide which video functions to run and pass back what they return"""
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
    # vimeo
    elif post_dict["video_type"] == u"vimeo":
        logging.debug("Post is vimeo video")
        return handle_vimeo_videos(session,post_dict)
    # "unknown" - special cases?
    elif (post_dict["video_type"] == u"unknown"):
        logging.warning("API reports video type as unknown, handlers may be inappropriate or absent.")
        if "imgur-embed" in repr(post_dict["player"]):
            logging.debug("Post is imgur video")
            return handle_imgur_videos(session,post_dict)
        elif "" in repr(post_dict["player"]):
            logging.debug("Post is livestream video")
            return handle_livestream_videos(session,post_dict)
    # If no handler is applicable, stop for fixing
    logging.error("Unknown video type!")
    logging.error("locals(): "+repr(locals()))
    assert(False)# Not implimented
    return {}


def debug():
    """For WIP, debug, ect function calls"""
    session = sql_functions.connect_to_db()

    # Youtube
    youtube_dict_1 = {u'reblog_key': u'HfjckfH7', u'short_url': u'http://tmblr.co/ZUGffq1cfuHuJ', u'thumbnail_width': 480, u'player': [{u'width': 250, u'embed_code': u'<iframe width="250" height="140" id="youtube_iframe" src="https://www.youtube.com/embed/lGIEmH3BoyA?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}, {u'width': 400, u'embed_code': u'<iframe width="400" height="225" id="youtube_iframe" src="https://www.youtube.com/embed/lGIEmH3BoyA?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}, {u'width': 500, u'embed_code': u'<iframe width="500" height="281" id="youtube_iframe" src="https://www.youtube.com/embed/lGIEmH3BoyA?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}], u'id': 110224285203L, u'post_url': u'http://askbuttonsmom.tumblr.com/post/110224285203/throwback-can-you-believe-its-been-almost-2yrs', u'tags': [u"button's mom", u'hardcopy', u'song', u'shadyvox'], u'highlighted': [], u'state': u'published', u'html5_capable': True, u'type': u'video', u'format': u'html', u'timestamp': 1423197599, u'note_count': 145, u'video_type': u'youtube', u'date': u'2015-02-06 04:39:59 GMT', u'thumbnail_height': 360, u'permalink_url': u'https://www.youtube.com/watch?v=lGIEmH3BoyA', u'slug': u'throwback-can-you-believe-its-been-almost-2yrs', u'blog_name': u'askbuttonsmom', u'caption': u'<p>Throwback! Can you believe it&#8217;s been almost 2yrs since this came out? Mommy&#8217;s getting old&#8230;</p>', u'thumbnail_url': u'https://i.ytimg.com/vi/lGIEmH3BoyA/hqdefault.jpg'}
    youtube_dict_2 = {u'highlighted': [], u'reblog_key': u'qO3JnfS7', u'player': [{u'width': 250, u'embed_code': False}, {u'width': 400, u'embed_code': False}, {u'width': 500, u'embed_code': False}], u'format': u'html', u'timestamp': 1390412461, u'note_count': 4282, u'tags': [], u'video_type': u'youtube', u'id': 74184911379L, u'post_url': u'http://askbuttonsmom.tumblr.com/post/74184911379/ask-thecrusaders-bar-buddies-dont-worry', u'caption': u'<p><a class="tumblr_blog" href="http://ask-thecrusaders.tumblr.com/post/74162414750/bar-buddies-dont-worry-neon-you-will-have-your">ask-thecrusaders</a>:</p>\n<blockquote>\n<p><strong>"Bar Buddies"</strong><br/><br/>Dont\u2019 worry Neon, you will have your music video soon enough.</p>\n</blockquote>\n<p>Honestly, that Neon Lights is a TERRIBLE influence!! No son of mine will grow up to be a drunken drug-shooting bass dropping hipster! :C</p>', u'state': u'published', u'html5_capable': False, u'reblog': {u'comment': u'<p>Honestly, that Neon Lights is a TERRIBLE influence!! No son of mine will grow up to be a drunken drug-shooting bass dropping hipster! :C</p>', u'tree_html': u'<p><a class="tumblr_blog" href="http://ask-thecrusaders.tumblr.com/post/74162414750/bar-buddies-dont-worry-neon-you-will-have-your">ask-thecrusaders</a>:</p><blockquote>\n<p><strong>"Bar Buddies"</strong><br/><br/>Dont\u2019 worry Neon, you will have your music video soon enough.</p>\n</blockquote>', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': 0, u'title_font': u'Helvetica Neue', u'link_color': u'#529ECC', u'header_image_focused': u'http://assets.tumblr.com/images/default_header/optica_pattern_04.png?_v=7c4e5e82cf797042596e2e64af1c383f', u'show_description': True, u'show_header_image': True, u'header_stretch': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://assets.tumblr.com/images/default_header/optica_pattern_04.png?_v=7c4e5e82cf797042596e2e64af1c383f', u'avatar_shape': u'circle', u'show_avatar': True, u'background_color': u'#F6F6F6', u'header_image': u'http://assets.tumblr.com/images/default_header/optica_pattern_04.png?_v=7c4e5e82cf797042596e2e64af1c383f'}, u'name': u'ask-thecrusaders'}, u'comment': u'<p><strong>"Bar Buddies"</strong><br><br>Dont\u2019 worry Neon, you will have your music video soon enough.</p>', u'post': {u'id': u'74162414750'}}]}, u'short_url': u'http://tmblr.co/ZUGffq155m_eJ', u'date': u'2014-01-22 17:41:01 GMT', u'type': u'video', u'slug': u'ask-thecrusaders-bar-buddies-dont-worry', u'blog_name': u'askbuttonsmom'}
    #youtube_result_1 = handle_video_posts(session,youtube_dict_1)
    #youtube_result_2 = handle_video_posts(session,youtube_dict_2)

    # Vimeo
    vimeo_dict_1 = {u'reblog_key': u'3BuzwM1q', u'reblog': {u'comment': u'', u'tree_html': u'<p><a href="http://robscorner.tumblr.com/post/110250942998/a-hyperfast-preview-video-for-the-kind-of-content" class="tumblr_blog">robscorner</a>:</p><blockquote><p>A hyperfast preview video for the kind of content I\u2019m featuring on Patreon (patreon.com/robaato)! Slower version will be available for my supporters!<br/>MUSIC: The End (T.E.I.N. Pt. 2) | 12th Planet<br/></p><p>Support for high-resolution art, PSDs, process videos, tutorials, character requests, and more!<br/></p></blockquote>', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'header_full_height': 1071, u'title_color': u'#FFFFFF', u'header_bounds': u'92,1581,978,3', u'title_font': u'Gibson', u'link_color': u'#529ECC', u'header_image_focused': u'http://static.tumblr.com/a5a733e78671519e8eb9cf3700ccfb70/ybimlef/1eon5zyi0/tumblr_static_tumblr_static_2df9bnxrqh1c4c8sgk8448s80_focused_v3.jpg', u'show_description': False, u'header_full_width': 1600, u'header_focus_width': 1578, u'header_stretch': True, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://static.tumblr.com/cfa3addece89b58093ea0a8a87082653/ybimlef/FWyn5zyhv/tumblr_static_2df9bnxrqh1c4c8sgk8448s80_2048_v2.png', u'avatar_shape': u'square', u'show_avatar': True, u'header_focus_height': 886, u'background_color': u'#337db1', u'header_image': u'http://static.tumblr.com/cfa3addece89b58093ea0a8a87082653/ybimlef/FWyn5zyhv/tumblr_static_2df9bnxrqh1c4c8sgk8448s80.png'}, u'name': u'robscorner'}, u'comment': u'<p>A hyperfast preview video for the kind of content I\u2019m featuring on Patreon (patreon.com/robaato)! Slower version will be available for my supporters!<br>MUSIC: The End (T.E.I.N. Pt. 2) | 12th Planet<br></p><p>Support for high-resolution art, PSDs, process videos, tutorials, character requests, and more!<br></p>', u'post': {u'id': u'110250942998'}}]}, u'thumbnail_width': 295, u'player': [{u'width': 250, u'embed_code': u'<iframe src="https://player.vimeo.com/video/118912193?title=0&byline=0&portrait=0" width="250" height="156" frameborder="0" title="Hyperfast Preview - Mai (Patreon Process Videos)" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>'}, {u'width': 400, u'embed_code': u'<iframe src="https://player.vimeo.com/video/118912193?title=0&byline=0&portrait=0" width="400" height="250" frameborder="0" title="Hyperfast Preview - Mai (Patreon Process Videos)" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>'}, {u'width': 500, u'embed_code': u'<iframe src="https://player.vimeo.com/video/118912193?title=0&byline=0&portrait=0" width="500" height="312" frameborder="0" title="Hyperfast Preview - Mai (Patreon Process Videos)" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>'}], u'id': 110255840681, u'post_url': u'http://nsfw.kevinsano.com/post/110255840681/robscorner-a-hyperfast-preview-video-for-the-kind', u'source_title': u'robscorner', u'tags': [u'reblog', u'erohua'], u'highlighted': [], u'state': u'published', u'short_url': u'http://tmblr.co/Zo9zBq1chmfsf', u'html5_capable': True, u'type': u'video', u'format': u'html', u'timestamp': 1423238010, u'note_count': 415, u'video_type': u'vimeo', u'source_url': u'http://robscorner.tumblr.com/post/110250942998/a-hyperfast-preview-video-for-the-kind-of-content', u'date': u'2015-02-06 15:53:30 GMT', u'thumbnail_height': 184, u'permalink_url': u'https://vimeo.com/118912193', u'slug': u'robscorner-a-hyperfast-preview-video-for-the-kind', u'blog_name': u'nsfwkevinsano', u'caption': u'<p><a href="http://robscorner.tumblr.com/post/110250942998/a-hyperfast-preview-video-for-the-kind-of-content" class="tumblr_blog">robscorner</a>:</p><blockquote><p>A hyperfast preview video for the kind of content I\u2019m featuring on Patreon (patreon.com/robaato)! Slower version will be available for my supporters!<br/>MUSIC: The End (T.E.I.N. Pt. 2) | 12th Planet<br/></p><p>Support for high-resolution art, PSDs, process videos, tutorials, character requests, and more!<br/></p></blockquote>', u'thumbnail_url': u'https://i.vimeocdn.com/video/506047324_295x166.jpg'}
    #vimeo_result_1 = handle_video_posts(session,vimeo_dict_1)

    # Imgur
    imgur_post_dict = {u'highlighted': [], u'reblog_key': u'qX0EtplN', u'player': [{u'width': 250, u'embed_code': u'<iframe class="imgur-embed" width="100%" height="720" frameborder="0" src="http://i.imgur.com/wSBlRyv.gifv#embed"></iframe>'}, {u'width': 400, u'embed_code': u'<iframe class="imgur-embed" width="100%" height="720" frameborder="0" src="http://i.imgur.com/wSBlRyv.gifv#embed"></iframe>'}, {u'width': 500, u'embed_code': u'<iframe class="imgur-embed" width="100%" height="720" frameborder="0" src="http://i.imgur.com/wSBlRyv.gifv#embed"></iframe>'}], u'format': u'html', u'timestamp': 1415466120, u'note_count': 109, u'tags': [], u'thumbnail_width': 0, u'id': 102102282191, u'post_url': u'http://jessicaanner.tumblr.com/post/102102282191/front-view-clothed-large-version-gif-back', u'caption': u'<p><em><strong><a href="http://jessicaanner.tumblr.com/post/101601852991/front-view-clothed-large-version-gif-back">Front View (Clothed)</a> <a href="http://i.imgur.com/fDixfAC.gifv"><span class="auto_link" title="">(Large version)</span></a><a href="http://d.facdn.net/art/benezia/1414952655.benezia_front_armored_optimized.gif"><span class="auto_link" title=""> (GIF)</span></a></strong></em><br/><em><strong><a href="http://jessicaanner.tumblr.com/post/101666148721/front-view-clothed-large-version-gif-back">Back View (Clothed)</a> <a href="http://i.imgur.com/QYfRNeQ.gifv" title="">(Large version)</a> <a href="http://d.facdn.net/art/benezia/1415012804.benezia_back_armored_optimized.gif">(GIF)</a></strong></em><br/><em><strong><a href="http://jessicaanner.tumblr.com/post/101768307896/front-view-clothed-large-version-gif-back">Front View (Nude)</a> <a href="http://i.imgur.com/0N7ir7o.gifv">(Large version)</a> <a href="http://d.facdn.net/art/benezia/1415120393.benezia_front_nude_optimized.gif" title="">(GIF)</a></strong></em><br/><em><strong><a href="http://jessicaanner.tumblr.com/post/101852253284/front-view-clothed-large-version-gif-back">Back View (Nude)</a> <a href="http://i.imgur.com/sP5h9ux.gifv" title="">(Large version)</a> <a href="http://d.facdn.net/art/benezia/1415120590.benezia_back_nude_optimized.gif" title="">(GIF)</a></strong></em><br/><strong><em><a href="http://jessicaanner.tumblr.com/post/101934955336/front-view-clothed-large-version-gif-back">Buttocks Closeup View</a> <a href="http://i.imgur.com/BXMYuxk.gifv" title="">(Large version)</a> <a href="http://i.imgur.com/3bhzRP2.gif">(GIF)</a></em></strong><br/><em><strong><a href="http://jessicaanner.tumblr.com/post/102102282191/front-view-clothed-large-version-gif-back">Crotch Closeup View</a> <a href="http://i.imgur.com/wSBlRyv.gifv">(Large version)</a> <a href="http://i.imgur.com/UiDU1XB.gif">(GIF)</a></strong></em><br/><em><strong><a href="http://jessicaanner.tumblr.com/post/102017653601/front-view-clothed-large-version-gif-back">Bust Closeup View</a> <a href="http://i.imgur.com/S5M6PID.gifv">(Large version)</a> <a href="http://i.imgur.com/BlMYohP.gif">(GIF)</a></strong></em></p>', u'state': u'published', u'html5_capable': False, u'video_type': u'unknown', u'short_url': u'http://tmblr.co/ZLO7Om1V5nI-F', u'date': u'2014-11-08 17:02:00 GMT', u'thumbnail_height': 0, u'thumbnail_url': u'', u'type': u'video', u'slug': u'front-view-clothed-large-version-gif-back', u'blog_name': u'jessicaanner'}
    imgur_result = handle_video_posts(session,imgur_post_dict)

    # Vine
    vine_dict = {u'reblog_key': u'A5DhHt28', u'reblog': {u'comment': u'<p>Have a nice weekend, Tumblr.&nbsp;</p>', u'tree_html': u'', u'trail': []}, u'placement_id': u'{"i":"mF4avY6GyshXjaQmfk0v","v":4,"t":1427193020,"c":{"p":"113540981790","b":"staff"},"d":{"v":{"e":"hjWIUFOYD31"}},"h":"3291f1aa07"}', u'thumbnail_width': 480, u'player': [{u'width': 250, u'embed_code': u'<iframe class="vine-embed" src="https://vine.co/v/hjWIUFOYD31/embed/simple"width="250" height="250" frameborder="0"></iframe><script async src="//platform.vine.co/static/scripts/embed.js" charset="utf-8"></script>'}, {u'width': 400, u'embed_code': u'<iframe class="vine-embed" src="https://vine.co/v/hjWIUFOYD31/embed/simple"width="400" height="400" frameborder="0"></iframe><script async src="//platform.vine.co/static/scripts/embed.js" charset="utf-8"></script>'}, {u'width': 500, u'embed_code': u'<iframe class="vine-embed" src="https://vine.co/v/hjWIUFOYD31/embed/simple"width="500" height="500" frameborder="0"></iframe><script async src="//platform.vine.co/static/scripts/embed.js" charset="utf-8"></script>'}], u'id': 113540981790L, u'post_url': u'http://staff.tumblr.com/post/113540981790/have-a-nice-weekend-tumblr', u'source_title': u'weloveshortvideos.com', u'tags': [], u'highlighted': [], u'state': u'published', u'short_url': u'http://tmblr.co/ZE5Fby1flaUGU', u'html5_capable': True, u'type': u'video', u'format': u'html', u'timestamp': 1426282797, u'note_count': 48309, u'video_type': u'vine', u'source_url': u'http://weloveshortvideos.com', u'date': u'2015-03-13 21:39:57 GMT', u'thumbnail_height': 480, u'permalink_url': u'https://vine.co/v/hjWIUFOYD31', u'slug': u'have-a-nice-weekend-tumblr', u'blog_name': u'staff', u'caption': u'<p>Have a nice weekend, Tumblr.\xa0</p>', u'thumbnail_url': u'http://v.cdn.vine.co/r/thumbs/FE4C8DC8781008139866036658176_1c16044fdd3.3.4.mp4_l_pAXVyCckNVnk2OzdadqNB_6bq4mYoBHpBFRIF8Hi3OdOW1vmjP1TR075G1ZegT.jpg?versionId=abawWSw4Y_QFv2TKPWz6j8N5y7.6LOGq'}
    vine_restult = handle_video_posts(session,vine_dict)

    # Tumblr
    tumblr_video_post_dict = {u'reblog_key': u'3bqfxHgy', u'short_url': u'http://tmblr.co/Z_sLQw1eYTSqS', u'thumbnail_width': 480, u'player': [{u'width': 250, u'embed_code': u'<iframe width="250" height="140" id="youtube_iframe" src="https://www.youtube.com/embed/tT5pifkZzEk?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}, {u'width': 400, u'embed_code': u'<iframe width="400" height="225" id="youtube_iframe" src="https://www.youtube.com/embed/tT5pifkZzEk?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}, {u'width': 500, u'embed_code': u'<iframe width="500" height="281" id="youtube_iframe" src="https://www.youtube.com/embed/tT5pifkZzEk?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}], u'id': 112247295260L, u'post_url': u'http://tsitra360.tumblr.com/post/112247295260/my-latest-art-timelapse-is-up-see-how-i-drew', u'tags': [], u'highlighted': [], u'state': u'published', u'html5_capable': True, u'type': u'video', u'format': u'html', u'timestamp': 1425068852, u'note_count': 79, u'video_type': u'youtube', u'date': u'2015-02-27 20:27:32 GMT', u'thumbnail_height': 360, u'permalink_url': u'https://www.youtube.com/watch?v=tT5pifkZzEk', u'slug': u'my-latest-art-timelapse-is-up-see-how-i-drew', u'blog_name': u'tsitra360', u'caption': u'<p>My latest art timelapse is up! See how I drew Berry Swirl on my youtube channel.</p>', u'thumbnail_url': u'https://i.ytimg.com/vi/tT5pifkZzEk/hqdefault.jpg'}
    tumblr_Result = handle_video_posts(session,tumblr_video_post_dict)

    return


def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","video-handlers-log.txt"))
        debug()
    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return


if __name__ == '__main__':
    main()
