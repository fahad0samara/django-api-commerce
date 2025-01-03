from django.db import models
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex

class SearchableModel(models.Model):
    search_vector = SearchVectorField(null=True, blank=True)
    
    class Meta:
        abstract = True
        indexes = [GinIndex(fields=['search_vector'])]
