"""
Module for read ID3v2.3 tag.

ID3v2.3 tag structure:

|Tag header (10 bytes)                   |Frames                        |
|file id|version|flags      |size        |                              |
-------------------------------------------------------------------------
|ID3    03 00   %abc00000   4 * %0xxxxxxx|ID3 frame 1|ID3 frame 2|......|
-------------------------------------------------------------------------

ID3 frame:

|Frame header (10 bytes)            |Frame body |
|Frame ID     |Size         |Flags  |           |
-------------------------------------------------
|$xx xx xx xx |$xx xx xx xx |$xx xx |Frame body |
-------------------------------------------------

"""
from abc import abstractmethod


class ID3V2Tag:
    """
    ID3v2 tag.
    """

    def __init__(self, frames,
                 tagsize=2048,
                 unsynchronisation=False,
                 extended_header=False,
                 experimental_indicator=False):
        """


        :type frames: dict
        :param tagsize:
        :param unsynchronisation:
        :param extended_header:
        :param experimental_indicator:
        :param frames:
        """
        self.id = 'ID3'
        self.version = b'\x03\x00'
        self.tagsize = tagsize
        self.unsynchronisation = unsynchronisation
        self.extended_header = extended_header
        self.experimental_indicator = experimental_indicator
        self.frames = frames

    def __getitem__(self, item):
        """

        :rtype : ID3V2Frame
        """
        return self.frames[item]

    def __str__(self):
        repr_string = ('-' * 30 + '\n\tTag header:\n' + '-' * 30 + '\n')
        repr_string += 'ID3v2/file Identifier: ' + self.id + '\n'
        repr_string += 'ID3v2 Version: {0}.{1}'.format(self.version[0], self.version[1]) + '\n'
        repr_string += 'ID3v2 size: {0} bytes'.format(self.tagsize) + '\n'
        repr_string += 'ID3v2 Unsynchronisation: ' + self.unsynchronisation.__str__() + '\n'
        repr_string += 'ID3v2 Extended header: ' + self.extended_header.__str__() + '\n'
        repr_string += 'ID3v2 Experimental indicator: ' + self.experimental_indicator.__str__() + '\n'
        repr_string += ('-' * 30 + '\n\tFrames:\n' + '-' * 30 + '\n')
        for fr in self.frames.values():
            repr_string += fr.__repr__() + '\n'
        return repr_string

    """
    def refresh(self):
        new_size = 0
        for fr in self.frames.values():
            new_size += fr.size
        self.tagsize = new_size

        # Do refresh tag header raw_data
        new_raw_header = self.header.raw_data[:6] + ID3V2TagHeader.set_tag_size(new_size)
        self.header.raw_data = new_raw_header
    """

    @staticmethod
    def decode_tagsize(sizebytes):
        """
        Convert ID3v2 tag size to bytes.

        The ID3v2 tag size is encoded with four bytes where the most significant bit (bit 7) is set to zero
        in every byte, making a total of 28 bits. The zeroed bits are ignored, so a 257 bytes long tag is
        represented as $00 00 02 01.

        The ID3v2 tag size is the size of the complete tag after unsynchronisation, including padding,
        excluding the header but not excluding the extended header (total tag size - 10).
        Only 28 bits (representing up to 256MB) are used in the size description to avoid the
        introduction of 'false syncsignals'.

        :rtype : int
        :param sizebytes:
        :return:
        """

        size = 0
        for i in range(0, 4):
            sizebyte = int(sizebytes[i]) * (256**(3-i))
            size += sizebyte >> (3-i)
        return size

    @staticmethod
    def encode_tagsize(size):
        """
        Encode tag size and make a bytes string for use in tag header's size field.

        Tag size: 0xxxxxxx 0xxxxxxx 0xxxxxxx 0xxxxxxx
        To encode teg size take a 'size' variable and do this:

        :rtype : bytes
        """
        sizebytes = []
        for i in range(0, 4):
            size_byte = (size >> 7*(3-i)) & 0x7F
            sizebytes.append(size_byte)
        return bytes(sizebytes)

    @staticmethod
    def read(bytestring):
        """
        Read ID3v2 tag from bytestring into ID3V2Tag object.

        :type bytestring: bytes
        :param bytestring:
        :return: ID3V2Tag object
        :rtype: ID3V2Tag
        """

        id3_tag = ID3V2Tag({})

        # Read tag header (first 10 bytes).
        tag_header = bytestring[:10]

        # Read and verify tag ID
        tag_id = tag_header[:3].decode()
        if tag_id != 'ID3':
            #! raise exception NOT_ID3_TAG
            return None

        # Read and verify version
        major_version = tag_header[3]
        if major_version != 3:
            #! raise exception UNSUPPORTED_VERSION
            return None
        else:
            id3_tag.version = tag_header[3:5]

        """
        Read flags (byte #6, after version bytes).
        Flag structure: %abc00000 where:
            a - Unsynchronisation
            b - Extended header
            c - Experimental indicator
        """
        id3_tag.unsynchronisation = bool(tag_header[5] & 0x80 != 0)
        id3_tag.extended_header = bool(tag_header[5] & 0x40 != 0)
        id3_tag.experimental_indicator = bool(tag_header[5] & 0x20 != 0)

        #id3_tag.tagsize = ID3V2TagHeader.get_tag_size(tag_header[6:])
        id3_tag.tagsize = ID3V2Tag.decode_tagsize(tag_header[6:])

        # Tag contains raw ID3 tag data
        tag = bytestring[:id3_tag.tagsize + 10]

        # Start read from tag body, don't read tag header
        read_position = 10

        frames = {}

        # Read, until tag end (using tagsize).
        while read_position < id3_tag.tagsize + 10:
            #fr = read_frame(tag, read_position)
            bytesframe = tag[read_position:]
            fr = ID3V2Frame.read(bytesframe)
            if fr:
                frames[fr.id] = fr

                # Calculate next frame position
                read_position += fr.size + 10

            # If frame object fr is empty stop reading
            else:
                break

        id3_tag.frames = frames
        return id3_tag


class ID3V2Frame:
    """
    Base ID3v2 frame object.
    """

    def __init__(self, frame_id='WNUL', frame_body=b'\x20', flags=b'\x00\x00'):
        self.id = frame_id
        self.flags = flags
        self.data = frame_body

        # Total size of frame
        self.size = len(frame_body)

    def __str__(self):
        repr_string = 'Frame ID: ' + self.id + '\n'
        repr_string += 'Frame Size: {0} bytes'.format(self.size)
        return repr_string

    def __repr__(self):
        repr_string = 'Frame ID: ' + self.id + '\n'
        repr_string += 'Frame Size: {0} bytes'.format(self.size)
        if self.flags != b'\x00\x00':
            flags = ''
            for flagbyte in self.flags:
                flags += '{0:08b} '.format(flagbyte)
            repr_string += 'Frame flags: ' + flags + '\n'
        return repr_string

    @staticmethod
    def read(bytestring):
        """

        """

        # Read ID3v2 frame header (first 10 bytes).
        frame_header = ID3V2FrameHeader.read(bytestring)

        # Detect frame type:
        if frame_header.frameid[0] == 'T':
            # Text information frame
            frame = FrameTextInfo.read(bytestring)

        elif frame_header.frameid == 'COMM':
            # Comments frame
            frame = FrameComments.read(bytestring)

        else:
            #frame = ID3V2Frame(frame_header, frame_body)
            frame = None

        return frame

    @abstractmethod
    def set_value(self, value):
        pass


class ID3V2FrameHeader:
    """
    ID3v2 Frame Header. Length - 10 bytes.
    """

    def __init__(self, frame_id='WNUL', frame_size=1, flags=b'\x00\x00'):
        """

        """
        self.frameid = frame_id
        self.framesize = frame_size
        self.flags = flags

    def __repr__(self):
        repr_string = 'Frame ID: ' + self.frameid + '\n'
        repr_string += 'Frame Size: {0} bytes'.format(self.framesize)
        if self.flags != b'\x00\x00':
            flags = ''
            for flagbyte in self.flags:
                flags += '{0:08b} '.format(flagbyte)
            repr_string += 'Frame flags: ' + flags + '\n'
        return repr_string

    @staticmethod
    def read(bytestring):
        """

        """

        frame_header = ID3V2FrameHeader()
        byteheader = bytestring[:10]
        if len(byteheader) == 10:
            frame_header.frameid = byteheader[:4].decode()
            frame_header.flags = byteheader[8:10]

            size = 0
            framesizebytes = byteheader[4:8]
            for i in range(0, 4):
                sizebyte = int(framesizebytes[i]) * (256**(3-i))
                size += sizebyte
            frame_header.framesize = size

        else:
            return None

        return frame_header


class FrameTextInfo(ID3V2Frame):
    """
    Text info frame.
    """

    def __init__(self, frame_id='WTXT', text='', encoding='unicode', flags=b'\x00\x00'):
        super().__init__(frame_id=frame_id, flags=flags)
        self.text = text
        self.encoding = encoding

    def __str__(self):
        return self.text

    def __repr__(self):
        repr_string = 'Frame ID: ' + self.id + '\n'
        repr_string += 'Frame Size: {0} bytes\n'.format(self.size)
        if self.flags != b'\x00\x00':
            flags = ''
            for flagbyte in self.flags:
                flags += '{0:08b} '.format(flagbyte)
            repr_string += 'Frame flags: ' + flags + '\n'
        repr_string += 'Frame text: ' + self.text + '\n'
        return repr_string

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

    @staticmethod
    def read(bytestring):
        """


        :rtype : FrameTextInfo
        :param bytestring:
        :return:
        """
        frame = FrameTextInfo()

        # Read frame header
        frame_header = ID3V2FrameHeader.read(bytestring)
        frame.id = frame_header.frameid
        frame.flags = frame_header.flags
        frame.size = frame_header.framesize

        # Read first byte in frame body and detect encoding
        frame_body = bytestring[10:10 + frame.size]
        encoding_byte = frame_body[0]
        if encoding_byte == 0:
            # Use ISO-8859-1
            frame.text = frame_body[1:].decode('iso8859_1')
            frame.encoding = 'iso8859_1'
        elif encoding_byte == 1:
            # Use Unicode
            frame.text = frame_body[1:].decode('utf_16')
            frame.encoding = 'unicode'
        else:
            frame.text = frame_body.decode()
        return frame

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

    def __init__(self, frame_id='WTXT', text='', language='', content_descr='', flags=b'\x00\x00'):
        super().__init__(frame_id=frame_id, flags=flags)
        self.text = text
        self.language = language
        self.content_descr = content_descr

    def __str__(self):
        return self.text

    def __repr__(self):
        repr_string = 'Frame ID: ' + self.id + '\n'
        repr_string += 'Frame Size: {0} bytes\n'.format(self.size)
        if self.flags != b'\x00\x00':
            flags = ''
            for flagbyte in self.flags:
                flags += '{0:08b} '.format(flagbyte)
            repr_string += 'Frame flags: ' + flags + '\n'
        repr_string += 'language: ' + self.language + '\n'
        repr_string += 'content_descr: ' + self.content_descr + '\n'
        repr_string += 'text: ' + self.text + '\n'
        return repr_string

    def set_value(self, value):
        pass

    @staticmethod
    def read(bytestring):
        """


        :rtype : FrameTextInfo
        :param bytestring:
        :return:
        """
        frame = FrameComments()

        # Read frame header
        frame_header = ID3V2FrameHeader.read(bytestring)
        frame.id = frame_header.frameid
        frame.flags = frame_header.flags
        frame.size = frame_header.framesize

        # Detect encoding
        frame_body = bytestring[10:frame.size + 10]
        encoding_byte = frame_body[0]
        if encoding_byte == 0:
            # Use ISO-8859-1
            text_len = frame_body.find(b'\x00')
            frame.content_descr = frame_body[:text_len].decode('iso8859_1')
            frame.text = frame_body[text_len+1:].decode('iso8859_1')

        elif encoding_byte == 1:
            # Use Unicode
            text_len = frame_body.find(b'\x00\x00')
            frame.content_descr = frame_body[:text_len].decode('utf_16')
            frame.text = frame_body[text_len+2:].decode('utf_16')

        else:
            # Unknown encoding
            return None

        return frame

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


def read_frame(bytestring, position=0):
    """
    Read ID3v2 frame into ID3V2Frame object.

    :type bytestring: bytes
    :param bytestring: bytestring contains raw ID3 tag data.
    :param position:
    :return:
    """
    # Read ID3v2 frame header (first 10 bytes).
    if len(bytestring) >= position+10:
        frame_header = ID3V2FrameHeader(bytestring[position:position+10])
    else:
        print('ERROR:')
        print(bytestring[position:position+10])
        return None

    # Read ID3v2 frame body.
    frame_body = bytestring[position + 10:position + 10 + frame_header.framesize]

    if frame_body:
        # Detect frame type:
        if frame_header.frameid[0] == 'T':
            # Text information frame
            frame = FrameTextInfo(frame_header, frame_body)
            return frame

        elif frame_header.frameid == 'COMM':
            # Comments frame
            frame = FrameComments(frame_header, frame_body)
            return frame

        else:
            frame = ID3V2Frame(frame_header, frame_body)
            return frame

    else:
        return None


def write_tag(tag):
    """
    Write tag data into byte string

    :type tag: ID3V2Tag
    :param tag:
    """

    # Refresh tag before writing
    tag.refresh()

    # Write tag header
    bytestring = tag.header.raw_data

    # Write tag frames
    for fr in tag.frames.values():
        bytestring = bytestring + fr.header.raw_data + fr.raw_body

    return bytestring