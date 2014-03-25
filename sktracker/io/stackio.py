import os
import logging

import numpy as np

from .metadataio import get_metadata
from . import TiffFile

log = logging.getLogger(__name__)

__all__ = ['StackIO']

class StackIO:
    """StackIO is designed to deal with Input/Output images. It can retrieve all
    kind of metadata with various methods. It also allows fast and efficient way
    to get image data (in memory or via an iterator).

    Parameters
    ----------
    image_path : str or None
    image_path_list : list or None
    base_dir : path or None
        Specify a root directory relative to `image_path`.
    json_discovery : bool
        Find metadata in metadata.json files

    """

    def __init__(self,
                 image_path=None,
                 image_path_list=None,
                 metadata=None,
                 base_dir=None,
                 json_discovery=False):

        self.base_dir = base_dir
        if image_path_list:
            image_path = image_path_list[0]
        if metadata:
            self.metadata = metadata
        else:
            self.metadata = get_metadata(image_path, json_discovery)
        self._image_path_list = image_path_list

    @property
    def image_path_list(self):
        if not self._image_path_list:
            return
        if self.base_dir:
             return [os.path.join(self.base_dir, image)
                     for image in self._image_path_list]
        else:
            return self._image_path_list

    @property
    def image_path(self):
        if self.base_dir:
            return os.path.join(self.base_dir, self.metadata['FileName'])
        else:
            return self.metadata['FileName']

    @classmethod
    def from_objectsio(cls, objectsio):
        """Load images and metadata from `sktracker.io.ObjectsIO`

        Parameters
        ----------
        objectsio : object
            `sktracker.io.ObjectsIO` instance.
        """

        return cls(image_path=objectsio.image_path, metadata=objectsio.metadata)

    def get_tif(self):
        """Get TiffFile instance.

        Returns
        -------
        tf : object
            An `sktracker.io.TiffFile` instance.

        """

        tf = TiffFile(self.image_path)
        return tf

    def get_tif_from_list(self, index=0):
        """Get TiffFile instance from images list.

        Returns
        -------
        tf : object
            An `sktracker.io.TiffFile` instance.

        """

        tf = TiffFile(self.image_path_list[index])
        return tf

    def image_iterator(self, channel_index=0, memmap=True):
        """Iterate over image T and Z dimensions. A channel has to be
        choosen and will be excluded from the iterator.

        Parameters
        ----------
        channel_index : int
            Channel position to remove
        memmap : bool
            If True, use `numpy.memmap` to read arrays from file if possible.

        Returns
        -------
        A Python iterator over the image array.

        """

        tf = self.get_tif()
        arr = tf.asarray(memmap=memmap)

        # Get only one single channel
        channel_position = self.metadata['DimensionOrder'].index('C')
        arr = np.take(arr, channel_index, axis=channel_position)

        # Define data iterator
        def it():
            for idx in np.ndindex(arr.shape[:-2]):
                yield arr[idx]

        return it

    def list_iterator(self, memmap=True):
        """Returns an iterator over each image from
        `self.image_path_list` as an array

        Parameters
        ----------
        memmap : bool
            If True, use `numpy.memmap` to read arrays from file if possible.

        Returns
        -------
        A Python iterator over the image list.
        """
        image_list = self.image_path_list
        def stack_iter():
            for filename in image_list:
                stack = TiffFile(filename).asarray(memmap=memmap)
                yield stack
        return stack_iter
