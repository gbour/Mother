# -*- coding: utf8 -*-
__version__ = "$Revision$ $Date$"
__author__  = "Guillaume Bour <guillaume@bour.cc>"
__license__ = """
	Copyright (C) 2010, Guillaume Bour <guillaume@bour.cc>

	This program is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License along
	with this program; if not, write to the Free Software Foundation, Inc.,
	51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA..
"""
import inspect, types
from urllib import quote_plus as qp

from callable import Callable

ROOT = '/'

def url(plug, target, postfix=None, **kwargs):
	"""Return url of target
		
		target is either a class, method or function.
		Class must subclass Callable, whereas method/function must implement @callback

		Return url as a string
	"""
	#print 'URL=', target, dir(target), target.__module__
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
	#print 'url for', target, dir(target), target.__callable__
	elif hasattr(target, 'im_self') and target.im_self is None:
		target = plug.boundmethod(target)

	if not hasattr(target, '__callable__') or 'url' not in target.__callable__:
		raise Exception('No url for %s' % target)

	if hasattr(target, 'im_class'):
		uri += target.im_class.url

	uri += target.__callable__['url']
	if postfix is not None:		
		#print 'postfix=', postfix
		uri += '/'
		if isinstance(postfix, list) or isinstance(postfix, tuple):
			uri += '/'.join(postfix)
		else:
			uri += '%s' % postfix

	if len(kwargs) > 0:
		qstr = '&'.join(["%s=%s" % (qp(k), qp(kwargs[k])) for k in kwargs])
		uri += '?' + qstr

	return(uri)

class Redirect(object):
	"""Redirect object"""
	def __init__(self, to, code=301):
		self.code = code
		self.to   = to
		self.url  = to if isinstance(to, types.StringTypes) else url(to)

class HTTPCode(object):
	code = -1
	msg  = None

	def __init__(self, msg):
		self.msg = msg

for code in (200, 204, 400, 404, 409, 500):
	exec "class HTTP_%d(HTTPCode): code = %d" % (code, code);


"""	
class HTTP_400(HTTPCode):
	code = 400

class HTTP_404(HTTPCode):
	code = 404

class HTTP_401(HTTPCode):
	code = 401
"""
