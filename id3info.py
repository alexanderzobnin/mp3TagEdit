"""
Information about music file.
"""

import id3v23tag


class ID3Info:
    """
    Information about music file.
    """

    def __init__(self, id3tag):
        """

        :type id3tag: id3v23tag.ID3V2Tag
        :param id3tag: 
        :return:
        """

        if 'TIT2' in id3tag.frames:
            self.title = id3tag.frames['TIT2'].text
        if 'TPE1' in id3tag.frames:
            self.artist = id3tag.frames['TPE1'].text
        if 'TALB' in id3tag.frames:
            self.album = id3tag.frames['TALB'].text

    def __str__(self):
        return '{0} - {1} ({2})'.format(self.artist, self.title, self.album)

    def print(self, view='short'):
        """
        Print information about song.

        :param view: view mode.
        :return:

        """
        if view == 'verbose':
            print('Artist:', self.artist)
            print('Title:', self.title)
            print('Album:', self.album)

        # Artist - Title (Album)
        if view == 'short':
            print('{0} - {1} ({2})'.format(self.artist, self.title, self.album))