"""
Module for read ID3v2.3 tag.
"""

from id3v23frames import *


class ID3V2Tag:
    """
    ID3v2 tag.
    """
    def __init__(self, tag_header, frames):
        """

        :type tag_header: ID3V2TagHeader
        :param tag_header:
        :type frames: list[ID3V2Frame]
        :param frames:
        """
        self.header = tag_header
        self.frames = frames

    def print(self):
        print('-' * 30 + '\n\tTag header:\n' + '-' * 30)
        self.header.print()
        print('-' * 30 + '\n\tFrames:\n' + '-' * 30)
        for fr in self.frames:
            fr.print()


class ID3V2TagHeader:
    """
    ID3v2 tag header.
    """
    def __init__(self, byteheader):
        self.id = byteheader[:3].decode()
        self.version = str(byteheader[3]) + '.' + str(byteheader[4])

        #! flags used for testing (print flag byte as is). May be deleted in future.
        self.flags = byteheader[5]
        self.tagsize = ID3V2TagHeader.convert_tag_size(byteheader[6:])

        """
        Read flags (byte #6 after version bytes).
        Flag structure: %abc00000 where:
            a - Unsynchronisation
            b - Extended header
            c - Experimental indicator
        """
        self.unsynchronisation = bool(byteheader[5] & 128 == 128)
        self.extended_header = bool(byteheader[5] & 64 == 64)
        self.experimental_indicator = bool(byteheader[5] & 32 == 32)

    def print(self):
        """
        Print tag header information (for testing).
        :return:
        """
        print('ID3v2/file Identifier:', self.id)
        print('ID3v2 Version:', self.version)
        print('ID3v2 Flags: {0:08b}'.format(self.flags))
        print('ID3v2 size: {0} bytes'.format(self.tagsize))
        print('ID3v2 Unsynchronisation:', self.unsynchronisation)
        print('ID3v2 Extended header:', self.extended_header)
        print('ID3v2 Experimental indicator:', self.experimental_indicator)
        print()

    @staticmethod
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
    id3header = ID3V2TagHeader(header)
    return id3header


def read_id3_frame_header(bytestring, position=0):
    """
    Read ID3v2 frame header.

    :param bytestring:
    :param position:
    :return: ID3V2FrameHeader object
    """
    byteheader = bytestring[position:position+10]
    frame_header = ID3V2FrameHeader(byteheader)
    return frame_header


def read_frame(bytestring, position=0):
    """
    Read ID3v2 frame into ID3V2Frame object.

    :param bytestring: bytestring contains raw ID3 tag data.
    :param position:
    :return:
    """
    frame_header = read_id3_frame_header(bytestring, position)
    frame_body = bytestring[position + 10:position + 10 + frame_header.framesize]
    if frame_body:
        # Detect frame type:
        if frame_header.frameid in FrameTypes:
            frame_type = FrameTypes[frame_header.frameid]
            if frame_type == 'TextInfo':
                frame = FrameTextInfo(frame_header, frame_body)
                return frame
            elif frame_type == 'Comments':
                frame = FrameComments(frame_header, frame_body)
                return frame
            else:
                frame = ID3V2Frame(frame_header, frame_body)
                return frame
        else:
            frame = ID3V2Frame(frame_header, frame_body)
            return frame
    else:
        return None


def read_frames(bytestring):
    """
    Read frames from ID3v2 tag.

    :param bytestring:
    :return: ID3V2Tag object
    :rtype: ID3V2Tag
    """
    # Read tag header
    tag_header = read_id3_header(bytestring)

    # Tag contains raw ID3 tag data
    tag = bytestring[:tag_header.tagsize]

    # Start read from tag body, don't read tag header
    read_position = 10

    frames = []

    # Read, until tag end (using tagsize).
    while read_position < tag_header.tagsize:
        fr = read_frame(tag, read_position)
        if fr:
            frames.append(fr)

            # Calculate next frame position
            read_position += fr.size

        # If frame object fr is empty stop reading
        else:
            break

    id3_tag = ID3V2Tag(tag_header, frames)
    return  id3_tag