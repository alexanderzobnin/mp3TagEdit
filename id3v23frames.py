"""
ID3v2.3 frame types description.
"""


class ID3V2Frame:
    """
    Base ID3v2 frame object.
    """

    def __init__(self, frame_header, frame_body):
        """

        :type frame_header: ID3V2FrameHeader
        """
        self.header = frame_header
        self.id = self.header.frameid
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


class ID3V2FrameHeader:
    """
    ID3v2 Frame Header. Length - 10 bytes.
    """

    def __init__(self, byteheader):
        """

        :type byteheader: bytes
        """
        self.raw_data = byteheader
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


class FrameTextInfo(ID3V2Frame):
    """
    Text info frame.
    """

    def __init__(self, frame_header, frame_body):
        super().__init__(frame_header, frame_body)
        self.text = FrameTextInfo.decode_text_info(frame_body)

    def __str__(self):
        return self.text
        #return FrameTextInfo.decode_text_info(self.raw_body)

    def set_value(self, value, encoding='utf_16'):
        # Set text value
        self.text = value

        # New raw frame body
        new_raw_body = self.encode_text_info(value, encoding)
        self.raw_body = new_raw_body

        # Calculate new frame size
        new_framesize = len(new_raw_body)
        self.size = new_framesize + 10

        # Write new size into frame header
        framesizebytes = new_framesize.to_bytes(4, 'big')
        new_raw_header = self.header.raw_data[:4] + framesizebytes + self.header.raw_data[8:10]
        new_frame_header = ID3V2FrameHeader(new_raw_header)
        self.header = new_frame_header

    def print(self):
        self.header.print()
        print('Frame text:', self.text)
        print()

    @staticmethod
    def decode_text_info(bytestring):
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

    @staticmethod
    def encode_text_info(text, encoding='utf_16'):
        """
        Encode text to frame body.

        :type text: str
        :param text:
        :param encoding:
        :rtype: bytes
        :return: byte string with encoded text
        """
        if encoding == 'iso8859_1':
            bytestring = b'\x00' + text.encode('iso8859_1')
            return bytestring
        if encoding == 'utf_16':
            bytestring = b'\x01' + text.encode('utf_16')
            return bytestring


class FrameComments(ID3V2Frame):
    """
    Comments frame.
    """

    def __init__(self, frame_header, frame_body):
        super().__init__(frame_header, frame_body)
        self.language = frame_body[1:4].decode()
        self.content_descr = FrameComments.decode_comments(frame_body[0], frame_body[4:])[0]
        self.text = FrameComments.decode_comments(frame_body[0], frame_body[4:])[1]

    def __str__(self):
        return self.text

    def print(self):
        self.header.print()
        print('language:', self.language)
        print('content_descr:', self.content_descr)
        print('text:', self.text)
        print()

    @staticmethod
    def decode_comments(encoding_byte, bytestring):
        """
        Decode comments and return 'short content description' and 'actual text' fields.

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