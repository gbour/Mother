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

import sys, inspect, types
from tentacles.table import Object, MetaObject

from mother import modifiers

#def callback(fnc):
#	print "callback(%s)" % fnc.__name__
#	fnc.__dict__['__callable__'] = fnc.__name__

#	# we get root module
#	modname = fnc.func_globals['__name__'].split('.',1)[0]
#	module  = sys.modules[modname]

#	if '__callbacks__' not in dir(module):
#		module.__callbacks__ = {}
#	module.__callbacks__[fnc.__name__] = True

#	return fnc

def callback(method='GET', autobind=True, *args, **kwargs):
	print 'CALLBACK =', method, args, kwargs
	def deco(fnc):
		print 'CALLBACK2=', fnc
		# base url. May be overridden if 'name' is set
		kwargs['_url']     = '/' + fnc.__name__ # not necessary. TO REMOVE
		kwargs['method']   = method
		kwargs['autobind'] = autobind #???

		# default content_type is 'text/html'
		if 'content_type' not in kwargs:
			kwargs['content_type'] = ('text/html')

		fnc.__dict__['__callable__'] = kwargs
		#fnc.__dict__['__callable__'] = {
		#	'name': kwargs.get('name', fnc.__name__), 
		#	'method': method
		#}
		return fnc

	# special case where invoking callback as keyword, not function 
	# (@callback instead of @callback())
	print method, type(method)
	if isinstance(method, types.FunctionType):
		fnc	 = method
		method  = ['GET']
		return deco(fnc)
		
	if isinstance(method, str):
		method = (method,)

	print 'ret', deco
	return deco

class CallableBuilder(type):
	def __new__(cls, name, bases, dct):
		print "CallableINIT", name
		if not 'url' in dct:
			dct['url'] = '/' + name.lower()
		elif dct['url'] is not None and not dct['url'].startswith('/'):
			raise Exception("url must start with '/'")

		return type.__new__(cls, name, bases, dct)

class Callable(object):
	#BUG: when class inherit both from Object (db abstraction) and Callable,
	#     only one metaclass __new__() will be executed (ones of the 1st parent class
	#     declared
	#	__metaclass__ = CallableBuilder
	
	#__content_type__ = 'application/json'
	__content_type__ = 'python/object'
	__modifiers__    = {'application/json': modifiers.json}

#class COBBuilder(MetaObject, CallableBuilder):
#	def __new__(cls, name, bases, dct):
#		print "COB::new", name
#		return super(COBBuilder, cls).__new__(cls, name, bases, dct)

#class CallableObject(Object, Callable):
#	__metaclass__ = COBBuilder


class _LoopbackSelf(object):
	def __init__(self, called=None):
		self.called = called

	def __getattr__(self, name):
		if self.called is None:
			return _LoopbackSelf(name)

		self.called += "." + name
		return self

	def __str__(self):
		return "LoopbackSelf(%s)" % self.called

	def __repr__(self):
		return self.__str__()
LoopbackSelf = _LoopbackSelf()
