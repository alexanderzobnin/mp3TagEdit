"""

"""


class ID3V2Header:
    """
    ID3v2 tag header.
    """
    def __init__(self, byteheader):
        """

        """

        self.id = byteheader[:3].decode()
        self.version = str(byteheader[3]) + '.' + str(byteheader[4])
        self.flags = byteheader[5]
        self.tagsize = convert_tag_size(byteheader[6:])
        self.unsynchronisation = bool(byteheader[5] & 128 == 128)
        self.extended_header = bool(byteheader[5] & 64 == 64)
        self.experimental_indicator = bool(byteheader[5] & 32 == 32)

    def print(self):
        print('ID3v2/file Identifier:', self.id)
        print('ID3v2 Version:', self.version)
        print('ID3v2 Flags: {0:08b}'.format(self.flags))
        print('ID3v2 size: {0} bytes'.format(self.tagsize))
        print('ID3v2 Unsynchronisation:', self.unsynchronisation)
        print('ID3v2 Extended header:', self.extended_header)
        print('ID3v2 Experimental indicator:', self.experimental_indicator)


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
        flags = ''
        for flagbyte in self.flags:
            flags += '{0:08b} '.format(flagbyte)
        print('Frame flags:', flags)


class ID3V2Frame:
    """
    ID3v2 Frame.
    """
    def __init__(self, frame_header, frame_body):
        """


        :type frame_header: ID3V2FrameHeader
        :param frame_header: 
        :param frame_body: 
        """
        self.header = frame_header
        self.size = self.header.framesize + 10
        self.raw_body = frame_body
        self.body = decode_frame_body(frame_body)
    
    def print(self):
        self.header.print()
        print('Frame body:', self.body)


def convert_tag_size(sizebytes):
    """
    Convert ID3v2 tag size to bytes.

    :param sizebytes:
    :return:
    """

    size = 0
    for i in range(0, 4):
        sizebyte = int(sizebytes[i]) * (256**(3-i))
        #print('{0:0X}'.format(sizebytes[i]))
        #print(sizebyte)
        #print(sizebyte >> (3-i))
        size += sizebyte >> (3-i)
    return size


def read_id3_header(bytestring):
    """
    Read ID3v2 header from byte string.

    :type bytestring:
    :param bytestring:
    :return ID3V2Header object.
    """

    header = bytestring[:10]
    id3header = ID3V2Header(header)
    id3header.print()
    return id3header


def read_id3_frame_header(bytestring, position=0):
    """
    Read ID3v2 frame header
    :param bytestring:
    :param position:
    :return: ID3V2FrameHeader object
    """
    byteheader = bytestring[position:position+10]
    frame_header = ID3V2FrameHeader(byteheader)
    return frame_header


def decode_frame_body(bytestring):
    """
    Convert frame body in sting.
    :param bytestring:
    :return: String contained frame body.
    """
    # Read first byte in frame and detect encodig
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


def read_frame(bytestring, position=0):
    """
    Read ID3v2 frame into ID3V2Frame object.
    :param bytestring:
    :param position:
    :return:
    """
    frame_header = read_id3_frame_header(bytestring, position)
    frame_body = bytestring[position + 10:position + 10 + frame_header.framesize]
    if frame_body:
        frame = ID3V2Frame(frame_header, frame_body)
        return frame
    else:
        return None


def read_frames(bytestring):
    """
    Read frames from ID3v2 tag.
    :param bytestring:
    :return:
    """

    tag_header = read_id3_header(bytestring)
    tag = bytestring[:tag_header.tagsize]
    read_position = 10

    frames = []
    while read_position < tag_header.tagsize:
        fr = read_frame(tag, read_position)
        if fr.raw_body:
            frames.append(fr)
            fr.print()

        if fr.size != 0:
            read_position += fr.size
        else:
            read_position += 1

    return  frames