# -*- coding: utf8 -*-
__version__ = "$Revision$ $Date$"
__author__  = "Guillaume Bour <guillaume@bour.cc>"
__license__ = """
	Copyright (C) 2010, Guillaume Bour <guillaume@bour.cc>

	This program is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; version 3 of the License

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License along
	with this program; if not, write to the Free Software Foundation, Inc.,
	51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA..
"""
import traceback, cjson, inspect

from twisted.web.resource   import Resource, NoResource
from twisted.web            import server

from mother.callable import Callable

CONTENTTYPE_JSON = 'application/json'
def query_builder(method, func):
	(ARGS, VAARGS, KWARGS, DFTS) = inspect.getargspec(func)

	if DFTS:
		ARGS = ARGS[:-len(DFTS)]
	if len(ARGS) > 0 and ARGS[0] == 'self':
		del ARGS[0]
		
	def pre_QUERY(request):
		print 'pre_QUERY', func.__name__, func.__callable__
		code	= 200
		msg	 = None
		argmap  = {}
		
		content_type = request.getHeader('content-type')
		if method in ['PUT', 'POST']:
			argmap['content'] = request.content

			if content_type == CONTENTTYPE_JSON:
				argmap['content'] = cjson.decode(argmap['content'].read())
			
		# url params precedes on content json data
		for arg in request.args.iterkeys():
			#CHECK: arg is a list only when has multiple values
			argmap[arg] = request.args[arg] #[0]

		if 'method' in ARGS:
			argmap['method'] = method
		if 'request' in ARGS:
			argmap['request'] = request
			
		for arg in ARGS:
			if arg not in argmap:
				code = 400
				msg  = "missing %s parameter" % arg
				break


		value = ''; ret = None
		if code == 200:
			ret = func(**argmap)
			if isinstance(ret, tuple):
				(code, value) = ret
			else:
				(code, value) = (200, ret)

		if ret == server.NOT_DONE_YET:
			return ret

		request.setResponseCode(code, msg)
		if content_type == CONTENTTYPE_JSON:
			value = cjson.encode(value)
		else:
			value = str(value)
		return value
	 
	return pre_QUERY
	
	
class ClassNode(Resource):
	def __init__(self, inst=None, leaf=False):
		Resource.__init__(self)
		self.isLeaf   = leaf

		self.instance   = inst
		self.isCallable = isinstance(inst, Callable)

		if not isinstance(inst, Callable):
			return

		for method in ('GET', 'PUT', 'DELETE'):
			if hasattr(inst, method) and inspect.ismethod(getattr(inst, method)):
				setattr(self, 'render_%s' % method, query_builder(method, getattr(inst, method)))

class FuncNode(Resource):
	def __init__(self, func):
		Resource.__init__(self)
		self.isLeaf = True

		self.func  = func
		self.url   = func.__callable__.get('url', func.__callable__['_url'])

		# possible methods are GET, PUT, DELETE
		for method in func.__callable__['method']:
			setattr(self, 'render_%s' % method, query_builder(method, func))

	def __repr__(self):
		return 'FuncNode(%s)' % self.func.__name__

class PluginNode(Resource):
	def __init__(self, plugin):
		Resource.__init__(self)

		self.plugin = plugin

	#def set_callback(self, func):
	#	for method in func.__callable__['method']:
	#		setattr(self, 'render_%s' % method, query_builder(method, func))

	def render(self, request):
		#print 'PluginNode::render', request.uri
		m = self.plugin.flat_urls.get('/', None)
		if m is None:
			return Resource.render(self, request)

		return m.render(request)

	def getChild(self, path, request):
		print 'PluginNode::getChild', request.uri, path, request.prepath, request.postpath

		uri = '/' + path
		if len(request.postpath) > 0:
			uri += '/' + '/'.join(request.postpath)
		
		if uri in self.plugin.flat_urls:
			print 'found in flaturi'
			return self.plugin.flat_urls[uri]

		for raw, (rx, target) in self.plugin.regex_urls.iteritems():
			m = rx.match(uri)
			if m is not None:
				# named groups a set as request args
				request.args.update(m.groupdict())
				return target

		# no resource found
		return NoResource('Not Found')
