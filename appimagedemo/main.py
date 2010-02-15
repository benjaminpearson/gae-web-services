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


# Based on Appspotimage at http://code.google.com/p/appspotimage/ written by Carlos Merida-Campos
# This version has been modified to add new models, remove 3scale integration and reduce methods to
# resize and crop with options to specify "pixels" and "percentages".


import cgi
import os
import logging
import contextlib
from xml.dom import minidom
from xml.dom.minidom import Document
import exceptions
import warnings
import imghdr
from google.appengine.ext import blobstore
from google.appengine.api import images
from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import blobstore_handlers

import wsgiref.handlers

# START Constants
CONTENT_TYPE_HEADER = "Content-Type"
CONTENT_TYPE_TEXT = "text/plain"
CONTENT_TYPE_PNG = "image/png"
CONTENT_TYPE_JPEG = "image/jpeg"
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
	'000.000.000.000':'v5na39h3uO2aGHoC4gTy5R80eWn3U71Hdqzx',
}

# END Constants

# START Exception Handling
class Error(StandardError):
	pass
class ImageNotFound(Error): #Exception raised when no image is found
	pass
class Forbidden(Error):
	pass

logging.getLogger().setLevel(logging.DEBUG)

@contextlib.contextmanager
def imageExcpHandler(ctx):
	try:
		yield {}
	except (images.LargeImageError, images.BadImageError, images.TransformationError), exc:
		logging.error(exc.message)
		xml_response(ctx, 'app.invalid_image', 'The image provided is too big or corrupt: ' + exc.message)
	except (ImageNotFound), exc:
		logging.error(exc.message)
		xml_response(ctx, 'app.not_found', 'The image requested has not been found: ' + exc.message)
	except (images.NotImageError), exc:
		logging.error(exc.message)
		xml_response(ctx, 'app.invalid_encoding', 'The indicated encoding is not supported, valid encodings are PNG and JPEG: ' + exc.message)
	except (ValueError, images.BadRequestError), exc:
		logging.error(exc.message)
		xml_response(ctx, 'app.invalid_parameters', 'The indicated parameters to manipulate the image are not valid: ' + exc.message)
	except (Forbidden), exc:
		logging.error(exc.message)
		xml_response(ctx, 'app.forbidden', 'You don\'t have permission to perform this action: ' + exc.message)
	except (Exception), exc:
		logging.error(exc.message)
		xml_response(ctx, 'system.other', 'An unexpected error in the web service has happened: ' + exc.message)

def xml_response(handle, response_status, response_msg):
	doc = Document()
	responsecard = doc.createElement("response")
	statuscard = doc.createElement("status")
	messagecard = doc.createElement("message")

	statustext = doc.createTextNode(response_status)
	messagetext = doc.createTextNode(response_msg)

	statuscard.appendChild(statustext)
	messagecard.appendChild(messagetext)

	responsecard.appendChild(statuscard)
	responsecard.appendChild(messagecard)
	doc.appendChild(responsecard)

	handle.response.headers[CONTENT_TYPE_HEADER] = XML_CONTENT_TYPE
	handle.response.out.write(doc.toxml(XML_ENCODING))

# END Exception Handling

# START Helper Methods
def loadModel(model):
	if model.lower() == 'avatar':
		return Avatar
	elif model.lower() == 'photo':
		return Photo
	else:
		raise images.BadRequestError("Unknown type")

def isAuth(ip = None, key = None):
	if AUTH == False:
		return True
	elif AUTH.has_key(ip) and key == AUTH[ip]:
		return True
	else:
		return False

# END Helper Methods

# START Model Definitions
class Avatar(db.Model):
	"""
	Storage for an avatar and its associated metadata.

	Properties:
		img_id: identificator for the avatar
		src_data: original image in full size
		transformed_data: manipulated version of original (ie, cropped, etc)
		thumbnail_data: jpeg format image in thumbnail size
		thumbnail_props: settings to apply when generating thumbnails
		max_dimension: the maximum size for storage - all uploaded will be resized if too large
	"""
	img_id = db.StringProperty()
	src_data = db.BlobProperty()
	transformed_data = db.BlobProperty()
	large_thumbnail_data = db.BlobProperty()
	large_thumbnail_props = {'width':200,'height':200,'type':'PNG'}
	medium_thumbnail_data = db.BlobProperty()
	medium_thumbnail_props = {'width':100,'height':100,'type':'PNG'}
	small_thumbnail_data = db.BlobProperty()
	small_thumbnail_props = {'width':50,'height':50,'type':'PNG'}
	max_dimension = 500

class Photo(db.Model):
	"""
	Storage for a photo and its associated metadata.

	Properties:
		img_id: identificator for the photo
		src_data: original image in full size
		transformed_data: manipulated version of original (ie, cropped, etc)
		thumbnail_data: jpeg format image in thumbnail size
		thumbnail_props: settings to apply when generating thumbnails
		max_dimension: the maximum size for storage - all uploaded will be resized if too large
	"""
	img_id = db.StringProperty()
	src_data = db.BlobProperty()
	transformed_data = db.BlobProperty()
	large_thumbnail_data = db.BlobProperty()
	large_thumbnail_props = {'width':600,'height':600,'type':'JPEG'}
	small_thumbnail_data = db.BlobProperty()
	small_thumbnail_props = {'width':50,'height':50,'type':'JPEG'}
	max_dimension = 800

# END Model Definitions

# START Request Handlers
class Upload(webapp.RequestHandler):
	def post(self, model):
		"""
		Uploads an image to be processed.

		Returns image key

		Args:
			model: (required) string of the model name in which to store the image (ie, avatar, photo)

		POST Args:
		  api_key: (required) the api key specified in the dictionary defined in the constants
			img_id: (required) user defined identifier for the specific image

			One (and only one) of the following is required
			image: the image file that it is being uploaded (< 1mb)
				OR
			blob_key: a key from an existing image being stored in the blobstore api (> 1mb)
		"""
		with imageExcpHandler(self):
			# check authorised
			if isAuth(self.request.remote_addr,self.request.get('api_key')) == False:
				raise Forbidden("Invalid Credentials")

			logging.debug('uploading')

			# read data from request
			user_id = cgi.escape(self.request.get('user_id'))
			img_id = cgi.escape(self.request.get('img_id'))

			# choose which path based on provided params
			args = self.request.arguments()
			logging.debug(args)
			logging.debug(img_id)

			if 'image' in args: # path 1 - image < 1mb
				logging.debug('path 1 - normal upload')
				img_data = self.request.POST.get('image').file.read()
				img = images.Image(img_data)

				# check its an accepted image type
				img_type = imghdr.what('filename', img_data)
				if img_type != 'png' and img_type != 'jpeg':
					raise images.NotImageError("Unknown image file type")
			elif 'blob_key' in args: 	# path 2 - image was > 1mb therefore uploaded to blobstore
				logging.debug('path 2 - blobstore api')
				blob_key = self.request.get("blob_key")
				blob_info = blobstore.get(blob_key)
				img = images.Image(blob_key=blob_key)

				# check its an accepted image type
				img_type = blob_info.content_type
				logging.debug('img_type: '+img_type)

				if img_type == "image/jpeg" or img_type == "image/jpg":
					img_type = 'jpeg'
				elif img_type == "image/png" or img_type == "image/x-png":
					img_type = 'png'
				else:
					logging.debug('Image type not recognised, assuming JPEG')
					img_type = 'jpeg'

			else: # neither path - no image or blob_key specified
				raise Exception("No image provided/specified")

			# set the image model to use
			ImageModel = loadModel(model)

			# generate source data by resizing to model max dimension prop if the image is larger
			max_d = ImageModel.max_dimension
			# blobstore images don't have width or height props, however because they are using the
			# 	blobstore it is assumed that they are large files which are most likely bigger than the
			# 	max dimension - seeking any better ideas on approaching this
 			if 'blob_key' in args or img.width > max_d or img.height > max_d:
				logging.debug('resizing to generate src_data (image > max_dimension)')
				img.resize(width = max_d, height = max_d)
				src_data = img.execute_transforms(eval('images.' + img_type.upper()))
			else:
				logging.debug('directly using img as src_data (image < max_dimension)')
				img.resize(width = img.width, height = img.height)
				src_data = img.execute_transforms(eval('images.' + img_type.upper()))

			# generate thumbnails only if they are part of the model properties
			props = ImageModel.properties()

			large_thumbnail_data = None
			if 'large_thumbnail_data' in props:
				img.resize(ImageModel.large_thumbnail_props['width'], ImageModel.large_thumbnail_props['height'])
				large_thumbnail_data = img.execute_transforms(eval('images.' + ImageModel.large_thumbnail_props['type']))

			medium_thumbnail_data = None
			if 'medium_thumbnail_data' in props:
				img.resize(ImageModel.medium_thumbnail_props['width'], ImageModel.medium_thumbnail_props['height'])
				medium_thumbnail_data = img.execute_transforms(eval('images.' + ImageModel.medium_thumbnail_props['type']))

			small_thumbnail_data = None
			if 'small_thumbnail_data' in props:
				img.resize(ImageModel.small_thumbnail_props['width'], ImageModel.small_thumbnail_props['height'])
				small_thumbnail_data = img.execute_transforms(eval('images.' + ImageModel.small_thumbnail_props['type']))

			# check if an image with that id already exists and delete it
			query = ImageModel.all(keys_only=True) # true means retrieve keys only
			query.filter('img_id = ', img_id)
			results = query.fetch(limit=1)
			if len(results) > 0:
				db.delete(results)

			# add new image
			# note: adding the null thumbnail data values on properties that don't exist on the model
			# 	does not affect the saving process
			reference = ImageModel(
													img_id = img_id,
													user_id = user_id,
													src_data = src_data,
													large_thumbnail_data = large_thumbnail_data,
													medium_thumbnail_data = medium_thumbnail_data,
													small_thumbnail_data = small_thumbnail_data
												).put()

			# delete blobstore object to prevent being orphaned
			if 'blob_key' in args:
				blobstore.delete(blob_key)

			# return the auto generated GAE UUID for the image stored
			xml_response(self, 'app.success', str(reference))


class View(webapp.RequestHandler):
	def get(self, model, display_type, img_id):
		"""
		Serves an image from the datastore based on the model, display_type and img_id.

		Args:
			model: (required) string of the model name in which to retrieve the image from (ie, avatar, photo)
			display_type: (required) a string describing the type of image to serve (image or thumbnail)
			img_id: (required) user defined identifier for the specific image

		"""
		with imageExcpHandler(self):
			# set the image model to use
			ImageModel = loadModel(model)

			# pull image from database
			query = ImageModel.all()
			query.filter('img_id = ', img_id)
			results = query.fetch(limit = 1)
			if len(results) == 0:
				raise ImageNotFound("No existing image with image id")
			image = results[0]

			if display_type == 'source':
				img_data = image.src_data
			elif display_type == 'image':
				img_data = image.transformed_data
				if img_data == None:
					img_data = image.src_data
			elif display_type == 'large':
				img_data = image.large_thumbnail_data
			elif display_type == 'medium':
				img_data = image.medium_thumbnail_data
			elif display_type == 'small':
				img_data = image.small_thumbnail_data
			else:
				raise images.BadRequestError

			img_type = imghdr.what('filename',img_data)
			if(img_type == 'png'):
				self.response.headers[CONTENT_TYPE_HEADER] = CONTENT_TYPE_PNG
			else:
				self.response.headers[CONTENT_TYPE_HEADER] = CONTENT_TYPE_JPEG
			self.response.out.write(img_data)

class Manipulate(webapp.RequestHandler):
	def get(self, task, model):
		"""
		Identifies the type of operation to be done, and passes flow to the appropriate function

		Args:
			model: (required) string of the model name in which to retrieve the image from (ie, avatar, photo)
			task: (required) a string describing the task to perform (ie, resize, crop)

		POST Args
		  api_key: (required) the api key specified in the dictionary defined in the constants
			img_id: (required) user defined identifier for the specific image

		Extra POST Args (resize) - Read descriptions in "def resize(self, image):"
			width,height,unit

		Extra POST Args (crop) - Read descriptions in "def crop(self, image):"
			x1,y1,x2,y2,unit
		"""
		with imageExcpHandler(self):
			# check authorised
			if isAuth(self.request.remote_addr,self.request.get('api_key')) == False:
				raise Forbidden("Invalid Credentials")

			# get data
			img_id = cgi.escape(self.request.get('img_id'))

			# set the image model to use
			ImageModel = loadModel(model)

			# find the image from datastore
			query = ImageModel.all()
			query.filter('img_id = ', img_id)
			results = query.fetch(limit=1)
			if len(results) == 0:
				raise ImageNotFound("No existing image with image id")
			image = results[0]

			# perform manipulation task
			if 'resize' == cgi.escape(task.lower()):
				transformed = self.resize(image.src_data)
			elif 'crop' == cgi.escape(task.lower()):
				transformed = self.crop(image.src_data)

			image.transformed_data = transformed

			thumbnail = images.Image(transformed)

			props = ImageModel.properties()

			large_thumbnail_data = None
			if 'large_thumbnail_data' in props:
				thumbnail.resize(ImageModel.large_thumbnail_props['width'], ImageModel.large_thumbnail_props['height'])
				image.large_thumbnail_data = thumbnail.execute_transforms(eval('images.' + ImageModel.large_thumbnail_props['type']))

			medium_thumbnail_data = None
			if 'medium_thumbnail_data' in props:
				thumbnail.resize(ImageModel.medium_thumbnail_props['width'], ImageModel.medium_thumbnail_props['height'])
				image.medium_thumbnail_data = thumbnail.execute_transforms(eval('images.' + ImageModel.medium_thumbnail_props['type']))

			small_thumbnail_data = None
			if 'small_thumbnail_data' in props:
				thumbnail.resize(ImageModel.small_thumbnail_props['width'], ImageModel.small_thumbnail_props['height'])
				image.small_thumbnail_data = thumbnail.execute_transforms(eval('images.' + ImageModel.small_thumbnail_props['type']))

			reference = image.put()

			xml_response(self, 'app.success', str(reference))

	def resize(self, image):
		"""
		Resizes an image based on specified width/height (maintaining aspect ratio - see below)

		NOTE: From http://code.google.com/appengine/docs/python/images/imageclass.html#Image_resize
		Resizes an image, scaling down or up to the given width and height. The resize transform preserves
		the aspect ratio of the image. If both the width and the height arguments are provided, the transform
		uses the dimension that results in a smaller image.

		Args:
			image: image file that has been retrieved from datastore

		POST Args:
			width: width to resize the image (pixels or percentage based on unit)
			height: height to resize the image (pixels or percentage based on unit)
			unit: 'pixels' or 'percentage' to indicate the type of measurement provided for width & height
		"""
		width = float(cgi.escape(self.request.get('width')))
		height = float(cgi.escape(self.request.get('height')))
		unit = cgi.escape(self.request.get('unit'))

		# determine image type
		img_type = imghdr.what('filename',image)
		if(img_type == 'png'):
			output_encoding = images.PNG
		else:
			output_encoding = images.JPEG

		img = images.Image(image)
		if unit == 'pixels':
			img.resize(width = int(width), height = int(height))
		elif unit == 'percentage':
			img.resize(width = int(img.width * width), height = int(img.height * height))
		else:
			raise images.BadRequestError("unit must be 'pixels' or 'percentage'")

		transformed = img.execute_transforms(output_encoding)
		return transformed

	def crop(self, image):
		"""
		Crops an image based on specified pixels/percentage

		Args:
			image: image file that has been retrieved from datastore

		POST Args
			x1,y1,x2,y2:
				If unit is 'percentage' - proportion of the image width/height specified as a float value from 0.0 to 1.0 (inclusive).
				If unit is 'pixels' - coordinate within image width/height specified as a pixel value (inclusive).

			unit: 'pixels' or 'percentage' to indicate the type of measurement provided for x1,y1,x2,y2
		"""
		x1 = float(cgi.escape(self.request.get('x1')))
		y1 = float(cgi.escape(self.request.get('y1')))
		x2 = float(cgi.escape(self.request.get('x2')))
		y2 = float(cgi.escape(self.request.get('y2')))
		unit = cgi.escape(self.request.get('unit'))

		# determine image type
		img_type = imghdr.what('filename',image)
		if(img_type == 'png'):
			output_encoding = images.PNG
		else:
			output_encoding = images.JPEG

		img = images.Image(image)
		if unit == 'pixels':
			img.crop(x1/img.width,y1/img.height,x2/img.width,y2/img.height)
		elif unit == 'percentage':
			img.crop(x1,y1,x2,y2)
		else:
			raise images.BadRequestError("unit must be 'pixels' or 'percentage'")

		transformed = img.execute_transforms(output_encoding)
		return transformed


# Gets a url to post a large file to
class BlobstoreUrl(webapp.RequestHandler):
	def post(self):
		# check authorised
		if isAuth(self.request.remote_addr,self.request.get('api_key')) == False:
			raise Forbidden("Invalid Credentials")

		upload_url = blobstore.create_upload_url('/blobstore/upload')
		xml_response(self, 'app.success', upload_url)

# Send a POST request to upload your file
class BlobstoreUpload(blobstore_handlers.BlobstoreUploadHandler):
	def post(self):
		# check authorised
		#if isAuth(self.request.remote_addr,self.request.get('api_key')) == False:
		#	raise Forbidden("Invalid Credentials")

		upload_files = self.get_uploads()
		blob_info = upload_files[0]
		logging.info(blob_info.key())
		self.redirect('/blobstore/response/%s' % blob_info.key()) # has to return 301, 302, 303

class BlobstoreResponse(webapp.RequestHandler):
	def get(self, blob_key):
		xml_response(self, 'app.success', blob_key)

# END Request Handlers

# START Application
application = webapp.WSGIApplication([
																			 ('/upload/(avatar|photo)', Upload),
																			 ('/(resize|crop)/(avatar|photo)', Manipulate),
																			 ('/view/(avatar|photo)/(large|medium|small|image|source)/([-\w]+)', View),
																			 ('/blobstore/url', BlobstoreUrl),
																			 ('/blobstore/upload', BlobstoreUpload),
																			 ('/blobstore/response/([^/]+)?', BlobstoreResponse)
																		 ],debug=True)

def main():
	run_wsgi_app(application)

if __name__ == '__main__':
	main()

# END Application