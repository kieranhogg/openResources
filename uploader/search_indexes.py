import datetime
from haystack import indexes
from uploader.models import Note, Resource


class NoteIndex(indexes.SearchIndex, indexes.Indexable):
        text = indexes.CharField(document=True, use_template=True)

        def get_model(self):
            return Note

        def index_queryset(self, using=None):
            """Used when the entire index for model is updated."""
            return self.get_model().objects.filter()

class ResourceIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    unit_topic = indexes.CharField(model_attr='unit_topic', null=True)
    pub_date = indexes.DateTimeField(model_attr='pub_date')

    def get_model(self):
        return Resource

    
