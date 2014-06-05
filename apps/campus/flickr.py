'''
Based off of flickrpy
http://code.google.com/p/flickrpy/
'''

from urllib import urlencode, urlopen
from xml.dom import minidom
from django.core.cache import cache
from settings import DEBUG
import os

USER_ID = "36226710@N08"
API_KEY = '9782baf2f495f633d6ef9de6e48a243a'
HOST = 'http://flickr.com'
API = '/services/rest'

_photos = []
def get_photos(page=1):
	"""
	Returns list of Photo objects
	http://www.flickr.com/services/api/flickr.people.getPublicPhotos.html
	"""
	photos = cache.get('photos')
	if photos is not None:
		if DEBUG: print "Flickr - photos cached"
		return photos

	if DEBUG: print "Flickr - grabbing photos"
	method = 'flickr.people.getPublicPhotos'
	data = _doget(method, user_id=USER_ID, per_page=500, page=page, extras="tags,description,date_taken,o_dims,path_alias,url_t,url_sq,url_s,url_m,url_l,url_z")
	if hasattr(data.rsp.photos, "photo"): # Check if there are photos at all (may be been paging too far).
		if isinstance(data.rsp.photos.photo, list):
			for photo in data.rsp.photos.photo:
				_photos.append(photo)
		else:
			_photos.append(data.rsp.photos.photo)

		#recursive call to grab all the photos
		if hasattr(data.rsp.photos, "pages") and page < int(data.rsp.photos.pages):
			return get_photos(page+1)

	cache.set('photos', _photos, 24*60*60)
	return _photos

def _doget(method, auth=False, **params):
	#uncomment to check you aren't killing the flickr server
	#print "***** do get %s" % method

	params = _prepare_params(params)
	url = '%s%s/?api_key=%s&method=%s&%s'% \
		  (HOST, API, API_KEY, method, urlencode(params))

	if DEBUG:
		print "Pulling photos: ", url

	return _get_data(minidom.parse(urlopen(url)))

def _prepare_params(params):
	"""Convert lists to strings with ',' between items."""
	for (key, value) in params.items():
		if isinstance(value, list):
			params[key] = ','.join([item for item in value])
	return params

def _get_data(xml):
	"""Given a bunch of XML back from Flickr, we turn it into a data structure
	we can deal with (after checking for errors)."""
	data = unmarshal(xml)
	if not data.rsp.stat == 'ok':
		msg = "ERROR [%s]: %s" % (data.rsp.err.code, data.rsp.err.msg)
		raise FlickrError, msg
	return data


class Photo: pass

#unmarshal taken and modified from pyamazon.py
#makes the xml easy to work with
def unmarshal(element):
	rc = Photo()
	if isinstance(element, minidom.Element):
		for key in element.attributes.keys():
			setattr(rc, key, element.attributes[key].value)

	childElements = [e for e in element.childNodes \
					 if isinstance(e, minidom.Element)]
	if childElements:
		for child in childElements:
			key = child.tagName
			if hasattr(rc, key):
				if type(getattr(rc, key)) <> type([]):
					setattr(rc, key, [getattr(rc, key)])
				setattr(rc, key, getattr(rc, key) + [unmarshal(child)])
			elif isinstance(child, minidom.Element) and \
					 (child.tagName == 'Details'):
				# make the first Details element a key
				setattr(rc,key,[unmarshal(child)])
				#dbg: because otherwise 'hasattr' only tests
				#dbg: on the second occurence: if there's a
				#dbg: single return to a query, it's not a
				#dbg: list. This module should always
				#dbg: return a list of Details objects.
			else:
				setattr(rc, key, unmarshal(child))
	else:
		#jec: we'll have the main part of the element stored in .text
		#jec: will break if tag <text> is also present
		text = "".join([e.data for e in element.childNodes \
						if isinstance(e, minidom.Text)])
		setattr(rc, 'text', text)
	return rc

if __name__ == "__main__":
	photos = get_photos()
	print len(photos)
