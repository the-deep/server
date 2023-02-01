import pickle
from django.db import models

import logging

from apps.user_resource.models import UserResourceCreated
from project.models import Project


logger = logging.getLogger(__name__)


class LSHIndex(UserResourceCreated):
    """
    Uses datasketch LSH Index
    """

    THRESHOLD = 0.55  # The value comes from experiments conducted on test CORE dataset
    """
    EXPERIMENTS SUMMARY
    ====================
    MODEL                  BEST THRESHOLD CORRESP JACC SIM SENTENCE_ENC_TIME(S) CREATE_INDEX_TIME(S)
    -----                  -------------- ---------------- -------------------- --------------------
    glove_6b_300d          0.675          0.7709           9.38197              0.02754
    paraphrase_Lm          1.5            0.6184           697                  0.00779
    glove_840b_300d        0.525          0.7385           9.7624               0.00705

    datasketch_lsh_perm256 0.55           0.7981           52.82732             6.4
    datasketch_lsh_perm128 0.55           0.7816           37.68474             4.81983
    """
    NUM_PERM = 128

    class IndexStatus(models.IntegerChoices):
        CREATING = 0, "Creating"
        CREATED = 1, "Created"

    name = models.CharField(max_length=256)
    status = models.PositiveIntegerField(
        choices=IndexStatus.choices,
        default=IndexStatus.CREATING,
    )
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        unique=True,
    )
    pickle_version = models.CharField(max_length=10, null=True)
    index_pickle = models.BinaryField(null=True)
    """
    A NOTE ON index_pickle - @bewakes, Feb 02 2023

    The index needs to persist that's why it is pickled and stored in db.
    Another alternative would be to store it in other storages like s3 but I
    think using db is lot cleaner.

    One concern is what if the index gets larger. Postgres column can handle
    columns upto 2 GB. The index indeed increases linearly in size with ~700
    Bytes per document. But the number of leads in a project in DEEP is maximum
    ~8300 till date, which will make the index size around 7MB which is not
    that much even if we have around 20K leads per project.

    We can also use redis as storage, but we will eventually need to persist
    data somewhere and having both will add complexity.
    """
    has_errored = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "LSH Indices"

    def load_index(self):
        """This sets the attribute index if pickle is present"""
        if (
            hasattr(self, "index_pickle") and
            self.index_pickle is not None and
            self.pickle_version is not None
        ):
            supported_formats = pickle.compatible_formats
            if self.pickle_version not in supported_formats:
                logger.warn(
                    "Pickle versions not compatible, setting index to None"
                )
                self._index = None
            else:
                self._index = pickle.loads(self.index_pickle)
        else:
            self._index = None
        self._index_loaded = True

    @property
    def index(self):
        if not self._index_loaded or (
            self._index is None and self.index_pickle is not None
        ):
            self.load_index()
        return self._index

    @index.setter
    def index(self, value):
        self._index = value
        self.index_pickle = pickle.dumps(value)

    def __init__(self, *args, **kwargs):
        self._index_loaded = False
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        # Set self._index_loaded = False so that next time it is accessed, it
        # is reloaded
        self._index_loaded = False
        super().save(*args, **kwargs)
