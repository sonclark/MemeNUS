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
#app_domain = "localhost:8080/"
ivle_api_key = "ph2hxIVG4Fzcr6e8OzZAQ"

class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key
        return self.session_store.get_session()

config = {}

config['webapp2_extras.sessions'] = {
    'secret_key': ivle_api_key,
}

class MainPage(BaseHandler):
    def get(self):

        self.session['ivle_token'] = ""
        self.session['is_valid'] = False

        template_values = {
            'login_url' : 'https://ivle.nus.edu.sg/api/login/?apikey=' + ivle_api_key + '&url=' +app_domain + 'welcome'
        }

        template = jinja_environment.get_template('welcome.html')
        self.response.out.write(template.render(template_values))



class Welcome(BaseHandler):
    def get(self):
        if self.session.get('is_valid') != True:
            self.session['ivle_token'] = self.request.get('token')
            self.session['is_valid'] = json.load(urllib2.urlopen('https://ivle.nus.edu.sg/api/Lapi.svc/Validate?APIKey=' + ivle_api_key + '&Token=' + self.session.get('ivle_token')))['Success']

        if self.session.get('is_valid') == True:
            student_profile_object = json.load(urllib2.urlopen('https://ivle.nus.edu.sg/api/Lapi.svc/Profile_View?APIKey=' + ivle_api_key + '&AuthToken=' + self.session.get('ivle_token')))['Results'][0]
            #self.session['student_id'] = student_profile_object['UserID']
            self.session['student_name'] = student_profile_object['Name']
            self.session['student_email'] = student_profile_object['Email']
            #self.session['student_matriculation_year'] = student_profile_object['MatriculationYear']
            #self.session['student_first_major'] = student_profile_object['FirstMajor']
            #self.session['student_second_major'] = student_profile_object['SecondMajor']
            #self.session['student_faculty'] = student_profile_object['Faculty']


            template_values = {
                'student_name' : self.session.get('student_name'),
                'student_email' : self.session.get('student_email')
            }

            template = jinja_environment.get_template("home.html")
            self.response.out.write(template.render(template_values))
        else :
            self.redirect(app_domain)

class Upload(BaseHandler):
    image = ""
    def post(self):
        global image
        image = self.request.get("textinput")
        self.redirect(app_domain + "upload")
    def get(self):
        if self.session.get('is_valid') != True:
            self.session['ivle_token'] = self.request.get('token')
            self.session['is_valid'] = json.load(urllib2.urlopen('https://ivle.nus.edu.sg/api/Lapi.svc/Validate?APIKey=' + ivle_api_key + '&Token=' + self.session.get('ivle_token')))['Success']

        if self.session.get('is_valid') == True:

            template_values = {
                'student_name' : self.session.get('student_name'),
                'student_email' : self.session.get('student_email'),
                'image' : image
            }

            template = jinja_environment.get_template("upload.html")
            self.response.out.write(template.render(template_values))
        else :
            self.redirect(app_domain)

app = webapp2.WSGIApplication([
                                  ('/', MainPage),
                                  ('/welcome', Welcome),
                                  ('/upload', Upload)
                                  ],
                              config = config,
                                        debug=True)
