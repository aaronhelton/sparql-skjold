from django.db import models
from jsonfield import JSONField

# Create your models here.

class Cache(models.Model):
  # a simple db-backed triple cache to speed up the most expensive list-based queries
  md5 = models.CharField(max_length=32)
  language = models.CharField(max_length=2)
  result_set = JSONField()
  
  def __unicode__(self):
    return self.md5
