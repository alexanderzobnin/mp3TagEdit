"""
ID3v2.3 frame types description.
"""

# Frame types dictionary.
# Format: 'Frame ID': 'Frame type'. Ex. {'TALB': 'TextInfo'}
FrameTypes = {'UFID': 'UFID',
              'TALB': 'TextInfo',
              'TBPM': 'TextInfo',
              'TCOM': 'TextInfo',
              'TCON': 'TextInfo',
              'TCOP': 'TextInfo',
              'TENC': 'TextInfo',
              'TIT1': 'TextInfo',
              'TIT2': 'TextInfo',
              'TIT3': 'TextInfo',
              'TPE1': 'TextInfo',
              'TPE2': 'TextInfo',
              'TPE3': 'TextInfo',
              'TPE4': 'TextInfo',
              'TRCK': 'TextInfo',
              'TYER': 'TextInfo',
              'COMM': 'Comments'}


class ID3V2Frame:
    """
    Base ID3v2 frame object.
    """

    def __init__(self, frame_header, frame_body):
        self.header = frame_header
        self.size = self.header.framesize + 10
        self.raw_body = frame_body
        #self.body = decode_frame_body(frame_body)

    def print(self):
        """
        Print frame information.
        """
        self.header.print()
        print('Frame raw body:', self.raw_body)
        print()


class FrameTextInfo(ID3V2Frame):
    """
    Text info frame.
    """

    def __init__(self, frame_header, frame_body):
        super().__init__(frame_header, frame_body)
        self.body = decode_frame_body(frame_body)

    def print(self):
        self.header.print()
        print('Frame text:', self.body)
        print()


class FrameComments(ID3V2Frame):
    """
    Comments frame.
    """
    def __init__(self, frame_header, frame_body):
        super().__init__(frame_header, frame_body)
        self.language = frame_body[1:4].decode()
        self.content_descr = decode_comments(frame_body[0], frame_body[4:])[0]
        self.text = decode_comments(frame_body[0], frame_body[4:])[1]

    def print(self):
        self.header.print()
        print('language:', self.language)
        print('content_descr:', self.content_descr)
        print('text:', self.text)
        print()


def decode_comments(encoding_byte, bytestring):
    """
    Decode comments and return Short content description
    and actual text fields.
    :type bytestring: bytes
    :param encoding_byte:
    :param bytestring:
    """
    # Detect encoding
    if encoding_byte == 0:
        # Use ISO-8859-1
        text_len = bytestring.find(b'\x00')
        content_descr = bytestring[:text_len].decode('iso8859_1')
        text = bytestring[text_len+1:].decode('iso8859_1')
        return content_descr, text
    elif encoding_byte == 1:
        # Use Unicode
        text_len = bytestring.find(b'\x00\x00')
        content_descr = bytestring[:text_len].decode('utf_16')
        text = bytestring[text_len+2:].decode('utf_16')
        return content_descr, text
    else:
        # Unknown encoding
        return None


def decode_full_text_string(encoding_byte, bytestring):
    """
    Decode full text string according to encoding.
    :type bytestring: bytes
    :param encoding_byte:
    :param bytestring:
    """
    # Detect encoding
    if encoding_byte == 0:
        # Use ISO-8859-1
        text_string = bytestring.decode('iso8859_1')
    elif encoding_byte == 1:
        # Use Unicode
        text_string = bytestring.decode('utf_16')
    else:
        # Unknown encoding
        text_string = bytestring.decode()
    return text_string


def decode_frame_body(bytestring):
    """
    Decode frame body.

    :param bytestring:
    :return: String contained frame body.
    """
    # Read first byte in frame and detect encoding
    encoding_byte = bytestring[0]
    if encoding_byte == 0:
        # Use ISO-8859-1
        frame_body = bytestring[1:].decode('iso8859_1')
    elif encoding_byte == 1:
        # Use Unicode
        frame_body = bytestring[1:].decode('utf_16')
    else:
        frame_body = bytestring.decode()
    return frame_body


class ID3V2FrameHeader:
    """
    ID3v2 Frame Header. Length - 10 bytes.
    """
    def __init__(self, byteheader):
        self.frameid = byteheader[:4].decode()
        self.flags = byteheader[8:10]

        size = 0
        framesizebytes = byteheader[4:8]
        for i in range(0, 4):
            sizebyte = int(framesizebytes[i]) * (256**(3-i))
            size += sizebyte
        self.framesize = size

    def print(self):
        print('Frame ID:', self.frameid)
        print('Frame Size: {0} bytes'.format(self.framesize))

        # Print only seated flags.
        if self.flags != b'\x00\x00':
            flags = ''
            for flagbyte in self.flags:
                flags += '{0:08b} '.format(flagbyte)
            print('Frame flags:', flags)