#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     17/03/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
import subprocess# For video downloads


from utils import *
from media_handlers import generate_media_file_path_timestamp, generate_media_file_path_hash, hash_file_data, move_file
import config


Base = declarative_base()


class Media(Base):
    __tablename__ = "media"
    # Columns
    # Locally generated
    primary_key = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    date_Added = sqlalchemy.Column(sqlalchemy.Integer)
    media_url = sqlalchemy.Column(sqlalchemy.String())
    sha512base64_hash = sqlalchemy.Column(sqlalchemy.String(250))
    filename = sqlalchemy.Column(sqlalchemy.String(250))
    extractor_used = sqlalchemy.Column(sqlalchemy.String(250))
    # Youtube
    youtube_yt_dl_info_json = sqlalchemy.Column(sqlalchemy.String())
    youtube_video_id = sqlalchemy.Column(sqlalchemy.String(250))
    # Tubmlr video
    tumblrvideo_yt_dl_info_json = sqlalchemy.Column(sqlalchemy.String())
    # Tumblr audio
    tumblraudio_album_art = sqlalchemy.Column(sqlalchemy.String())
    tumblraudio_artist = sqlalchemy.Column(sqlalchemy.String())
    # SoundCloud audio embeds
    soundcloud_id = sqlalchemy.Column(sqlalchemy.String())





def handle_soundcloud_audio(session,post_dict):
    """Save soundcloud audio ect from a post
    Use youtube-dl to save audio
    https://github.com/rg3/youtube-dl/blob/master/docs/supportedsites.md
    https://github.com/rg3/youtube-dl/"""
    # Send album art image link off to be checked
    logging.debug("post_dict: "+repr(post_dict))
    post_id = str(post_dict["id"])
    # Grab "track id"?
    # u'https://api.soundcloud.com/tracks/192213990/stream?client_id=3cQaPshpEeLqMsNFAUw1Q' to '192213990'
    soundcloud_link = post_dict["audio_url"]
    track_id = re.search("""api\.soundcloud\.com/tracks/(\d+)/stream""", soundcloud_link, re.IGNORECASE|re.DOTALL).group(1)
    soundcloud_id = track_id

    # Check if audio has been saved, and return if it has
    #preexisting_filepath  = sql_functions.check_if_audio_in_db(connection,soundcloud_id=None)#TODO FIXME

    media_url_query = sqlalchemy.select([Media]).where(Media.soundcloud_id == soundcloud_id)
    rows = session.execute(media_url_query)
    row = rows.fetchone()
    logging.debug("row"+repr(row))

    if row is not None:
        previous_media_url = row["media_url"]
        logging.debug("previous_media_url: "+repr(previous_media_url))
        return previous_media_url

    # Grab url to send to youtube-dl
    soundcloud_url = post_dict["audio_url"]
    logging.debug("soundcloud_url: "+repr(soundcloud_url))
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
    command = [program_path, ignore_errors, safe_filenames, info_json_arg, description_arg, output_arg, output_template, soundcloud_url]
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
    logging.warning("CODE SC AUDIO DB STUFF")# TODO FIXME



    #preexisting_filepath = sql_functions.check_if_audio_in_db(connection,sha512base64_hash=sha512base64_hash)



    find_path = sqlalchemy.select([Media.filename]).where(Media.sha512base64_hash == sha512base64_hash)
    rs = session.execute(find_path)
    one = rs.fetchone()
    logging.debug("one"+repr(one))
    if one is not None:
        preexisting_filepath = one[0]
    else:
        preexisting_filepath = None




    if preexisting_filepath is not None:
        # Delete temp file if media is already saved
        logging.info("Deleting duplicate video file")
        os.remove(media_temp_filepath)
        os.remove(expected_info_path)
        final_media_filepath = preexisting_filepath
    else:
        # Move file to media DL location
        logging.info("Moving video to final location")
        # Generate output filepath
        file_ext = media_temp_filename.split(".")[-1]
        filename = str(time_of_retreival)+"."+file_ext
        final_media_filepath = generate_media_file_path_timestamp(root_path=config.root_path,filename=filename)
        # Move file to final location
        move_file(media_temp_filepath,final_media_filepath)
    logging.debug("final_media_filepath: "+repr(final_media_filepath))
    assert(os.path.exists(final_media_filepath))
    # Add video to DB
    logging.warning("CODE SC AUDIO DB STUFF")# TODO FIXME


    new_media_row = Media(
    media_url=soundcloud_link,
    sha512base64_hash=sha512base64_hash,
    filename=final_media_filepath,
    date_Added=time_of_retreival,
    extractor_used="soundcloud_audio_embed",
    youtube_yt_dl_info_json=info_json,
    soundcloud_id = soundcloud_id
    )
    session.add(new_media_row)




##    sql_functions.add_media_to_db(
##    connection,
##    media_url=soundcloud_link,
##    sha512base64_hash=sha512base64_hash,
##    media_filename=final_media_filepath,
##    time_of_retreival=time_of_retreival,
##    extractor_used="soundcloud_audio_embed",
##    youtube_yt_dl_info_json=info_json)
##    logging.debug("Finished downloading soundcloud embed")
    return {"soundcloud_audio_embed":sha512base64_hash}
















def main():
    setup_logging(log_file_path=os.path.join("debug","sql_alchemy-log.txt"))

if __name__ == '__main__':
    main()




engine = sqlalchemy.create_engine('sqlite:///sqlalchemy_example.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine
Base.metadata.create_all(engine)

DBSession = sqlalchemy.orm.sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Insert a Person in the person table
new_media_row = Media()
new_media_row.media_url = "Http://examp"
session.add(new_media_row)
session.commit()

soundcloud_post_dict = {u'reblog_key': u'S6VWj0Cb', u'reblog': {u'comment': u'', u'tree_html': u'<p><a class="tumblr_blog" href="http://waltzforluma.tumblr.com/post/111622677961/or-your-computer-could-overheat-while-youre">waltzforluma</a>:</p><blockquote><p>Or, your computer could overheat while you\u2019re listening to \u201cDeath Rag\u201d from Future Vision, and burst into flames!</p></blockquote>', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'regular', u'header_full_height': 262, u'title_color': u'#444444', u'header_bounds': u'0,623,262,157', u'background_color': u'#FAFAFA', u'link_color': u'#529ECC', u'header_image_focused': u'http://static.tumblr.com/a50dd34705b42b1479c2535a15461b00/oevxq7m/ZrTn5ivly/tumblr_static_tumblr_static_57wsbbc6rz0g0gk4ww8k884wk_focused_v3.png', u'show_description': True, u'header_full_width': 898, u'avatar_shape': u'circle', u'header_focus_width': 466, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'header_image_scaled': u'http://static.tumblr.com/a50dd34705b42b1479c2535a15461b00/oevxq7m/g9cn5ivlx/tumblr_static_57wsbbc6rz0g0gk4ww8k884wk_2048_v2.png', u'show_avatar': True, u'header_focus_height': 262, u'title_font': u'Garamond Classic FS', u'header_image': u'http://static.tumblr.com/a50dd34705b42b1479c2535a15461b00/oevxq7m/g9cn5ivlx/tumblr_static_57wsbbc6rz0g0gk4ww8k884wk.png'}, u'name': u'waltzforluma'}, u'comment': u'<p>Or, your computer could overheat while you\u2019re listening to \u201cDeath Rag\u201d from Future Vision, and burst into flames!</p>', u'post': {u'id': u'111622677961'}}]}, u'player': u'<iframe src="https://w.soundcloud.com/player/?url=https%3A%2F%2Fapi.soundcloud.com%2Ftracks%2F192213990&amp;visual=true&amp;liking=false&amp;sharing=false&amp;auto_play=false&amp;show_comments=false&amp;continuous_play=false&amp;origin=tumblr" frameborder="0" allowtransparency="true" class="soundcloud_audio_player" width="500" height="500"></iframe>', u'id': 113020390888L, u'post_url': u'http://doscoon.tumblr.com/post/113020390888/waltzforluma-or-your-computer-could-overheat', u'source_title': u'waltzforluma', u'format': u'html', u'highlighted': [], u'state': u'published', u'track_name': u'Steven Universe - Death Rag', u'short_url': u'http://tmblr.co/ZlYOqv1fGYate', u'type': u'audio', u'tags': [], u'timestamp': 1425776404, u'note_count': 1014, u'source_url': u'http://waltzforluma.tumblr.com/post/111622677961/or-your-computer-could-overheat-while-youre', u'date': u'2015-03-08 01:00:04 GMT', u'plays': 38933, u'slug': u'waltzforluma-or-your-computer-could-overheat', u'album_art': u'http://38.media.tumblr.com/tumblr_nk3re1A1Cf1qzqb72_1424489834_cover.jpg', u'blog_name': u'doscoon', u'is_external': True, u'audio_url': u'https://api.soundcloud.com/tracks/192213990/stream?client_id=3cQaPshpEeLqMsNFAUw1Q', u'caption': u'<p><a class="tumblr_blog" href="http://waltzforluma.tumblr.com/post/111622677961/or-your-computer-could-overheat-while-youre">waltzforluma</a>:</p><blockquote><p>Or, your computer could overheat while you\u2019re listening to \u201cDeath Rag\u201d from Future Vision, and burst into flames!</p></blockquote>', u'audio_type': u'soundcloud', u'audio_source_url': u'https://soundcloud.com/aivisura/steven-universe-death-rag', u'embed': u'<iframe src="https://w.soundcloud.com/player/?url=https%3A%2F%2Fapi.soundcloud.com%2Ftracks%2F192213990&amp;visual=true&amp;liking=false&amp;sharing=false&amp;auto_play=false&amp;show_comments=false&amp;continuous_play=false&amp;origin=tumblr" frameborder="0" allowtransparency="true" class="soundcloud_audio_player" width="500" height="500"></iframe>'}
handle_soundcloud_audio(session,soundcloud_post_dict)
session.commit()