from __future__ import with_statement

#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#			http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import cgi
import os
import logging
import contextlib
from xml.dom import minidom
from xml.dom.minidom import Document
import exceptions
import warnings
import imghdr
from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import mail
import wsgiref.handlers

# START Constants
CONTENT_TYPE_HEADER = "Content-Type"
CONTENT_TYPE_TEXT = "text/plain"
XML_CONTENT_TYPE = "application/xml"
XML_ENCODING = "utf-8"
"""
Allows you to specify IP addresses and associated "api_key"s to prevent others from using your app.
Storage and Manipulation methods will check for this "api_key" in the POST/GET params.
Retrieval methods don't use it (however you could enable them to use it, but maybe rewrite so you have a "read" key and a "write" key to prevent others from manipulating your data).

Set "AUTH = False" to disable (allowing anyone use your app and CRUD your data).

To generate a hash/api_key visit https://www.grc.com/passwords.htm
To find your ip visit http://www.whatsmyip.org/
"""
AUTH = {
	'000.000.000.000':'JLQ7P5SnTPq7AJvLnUysJmXSeXTrhgaJ',
}
# END Constants

# START Exception Handling
class Error(StandardError):
	pass
class Forbidden(Error):
	pass

logging.getLogger().setLevel(logging.DEBUG)

@contextlib.contextmanager
def mailExcpHandler(ctx):
	try:
		yield {}
	except (ValueError), exc:
		xml_error_response(ctx, 400 ,'app.invalid_parameters', 'The indicated parameters are not valid: ' + exc.message)
	except (Forbidden), exc:
		xml_error_response(ctx, 403 ,'app.forbidden', 'You don\'t have permission to perform this action: ' + exc.message)
	except (Exception), exc:
		xml_error_response(ctx, 500 ,'system.other', 'An unexpected error in the web service has happened: ' + exc.message)

def xml_error_response(ctx, status, error_id, error_msg):
	ctx.error(status)
	doc = Document()
	errorcard = doc.createElement("error")
	errorcard.setAttribute("id", error_id)
	doc.appendChild(errorcard)
	ptext = doc.createTextNode(error_msg)
	errorcard.appendChild(ptext)
	ctx.response.headers[CONTENT_TYPE_HEADER] = XML_CONTENT_TYPE
	ctx.response.out.write(doc.toxml(XML_ENCODING))
# END Exception Handling

# START Helper Methods
def isAuth(ip = None, key = None):
	if AUTH == False:
		return True
	elif AUTH.has_key(ip) and key == AUTH[ip]:
		return True
	else:
		return False

# END Helper Methods


# START Request Handlers
class Send(webapp.RequestHandler):
	def post(self):
		"""
		Sends an email based on POST params. It will queue if resources are unavailable at the time.

		Returns "Success"

		POST Args:
			to: the receipent address
			from: the sender address (must be a registered GAE email)
			subject: email subject
			body: email body content
		"""
		with mailExcpHandler(self):
			# check authorised
			if isAuth(self.request.remote_addr,self.request.POST.get('api_key')) == False:
				raise Forbidden("Invalid Credentials")

			# read data from request
			mail_to = str(self.request.POST.get('to'))
			mail_from = str(self.request.POST.get('from'))
			mail_subject = str(self.request.POST.get('subject'))
			mail_body = str(self.request.POST.get('body'))

			mail.send_mail(mail_from, mail_to, mail_subject, mail_body)

			self.response.headers[CONTENT_TYPE_HEADER] = CONTENT_TYPE_TEXT
			self.response.out.write("Success")


# END Request Handlers

# START Application
application = webapp.WSGIApplication([
																			 ('/send', Send)
																		 ],debug=True)

def main():
	run_wsgi_app(application)

if __name__ == '__main__':
	main()

# END Application