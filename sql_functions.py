#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     04/03/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------


def generate_insert_query(table_name,value_names):
    """Generate a SQL insert statement so all the statements can be made in one place
    NEVER LET THIS TOUCH OUTSIDE DATA!
    'INSERT INTO <TABLE_NAME> (<VALUE_NAME_1>, <VALUE_NAME_2>,...) %s, %s, ...);'
    """
    assert len(value_names) > 0
    value_names_with_backticks = []
    for value in value_names:
        assert(type(value) is type(""))
        value_names_with_backticks.append("`"+value+"`")
    query = (
    "INSERT INTO `"+table_name+"` (%s) VALUES (" % (", ".join(value_names_with_backticks),)# Values from dict
    +"%s, "*(len(value_names_with_backticks)-1)#values to insert
    +"%s);"
    )
    #logging.debug(repr(query))
    return query


def add_post_to_db(connection,post_dict,info_dict):
    row_to_insert = { # TODO, Waiting on ATC for DB design
    "FIELD_NAME":post_dict["body"],
    "FIELD_NAME":post_dict["highlighted"],
    "FIELD_NAME":post_dict["reblog_key"],
    "FIELD_NAME":post_dict["format"],
    "FIELD_NAME":post_dict["timestamp"],
    "FIELD_NAME":post_dict["note_count"],
    "FIELD_NAME":post_dict["tags"],
    "FIELD_NAME":post_dict["id"],
    "FIELD_NAME":post_dict["post_url"],
    "FIELD_NAME":post_dict["state"],
    "FIELD_NAME":post_dict["reblog"],
    "FIELD_NAME":post_dict["short_url"],
    "FIELD_NAME":post_dict["date"],
    "FIELD_NAME":post_dict["title"],
    "FIELD_NAME":post_dict["type"],
    "FIELD_NAME":post_dict["slug"],
    "FIELD_NAME":post_dict["blog_name"],
    "FIELD_NAME":post_dict[""],
    "FIELD_NAME":post_dict[""],
    "FIELD_NAME":post_dict[""],
    "FIELD_NAME":info_dict["response"][""],

    }
    fields = row_to_insert.keys()
    values = row_to_insert.values()
    query = generate_insert_query(table_name="story_metadata",value_names=fields)
    logging.debug(repr(query))
    result = cursor.execute(query, values)
    cursor.close()
    return




def add_image_to_db(connection,image_filename):
    pass










def main():
    pass

if __name__ == '__main__':
    main()
