from xml.sax.saxutils import escape


# TODO Check if we can export 0xD800
# Otherwise we also need to use valid_xml_char_ordinal)

def get_valid_xml_string(string):
    if string:
        return escape(string)
    return ''


def format_date(date):
    if date:
        return date.strftime('%d-%m-%Y')
    else:
        return None
