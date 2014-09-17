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

    def __repr__(self):
        repr_string = ('-' * 40 + '\n\tTag header:\n' + '-' * 40 + '\n')
        repr_string += 'ID3v2/file Identifier: {}\n'.format(self.id)
        repr_string += 'ID3v2 Version: {0}.{1}'.format(self.version[0], self.version[1]) + '\n'
        repr_string += 'ID3v2 size: {0} bytes'.format(self.tagsize) + '\n'
        repr_string += 'ID3v2 Unsynchronisation: {}\n'.format(self.unsynchronisation.__str__())
        repr_string += 'ID3v2 Extended header: {}\n'.format(self.extended_header.__str__())
        repr_string += 'ID3v2 Experimental indicator: {}\n'.format(self.experimental_indicator.__str__())
        repr_string += ('-' * 40 + '\n\tFrames:\n' + '-' * 40 + '\n')
        for fr in self.frames.values():
            repr_string += fr.__repr__() + '\n'
            repr_string += ('-' * 40 + '\n')
        return repr_string

    def __str__(self):
        repr_string = 'ID3v2 tag ({0} bytes)\n'.format(self.tagsize)
        for fr in self.frames.values():
            repr_string += '{0}: {1}\n'.format(fr.id, fr.__str__())
        return repr_string

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
        To encode tag size take a 'size' variable and do this:

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
        try:
            tag_id = tag_header[:3].decode()
            if tag_id != 'ID3':
                #! raise exception NOT_ID3_TAG
                return None
        except UnicodeDecodeError:
            # Not ID3v2.3 tag
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

    def encode(self):
        # Refresh tag header raw_data
        new_raw_tag = self.id.encode() + self.version

        # Write flags
        flags = 0
        if self.unsynchronisation:
            flags += 0x80
        if self.extended_header:
            flags += 0x40
        if self.experimental_indicator:
            flags += 0x20
        new_raw_tag += flags.to_bytes(1, byteorder='big')

        # Write size
        new_raw_tag += self.encode_tagsize(self.tagsize)

        # Write frames
        for fr in self.frames.values():
            new_raw_tag += fr.encode()

        # Calculate new tag size
        new_size = 0
        for fr in self.frames.values():
            new_size += fr.size + 10

        if new_size > self.tagsize:
            self.tagsize = new_size
        else:
            # Add padding
            padding_size = self.tagsize - new_size
            new_raw_tag += b'\x00' * padding_size

        return new_raw_tag


class ID3V2Frame:
    """
    Base ID3v2 frame object.


    ID3 frame:

    |Frame header (10 bytes)            |Frame body |
    |Frame ID     |Size         |Flags  |           |
    -------------------------------------------------
    |$xx xx xx xx |$xx xx xx xx |$xx xx |Frame body |
    -------------------------------------------------
    """

    def __init__(self, frame_id='WNUL', frame_body=b'\x20', flags=b'\x00\x00'):
        self.id = frame_id
        self.flags = flags
        self.data = frame_body

        # Total size of frame
        self.size = len(frame_body)

    def __str__(self):
        return self.data

    def __repr__(self):
        repr_string = 'Frame ID: {}\n'.format(self.id)
        repr_string += 'Frame Size: {0} bytes\n'.format(self.size)
        if self.flags != b'\x00\x00':
            repr_string += 'Frame flags: {0:08b} {0:08b}\n'.format(*self.flags)
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
    def encode(self):
        pass

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
        repr_string = 'Frame ID: {}\n'.format(self.frameid)
        repr_string += 'Frame Size: {0} bytes'.format(self.framesize)
        if self.flags != b'\x00\x00':
            repr_string += 'Frame flags: {0:08b} {0:08b}\n'.format(*self.flags)
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
    The text information frames are the most important frames, containing information like artist, album and more.
    There may only be one text information frame of its kind in an tag. If the textstring is followed by a
    termination ($00 (00)) all the following information should be ignored and not be displayed. All text frame
    identifiers begin with "T". Only text frame identifiers begin with "T", with the exception of the "TXXX" frame.
    All the text information frames have the following format:

    <Header for 'Text information frame', ID: "T000" - "TZZZ", excluding "TXXX" described in 4.2.2.>
    Text encoding    $xx
    Information    <text string according to encoding>
    """

    def __init__(self, frame_id='WTXT', data='', encoding='utf_16', flags=b'\x00\x00'):
        super().__init__(frame_id=frame_id, flags=flags)
        self.data = data
        self.encoding = encoding

    def __str__(self):
        return self.data

    def __repr__(self):
        repr_string = 'Frame ID: {}\n'.format(self.id)
        repr_string += 'Frame Size: {0} bytes\n'.format(self.size)
        if self.flags != b'\x00\x00':
            repr_string += 'Frame flags: {0:08b} {0:08b}\n'.format(*self.flags)
        repr_string += 'Frame data: {}\n'.format(self.data)
        return repr_string

    def set_value(self, value):
        # Set text value
        """

        :type value: str
        :param value:
        """
        self.data = value

        # Calculate new frame size
        self.size = len(self.data.encode(self.encoding)) + 1

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
            frame.data = frame_body[1:].decode('iso8859_1')
            frame.encoding = 'iso8859_1'
        elif encoding_byte == 1:
            # Use Unicode
            frame.data = frame_body[1:].decode('utf_16')
            frame.encoding = 'utf_16'
        else:
            frame.data = frame_body.decode()
            frame.encoding = 'unknown'
        return frame

    def encode(self):
        """

        :return:
        """

        raw_frame = b''

        # Write frame header
        raw_frame += self.id.encode('iso8859_1')
        raw_frame += self.size.to_bytes(4, byteorder='big')
        raw_frame += self.flags

        # Write frame data
        if self.encoding == 'iso8859_1':
            raw_frame += b'\x00' + self.data.encode('iso8859_1')
        if self.encoding == 'utf_16':
            raw_frame += b'\x01' + self.data.encode('utf_16')

        return raw_frame


class FrameComments(ID3V2Frame):
    """
    This frame is indended for any kind of full text information that does not fit in any other frame.
    It consists of a frame header followed by encoding, language and content descriptors and is ended
    with the actual comment as a text string. Newline characters are allowed in the comment text string.
    There may be more than one comment frame in each tag, but only one with the same language and content descriptor.

    <Header for 'Comment', ID: "COMM">
    Text encoding           $xx
    Language                $xx xx xx
    Short content descrip.  <text string according to encoding> $00 (00)
    The actual text         <full text string according to encoding>
    """

    def __init__(self, frame_id='WTXT', data='', language='', content_descr='', encoding='utf_16', flags=b'\x00\x00'):
        super().__init__(frame_id=frame_id, flags=flags)
        self.data = data
        self.language = language
        self.content_descr = content_descr
        self.encoding = encoding

    def __str__(self):
        return self.data

    def __repr__(self):
        repr_string = 'Frame ID: {}\n'.format(self.id)
        repr_string += 'Frame Size: {0} bytes\n'.format(self.size)
        if self.flags != b'\x00\x00':
            repr_string += 'Frame flags: {0:08b} {0:08b}\n'.format(*self.flags)
        repr_string += 'language: {}\n'.format(self.language)
        repr_string += 'content_descr: {}\n'.format(self.content_descr)
        repr_string += 'text: {}\n'.format(self.data)
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

        frame_body = bytestring[10:frame.size + 10]
        frame.language = frame_body[1:4].decode()

        # Detect encoding
        encoding_byte = frame_body[0]
        if encoding_byte == 0:
            # Use ISO-8859-1
            text_len = frame_body.find(b'\x00') - 4
            frame.content_descr = frame_body[4:text_len + 4].decode('iso8859_1')
            frame.data = frame_body[text_len+5:].decode('iso8859_1')
            frame.encoding = 'iso8859_1'

        elif encoding_byte == 1:
            # Use Unicode
            text_len = frame_body.find(b'\x00\x00') - 4
            frame.content_descr = frame_body[4:text_len + 4].decode('utf_16')
            frame.data = frame_body[text_len+6:].decode('utf_16')
            frame.encoding = 'utf_16'

        else:
            # Unknown encoding
            return None

        return frame

    def encode(self):
        """

        :return:
        """

        raw_frame = b''

        # Write frame header
        raw_frame += self.id.encode('iso8859_1')
        raw_frame += self.size.to_bytes(4, byteorder='big')
        raw_frame += self.flags

        # Write frame data
        # Write encoding
        if self.encoding == 'iso8859_1':
            raw_frame += b'\x00'
            raw_frame += self.language.encode('iso8859_1')
            raw_frame += self.content_descr.encode('iso8859_1') + b'\x00'
            raw_frame += self.data.encode('iso8859_1')
        if self.encoding == 'utf_16':
            raw_frame += b'\x01'
            raw_frame += self.language.encode('iso8859_1')
            raw_frame += self.content_descr.encode('utf_16') + b'\x00\x00'
            raw_frame += self.data.encode('utf_16')

        return raw_frame