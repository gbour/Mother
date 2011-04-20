# -*- coding: utf8 -*-
__version__ = "$Revision$ $Date$"
__author__  = "Guillaume Bour <guillaume@bour.cc>"
__license__ = """
	Copyright (C) 2010-2011, Guillaume Bour <guillaume@bour.cc>

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU Affero General Public License as
	published by the Free Software Foundation, version 3.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU Affero General Public License for more details.

	You should have received a copy of the GNU Affero General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import inspect, types, re, urllib
from urllib import quote_plus as qp

from callable import Callable

ROOT = '/'

def url(plug, target, postfix=None, **kwargs):
	"""Return url of target
		
		target is either a class, method or function.
		Class must subclass Callable, whereas method/function must implement @callback

		Return url as a string
	"""
	if inspect.ismodule(target):
		return '/%s' % target.__name__.rsplit('.', 1)[0].replace('.','/')

	## 
	#TODO: need to be reviewed
	uri = '/%s' % target.__module__.rsplit('.', 1)[0].replace('.','/') 

	#TODO: handle sub-module urls
	#

	# target is a Callable class
	if inspect.isclass(target) and issubclass(target, Callable):
		target = plug.classinstance(target)

		#FAKE
		target.__callable__ = {'url': target.url}

	# bounding method
	#NOTE: suboptimal (cloned from pluggable.py)
	elif hasattr(target, 'im_self') and target.im_self is None:
		target = plug.boundmethod(target)

	if not hasattr(target, '__callable__') or 'url' not in target.__callable__:
		raise Exception('No url for %s' % target)

	if hasattr(target, 'im_class'):
		uri += target.im_class.url

	target_part = str(target.__callable__['url'])
	# uri can contains regex: i.e /a/b/{plop} 
	def rxmap(m):
		key = m.group(0)[1:-1]
		value = kwargs[key]
		del kwargs[key]

		if isinstance(value, (list, tuple)):
				value = ''.join(value)
		return value

	uri += re.sub("\{.*?\}", rxmap, target_part)
	def un_unicode(_str):
		if isinstance(_str, unicode):
			_str = _str.encode('utf8')
		return str(_str)

	if postfix is not None:		
		uri += '/'
		if isinstance(postfix, list) or isinstance(postfix, tuple):
			uri += '/'.join(urllib.quote(un_unicode(postfix)))
		else:
			uri += urllib.quote(un_unicode(postfix))

	def mergeargs(key, value):
		key = qp(k)
		if isinstance(value, (tuple, list)):
			return '&'.join("%s=%s" % (key, qp(un_unicode(v))) for v in value)

		return "%s=%s" % (key, qp(un_unicode(value)))

	if len(kwargs) > 0:
		qstr = '&'.join([mergeargs(k, v) for k,v in kwargs.iteritems()])
		uri += '?' + qstr

	return(uri)


def fromurl(url):
	"""Return app/class/method/function pointed by an url

		1. raise ValueError if url is external
		2. return None      if url does not match any callable app/class/...

		else return target item
	"""
	if re.find('[^\w/-+#]', url):
		raise ValueError

	target = None
	for part in url.split('/'):
		pass
	#aaa/bb/cc/dd

	return 


class Redirect(object):
	"""Redirect object"""
	def __init__(self, to, code=301):
		self.code = code
		self.to   = to

		if isinstance(to, str):
			self.url = to
		elif isinstance(to, unicode):
			self.url = to.encode('utf8')
		else:
			self.url = url(to)


class MetaHTTPCode(type):
	def __str__(cls):
		return '/' + str(cls.code)


class HTTPCode(object):
	__metaclass__ = MetaHTTPCode
	code = -1
	msg  = None

	def __init__(self, msg, content=None):
		#TODO: remove msg (replaced by content)
		self.msg     = msg
		self.content = content

	def __repr__(self):
		return "%s(%s)" % (self.__class__.__name__, self.msg)


for code in (200, 204, 400, 401, 403, 404, 409, 500, 501, 503):
	exec "class HTTP_%d(HTTPCode): code = %d" % (code, code);


"""	
class HTTP_400(HTTPCode):
	code = 400

class HTTP_404(HTTPCode):
	code = 404

class HTTP_401(HTTPCode):
	code = 401
"""

class ActionURL(object):
	pass


class LOGIN(ActionURL):
	url = '/login'

	def __init__(self, url):
		self.url = url


class LOGOUT(ActionURL):
	url = '/logout'

	def __init__(self, url):
		self.url = url

