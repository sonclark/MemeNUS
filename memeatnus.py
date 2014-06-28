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


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + "/templates"), autoescape=True)
app_domain = "http://memeatnus.appspot.com/"

class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        #if login already
        if user:
            template_values = {
                'user_mail' : users.get_current_user().email(),
                'user_name' : users.get_current_user().email().split("@")[0],
                'logout' : users.create_logout_url(self.request.host_url),

            }
            template = jinja_environment.get_template('home.html')
            self.response.out.write(template.render(template_values))
        else :
            template = jinja_environment.get_template('welcome.html')
            self.response.out.write(template.render())



class Welcome(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            template_values = {
                'user_mail' : users.get_current_user().email(),
                'user_name' : users.get_current_user().email().split("@")[0],
                'logout' : users.create_logout_url(self.request.host_url),

            }

            template = jinja_environment.get_template("home.html")
            self.response.out.write(template.render(template_values))
        else :
            self.redirect(self.request.host_url)

class Upload(webapp2.RequestHandler):
    image = ""
    def post(self):
        global image
        image = self.request.get("textinput")
        self.redirect(app_domain + "upload")
    def get(self):
        user = users.get_current_user()
        if user:
            template_values = {
                'user_mail' : users.get_current_user().email(),
                'user_name' : users.get_current_user().email().split("@")[0],
                'logout' : users.create_logout_url(self.request.host_url),
                'image' : image
            }

            template = jinja_environment.get_template("upload.html")
            self.response.out.write(template.render(template_values))
        else :
            self.redirect(self.request.host_url)


class GetOpenId(webapp2.RequestHandler):
    def post(self):
        openId = self.request.get('openId').rstrip()
        self.redirect(users.create_login_url('/',None, federated_identity=openId))

app = webapp2.WSGIApplication([
                                  ('/', MainPage),
                                  ('/welcome', Welcome),
                                  ('/upload', Upload),
                                  ('/getOpenId', GetOpenId),

                                  ],
                                    debug=True)
