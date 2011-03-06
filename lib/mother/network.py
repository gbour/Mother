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
import sys, traceback, cjson, inspect

from twisted.web.resource   import Resource, NoResource
from twisted.web            import server

from mother.callable        import Callable
from mother                 import template, routing

CONTENTTYPE_JSON = 'application/json'
def query_builder(method, func, modifiers={}, pre={}, instance=None):
	(ARGS, VAARGS, KWARGS, DFTS) = inspect.getargspec(func)

	if DFTS:
		ARGS = ARGS[:-len(DFTS)]
	if len(ARGS) > 0 and ARGS[0] == 'self':
		del ARGS[0]
		
	def pre_QUERY(request):
		code	= 200
		msg	 = None
		argmap  = {}

		# session management
		content_type = request.getHeader('content-type')
		#TODO: we should check if content type match default content type or modifiers
		# (case Callable classes)

		#TODO: following bloc is not generic enough. What if we do HTTP POST? 
		if method in ['PUT', 'POST']:
			argmap['content'] = request.content

			if content_type == CONTENTTYPE_JSON:
				argmap['content'] = cjson.decode(argmap['content'].read())
			
		# url params precedes on content json data
		for key, val in request.args.iteritems():
			#NOTE: args values are always a list (even with single value)
			#      i.e: a=1&b=2&c=3&c=4 give {'a':[1], 'b':[2], 'c':[3,4]}
			# 
			#      rx-url mapped values are NOT list, but single string value
			#       but code also work for string
			if isinstance(val, (list, tuple)):
				val= [v.decode('utf8','replace') for v in val]
				if len(val) == 1:
					val = val[0]
			else:
				val = val.decode('utf8','replace')
			argmap[key] = val
			argmap[arg] = unicode(argmap[arg])

		if 'method' in ARGS:
			argmap['method'] = method
		if 'request' in ARGS:
			argmap['request'] = request
			
		for arg in ARGS:
			if not arg.startswith('__') and arg not in argmap:
				code = 400
				msg  = "missing %s parameter" % arg
				break

		## GET Application context
		appcontext = sys.modules[func.__module__.split('.',1)[0]].CONTEXT

		#TODO: this is not correct, has it doesn't work when we have simultaneous	requests
		# !! FOR TESTS ONLY !!
		sys.modules[func.__module__.split('.',1)[0]].SESSION = request.getSession()

		value = ''; ret = None
		if code == 200:
			argmap['__referer__'] = request.getHeader('referer')

			_func = func
			if request.raw_content_type in modifiers:
				argmap['__callback__'] = func
				_func = modifiers[request.raw_content_type]

			#DEBUG
			argmap['__context__'] = request
			print "calling handler:: argmap=", argmap, request.raw_content_type
			ret = _func(**argmap)


			if   isinstance(ret, template.Template):
				value = appcontext.render(ret)
				code  = 200
			elif isinstance(ret, routing.Redirect):
				#TODO: code is not correctly set
				request.setResponseCode(ret.code)
				request.redirect(ret.url)
				#request.finish()
				return ''

			elif isinstance(ret, type) and issubclass(ret, routing.HTTPCode):
				request.setResponseCode(ret.code)

				value = ''
				if request.raw_content_type == 'text/html':
					# SHOULD return TemplateNode
					ret = appcontext.app.PLUGIN.flat_urls[(ret,'text/html')]#.get(ret, None)
					#TODO: ret MAY be template, or static file
					# we must handle all cases
					if ret is not None:
						# we do the test with a template
						value = appcontext.render(ret.tmpl)
				else:
					import cjson
					value = cjson.encode(ret.msg)
				return value

			elif isinstance(ret, routing.HTTPCode):
				request.setResponseCode(ret.code, ret.msg)
				import cjson
				value = cjson.encode(ret.msg)
				ret = appcontext.app.PLUGIN.flat_urls.get(ret, None)
				#TODO: ret MAY be template, or static file
				# we must handle all cases
				#value = ''
				if ret is not None:
					# we do the test with a template
					value = appcontext.render(ret)
				return value


			elif isinstance(ret, tuple):
				(code, value) = ret
			else:
				(code, value) = (200, ret)

		if ret == server.NOT_DONE_YET:
			return ret


		request.setResponseCode(code, msg)

		#if content_type == CONTENTTYPE_JSON:
		#	value = cjson.encode(value)
		#else:
		value = str(value)
		#print code, value
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

		for method in ('HEAD', 'GET', 'POST', 'PUT', 'DELETE'):
			if hasattr(inst, method) and inspect.ismethod(getattr(inst, method)):
				modifiers = getattr(inst, method).__dict__.get('__callable__', dict()).get('modifiers', dict())
				modifiers.update(inst.__modifiers__)
				pre = getattr(inst, method).__dict__.get('__callable__', dict()).get('pre', dict())

				setattr(self, 'render_%s' % method, query_builder(method, getattr(inst,
					method), modifiers, pre, instance=inst))


	def auth(self):
		return True


class FuncNode(Resource):
	def __init__(self, func):
		Resource.__init__(self)
		self.isLeaf = True

		self.func  = func
		self.url   = func.__callable__.get('url', func.__callable__['_url'])
		self.modifiers = func.__callable__.get('modifiers', dict())

		# possible methods are GET, PUT, DELETE
		for method in func.__callable__['method']:
			setattr(self, 'render_%s' % method, query_builder(method, func,	self.modifiers))

	def __repr__(self):
		return 'FuncNode(%s)' % self.func.__name__

	def auth(self):
		return True


class TemplateNode(Resource):
	#TODO: use twisted.web.ErrorPage as base
	def __init__(self, module, tmpl):
		Resource.__init__(self)

		self.module = module
		self.tmpl   = tmpl

	def render_GET(self, request):
		appcontext = self.module.CONTEXT

		#TODO: generic
		request.setResponseCode(404)
		return appcontext.render(self.tmpl)

	def getChild(self, name, request):
		return self

	def auth(self):
		return True

class PluginNode(Resource):
	def __init__(self, plugin):
		Resource.__init__(self)

		self.plugin = plugin

	#def set_callback(self, func):
	#	for method in func.__callable__['method']:
	#		setattr(self, 'render_%s' % method, query_builder(method, func))

	def render(self, request):
		from twisted.web2 import http_headers
		head = http_headers.Headers(handler=http_headers.DefaultHTTPHandler)
		head.setRawHeaders('Accept', (request.getHeader('Accept'),))
		accept = head.getHeader('Accept')
		accept = sorted([(mime, prio) for mime, prio in accept.iteritems()], key=lambda	x: -x[1])

		if self.plugin.flat_urls.hasURL('/'):
			urls = self.plugin.flat_urls.getURL('/')
			for ctype, weight in accept:
				ctype = '%s/%s' % (ctype.mediaType, ctype.mediaSubtype)
				if ctype in urls:
					request.raw_content_type = ctype
					return self.plugin.flat_urls[('/', ctype)].render(request)

		return Resource.render(self, request)

	def getChild(self, path, request):
		# path may be LOGIN (auth)
		if isinstance(path, str):
			uri = '/' + path
			if len(request.postpath) > 0:
				uri += '/' + '/'.join(request.postpath)
		else:
			uri = path

		from twisted.web2 import http_headers

		# hot-patching web2.http_headers.MimeType
		def mime_neq(self, other):
			if not isinstance(other, http_headers.MimeType): return NotImplemented

			return not (self.mediaType == other.mediaType and
				self.mediaSubtype == other.mediaSubtype and
				self.params == other.params)
		http_headers.MimeType.__ne__ = mime_neq

		head = http_headers.Headers(handler=http_headers.DefaultHTTPHandler)
		from odict import odict
		head.handler.updateParsers({'Accept': (http_headers.tokenize,http_headers.listParser(http_headers.parseAccept), odict)})
		head.setRawHeaders('Accept', (request.getHeader('Accept'),))
		accept = head.getHeader('Accept')
		accept = sorted([(mime, prio) for mime, prio in accept.iteritems()], key=lambda	x: -x[1])

		if self.plugin.flat_urls.hasURL(uri):
			urls = self.plugin.flat_urls.getURL(uri)
			for ctype, weight in accept:
				ctype = '%s/%s' % (ctype.mediaType, ctype.mediaSubtype)
				if ctype in urls:
					(request.raw_content_type, resource) = self.plugin.flat_urls.getWithBaseContentType((uri, ctype))
					return resource

			return NoResource('Not Found')

		#TODO: really not optimal
		for raw, sub in self.plugin.regex_urls.iteritems():
			for ctype, weight in accept:
				ctype = '%s/%s' % (ctype.mediaType, ctype.mediaSubtype)
				if ctype in sub:
					(rx, target) = self.plugin.regex_urls[(raw, ctype)]

					m = rx.match(uri)
					if m is not None:
						# gamed groups a set as request args
						request.args.update(m.groupdict())

						#NOTE: need to empty request.postpath, cause if target is not leaf,
						#twisted will continue until postpath is empty
						if isinstance(target, ClassNode):
							request.postpath=[]

						#TODO: must handle type generalization
						mtype = self.plugin.regex_urls.getMatchContentType(raw, ctype)
						#request.raw_content_type = ctype
						request.raw_content_type = mtype
						return target

		# no resource found
		if self.plugin.flat_urls.hasURL(routing.HTTP_404):
			urls = self.plugin.flat_urls.getURL(routing.HTTP_404)
			for ctype, weight in accept:
				ctype = '%s/%s' % (ctype.mediaType, ctype.mediaSubtype)
				if ctype in urls:
					print 'RES=', self.plugin.flat_urls[(routing.HTTP_404, ctype)]
					return self.plugin.flat_urls[(routing.HTTP_404, ctype)]


		return NoResource('Not Found')

