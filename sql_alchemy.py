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


import config


Base = declarative_base()


class media(Base):
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



def main():
    pass

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
new_media_row = media(date_Added=1,filename="foo.txt")
session.add(new_media_row)
session.commit()