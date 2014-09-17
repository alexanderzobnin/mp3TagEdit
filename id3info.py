"""
Information about music file.
"""

import id3v23tag


class ID3Info:
    """
    Information about music file.
    """

    def __init__(self, title='', artist='', album=''):
        """

        :return:
        """
        self.title = title
        self.artist = artist
        self.album = album

    def __str__(self):
        return '{artist} - {title} ({album})'.format(**self.__dict__)

    def __repr__(self):
        return 'Artist: {artist}\nTitle: {title}\nAlbum: {album}'.format(**self.__dict__)

    @staticmethod
    def read(id3tag):
        """

        :type id3tag: id3v23tag.ID3V2Tag
        :param id3tag:
        :return:
        """
        id3_info = ID3Info()
        if 'TIT2' in id3tag.frames:
            id3_info.title = id3tag.frames['TIT2'].text
        if 'TPE1' in id3tag.frames:
            id3_info.artist = id3tag.frames['TPE1'].text
        if 'TALB' in id3tag.frames:
            id3_info.album = id3tag.frames['TALB'].text