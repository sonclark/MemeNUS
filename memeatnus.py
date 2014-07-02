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
            query = ndb.gql("SELECT * "
                            "FROM Images "
                            "ORDER BY date DESC "
                            )
            query2 = ndb.gql("SELECT * "
                             "FROM Images2 "
                             "ORDER BY date DESC")

            template_values = {
                'user_mail' : users.get_current_user().email(),
                'user_name' : users.get_current_user().email().split("@")[0],
                'logout' : users.create_logout_url(self.request.host_url),
                'items' : query,
                'items2' : query2,
                'upload_url' :upload_url,
            }

            template = jinja_environment.get_template('home.html')
            self.response.out.write(template.render(template_values))
        else :
            template = jinja_environment.get_template('welcome.html')
            self.response.out.write(template.render())

class Persons(ndb.Model):
    next_item = ndb.IntegerProperty()

class Images(ndb.Model):
    #Models an item with item_link, image_link, description, and date. Key is item_id.
    item_id = ndb.IntegerProperty()
    image_link =  ndb.StringProperty()
    description = ndb.TextProperty()
    #image = ndb.BlobKeyProperty
    date = ndb.DateTimeProperty(auto_now_add=True)

class Images2(ndb.Model):
    item_id = ndb.IntegerProperty()
    image_key = ndb.BlobKeyProperty()
    servingUrl = ndb.StringProperty()
    description = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)

class Submit(blobstore_handlers.BlobstoreUploadHandler, webapp2.RequestHandler):
    def post(self):
        parent = ndb.Key('Persons', users.get_current_user().email())
        person = parent.get()

        if person == None:
            person = Persons(id=users.get_current_user().email())
            person.next_item = 1
        image = Images2(parent=parent, id = str(person.next_item))
        image.item_id = person.next_item

        uploadfile = self.get_uploads('filebutton')
        image.image_key = uploadfile[0].key()
        image.description = self.request.get("test2")
        image.servingUrl = images.get_serving_url(image.image_key)

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

        image = Images(parent=parent, id = str(person.next_item))
        image.item_id = person.next_item

        image.image_link = self.request.get("textinput")
        image.description = self.request.get("test1")

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
            query2 = ndb.gql("SELECT * "
                             "FROM Images2 "
                             "WHERE ANCESTOR IS :1 "
                             "ORDER BY date DESC",
                             parent_key)
            #for pic in query2:
             #   pic.servingUrl = images.get_serving_url(pic.image_key)

            template_values = {
                'user_mail' : users.get_current_user().email(),
                'user_name' : users.get_current_user().email().split("@")[0],
                'logout' : users.create_logout_url(self.request.host_url),
                'items' : query,
                'items_num' : query.count(),
                'upload_url' : upload_url,
                'pic' : query2,
                'pic_num' : query2.count()

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
        item = ndb.Key('Persons', users.get_current_user().email(), 'Images2', self.request.get('itemid'))
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

            template_values = {
                'user_mail' : users.get_current_user().email(),
                'user_name' : users.get_current_user().email().split("@")[0],
                'logout' : users.create_logout_url(self.request.host_url),
                'items' : query.count()

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
                                  ('/upload', Upload),
                                  ('/submit', Submit),
                                  ('/profile', Profile),
                                  ('/getOpenId', GetOpenId),

                                  ],
                                    debug=True)
