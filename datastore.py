__author__ = 'dso'
from google.appengine.ext import ndb

class Profile(ndb.Model):
    student_id = ndb.StringProperty()

class Picture(ndb.Model):
    images = ndb.BlobKeyProperty(requiried = True)

    comments = ndb.TextProperty
    likes = ndb.IntegerProperty