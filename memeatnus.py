#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import jinja2

import os
import urllib2
import json
import os
import HTMLParser
from webapp2_extras import sessions
from urlparse import urlparse
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + "/templates"), autoescape=True)
app_domain = "http://memeatnus.appspot.com/"

class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        #if login already
        upload_url = blobstore.create_upload_url('/submit')

        if user:
            parent_key = ndb.Key('Persons', users.get_current_user().email())
            query = ndb.gql("SELECT * "
                            "FROM Images "
                            "ORDER BY date DESC "
                            )
            query2 = ndb.gql("SELECT *"
                             "from Liked_photos "
                             "WHERE ANCESTOR IS :1 ",
                             parent_key
            )

            template_values = {
                'user_mail' : users.get_current_user().email(),
                'user_name' : users.get_current_user().email().split("@")[0],
                'logout' : users.create_logout_url(self.request.host_url),
                'items' : query,
                'upload_url' :upload_url,
                'liked_photos' : query2,
                'liked_photos_count' : query2.count(),

            }

            template = jinja_environment.get_template('home.html')
            self.response.out.write(template.render(template_values))
        else :
            template = jinja_environment.get_template('welcome.html')
            self.response.out.write(template.render())

class Persons(ndb.Model):
    next_item = ndb.IntegerProperty()
    next_like = ndb.IntegerProperty()

class Liked_photos(ndb.Model):
    photos_id = ndb.StringProperty()
    like_status = ndb.StringProperty()

class Images(ndb.Model):
    #Models an item with item_link, image_link, description, and date. Key is item_id.
    item_id = ndb.IntegerProperty()
    image_link =  ndb.StringProperty()
    description = ndb.TextProperty()
    image_key = ndb.BlobKeyProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)
    likes = ndb.IntegerProperty()
    dislikes = ndb.IntegerProperty()
    #store the ownername + image_link
    OwnerString = ndb.StringProperty()


class Submit_likes(webapp2.RequestHandler):
    def post(self):
        like = str(self.request.get('like'))
        dislike =str (self.request.get('dislike'))

        parent = ndb.Key('Persons', users.get_current_user().email())
        person = parent.get()



        if person == None:
            person = Persons(id=users.get_current_user().email())
            person.next_item = 1
            person.next_like = 1



        if like:

            liked = ndb.gql("SELECT *"
                            "from Liked_photos "
                            "WHERE ANCESTOR IS :1 "
                            "AND photos_id = :2 ",
                            parent, like
            )

            query = ndb.gql("SELECT * "
                            "FROM Images "
                            "WHERE OwnerString = :1",like
            )

            if liked.count() == 0:
                like_photos = Liked_photos(parent=parent, id = str(person.next_like))
                like_photos.photos_id = like
                like_photos.like_status = "like"
                like_photos.put()
                person.next_like+=1
            else:
                query_liked = ndb.gql("SELECT * "
                                "FROM Liked_photos "
                                "WHERE photos_id = :1", like)
                for item in query_liked:
                    item.like_status = "like"
                    item.put()
            for item in query:
                item.likes +=1
                item.put()

            person.put()
        if dislike:
            liked = ndb.gql("SELECT *"
                            "from Liked_photos "
                            "WHERE ANCESTOR IS :1 "
                            "AND photos_id = :2 ",
                            parent, dislike
            )
            query = ndb.gql("SELECT * "
                            "FROM Images "
                            "WHERE OwnerString = :1",dislike)

            if liked.count() == 0:
                like_photos = Liked_photos(parent=parent, id = str(person.next_like))
                like_photos.photos_id = dislike
                like_photos.like_status = "dislike"
                person.next_like+=1
                like_photos.put()
            else:
                query_liked = ndb.gql("SELECT * "
                                "FROM Liked_photos "
                                "WHERE photos_id = :1", dislike)
                for item in query_liked:
                    item.like_status = "dislike"
                    item.put()

            for item in query:
                item.likes -=1
                item.put()

            person.put()
        self.redirect(app_domain)
    def get(self):
        self.redirect(app_domain)

class Submit(blobstore_handlers.BlobstoreUploadHandler, webapp2.RequestHandler):
    def post(self):
        parent = ndb.Key('Persons', users.get_current_user().email())
        person = parent.get()

        if person == None:
            person = Persons(id=users.get_current_user().email())
            person.next_item = 1
            person.next_like = 1
        image = Images(parent=parent, id = str(person.next_item))
        image.item_id = person.next_item
        image.likes = 0
        image.dislikes = 0

        uploadfile = self.get_uploads('filebutton')
        image.image_key = uploadfile[0].key()
        image.description = self.request.get("test2")
        image.image_link = images.get_serving_url(image.image_key)
        image.OwnerString = str(image.image_link)+"/"+users.get_current_user().email().split("@")[0]

        if image.image_key != '':
            person.next_item +=1
            person.put()
            image.put()
        self.redirect(app_domain + "upload")
    def get(self):
        self.redirect(app_domain)

class Upload(webapp2.RequestHandler):
    def post(self):
        #retrieve person
        parent = ndb.Key('Persons', users.get_current_user().email())
        person = parent.get()

        #If no such user in DB, create that user
        if person == None:
            person = Persons(id=users.get_current_user().email())
            person.next_item = 1
            person.next_like = 1
        image = Images(parent=parent, id = str(person.next_item))
        image.item_id = person.next_item
        image.likes = 0
        image.dislikes = 0

        image.image_link = self.request.get("textinput")
        image.description = self.request.get("test1")
        image.OwnerString = str(image.image_link)+"/"+users.get_current_user().email().split("@")[0]

        if image.image_link.rstrip() != '' :
            person.next_item +=1
            person.put()
            image.put()
        self.redirect(app_domain + "upload")


    def get(self):
        self.show()

    def show(self):
        user = users.get_current_user()
        if user:

            parent_key = ndb.Key('Persons', users.get_current_user().email())
            query = ndb.gql("SELECT * "
                            "FROM Images "
                            "WHERE ANCESTOR IS :1 "
                            "ORDER BY date DESC",
                            parent_key)
            upload_url = blobstore.create_upload_url('/submit')


            template_values = {
                'user_mail' : users.get_current_user().email(),
                'user_name' : users.get_current_user().email().split("@")[0],
                'logout' : users.create_logout_url(self.request.host_url),
                'items' : query,
                'items_num' : query.count(),
                'upload_url' : upload_url,

            }

            template = jinja_environment.get_template("upload.html")
            self.response.out.write(template.render(template_values))
        else :
            self.redirect(self.request.host_url)

class DeleteItem(webapp2.RequestHandler):
    # Delete item specified by user

    def post(self):
        item = ndb.Key('Persons', users.get_current_user().email(), 'Images', self.request.get('itemid'))
        item.delete()
        self.redirect('/upload')

class DeleteItem_images(webapp2.RequestHandler):
    # Delete item specified by user

    def post(self):
        item = ndb.Key('Persons', users.get_current_user().email(), 'Images', self.request.get('itemid'))
        item.delete()
        blobstore.delete(self.request.get('blobkey'))
        self.redirect('/upload')

class GetOpenId(webapp2.RequestHandler):
    def post(self):
        openId = self.request.get('openId').rstrip()
        self.redirect(users.create_login_url('/',None, federated_identity=openId))

class Profile(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:

            parent_key = ndb.Key('Persons', users.get_current_user().email())
            query = ndb.gql("SELECT * "
                            "FROM Images "
                            "WHERE ANCESTOR IS :1 "
                            "ORDER BY date DESC",
                            parent_key)
            upload_url = blobstore.create_upload_url('/submit')
            template_values = {
                'user_mail' : users.get_current_user().email(),
                'user_name' : users.get_current_user().email().split("@")[0],
                'logout' : users.create_logout_url(self.request.host_url),
                'items' : query.count(),
                'upload_url' : upload_url,

            }
            template = jinja_environment.get_template("profile.html")
            self.response.out.write(template.render(template_values))
        else :
            self.redirect(self.request.host_url)

app = webapp2.WSGIApplication([
                                  ('/', MainPage),
                                  ('/deleteitem', DeleteItem),
                                  ('/deleteitem_images', DeleteItem_images),
                                  #('/welcome', Welcome),
                                  ('/submit_likes',Submit_likes),
                                  ('/upload', Upload),
                                  ('/submit', Submit),
                                  ('/profile', Profile),
                                  ('/getOpenId', GetOpenId),

                                  ],
                                    debug=True)
