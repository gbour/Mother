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
		print 'pre_QUERY', func.__name__  #func.__callable__:: Callable class method (GET, ..) is not callback
		code	= 200
		msg	 = None
		argmap  = {}

		# session management
		print 'SESSION=', request.getSession()

		content_type = request.getHeader('content-type')
		print "RCONTENT=", request.content.read()
		#TODO: we should check if content type match default content type or modifiers
		# (case Callable classes)

		#TODO: following bloc is not generic enough. What if we do HTTP POST? 
		if method in ['PUT', 'POST']:
			argmap['content'] = request.content

			if content_type == CONTENTTYPE_JSON:
				argmap['content'] = cjson.decode(argmap['content'].read())
			
		# url params precedes on content json data
		print request.args
		for arg in request.args.iterkeys():
			#CHECK: arg is a list only when has multiple values
			#NOTE: 
			#  . url.path args are single items (string, integer)
			#  . url.query are list (even if has only one value)
			#  POST form args ??
			argmap[arg] = request.args[arg] #[0]
			if isinstance(argmap[arg], list) and len(argmap[arg]) == 1:
				argmap[arg] = argmap[arg][0]

		if 'method' in ARGS:
			argmap['method'] = method
		if 'request' in ARGS:
			argmap['request'] = request
			
		for arg in ARGS:
			if arg not in argmap:
				code = 400
				msg  = "missing %s parameter" % arg
				break

		## GET Application context
		#print func.__module__.split('.', 1)
		appcontext = sys.modules[func.__module__.split('.',1)[0]].CONTEXT
		#print "AppContext=", appcontext

		#TODO: this is not correct, has it doesn't work when we have simultaneous	requests
		# !! FOR TESTS ONLY !!
		sys.modules[func.__module__.split('.',1)[0]].SESSION = request.getSession()

		value = ''; ret = None
		if code == 200:
			#print argmap, func
			argmap['__referer__'] = request.getHeader('referer')

			_func = func
			if request.raw_content_type in modifiers:
				argmap['__callback__'] = func
				_func = modifiers[request.raw_content_type]

			print 'BEF CALL', request.uri, _func, argmap, request.getAllHeaders()
			ret = _func(**argmap)
			#print "RET=", ret


			if   isinstance(ret, template.Template):
				value = appcontext.render(ret)
				code  = 200
			elif isinstance(ret, routing.Redirect):
				print "REDIRECT TO", ret.url
				#TODO: code is not correctly set
				request.setResponseCode(ret.code)
				request.redirect(ret.url)
				#request.finish()
				return ''

			elif isinstance(ret, type) and issubclass(ret, routing.HTTPCode):
				print "return", ret
				request.setResponseCode(ret.code, None)
				# SHOULD return TemplateNode
				ret = appcontext.app.PLUGIN.flat_urls[(ret,'text/html')]#.get(ret, None)
				print 'ret=', ret
				#TODO: ret MAY be template, or static file
				# we must handle all cases
				value = ''
				if ret is not None:
					# we do the test with a template
					value = appcontext.render(ret.tmpl)
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
				print "MODIFIERS", method, "=", modifiers
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
		#print 'PluginNode::render', request.uri
		from twisted.web2 import http_headers
		head = http_headers.Headers(handler=http_headers.DefaultHTTPHandler)
		head.setRawHeaders('Accept', (request.getHeader('Accept'),))
		accept = head.getHeader('Accept')
		accept = sorted([(mime, prio) for mime, prio in accept.iteritems()], key=lambda	x: -x[1])
		print 'accept=', accept, accept[0]

		if self.plugin.flat_urls.hasURL('/'):
			urls = self.plugin.flat_urls.getURL('/')
			for ctype, weight in accept:
				ctype = '%s/%s' % (ctype.mediaType, ctype.mediaSubtype)
				if ctype in urls:
					request.raw_content_type = ctype
					return self.plugin.flat_urls[('/', ctype)].render(request)

		return Resource.render(self, request)
		"""
		m = self.plugin.flat_urls.get('/', None)
		if m is None:
			return Resource.render(self, request)

		return m.render(request)
		"""

	def getChild(self, path, request):
		print 'PluginNode::getChild', request.uri, path, request.prepath, request.postpath

		# path may be LOGIN (auth)
		if isinstance(path, str):
			uri = '/' + path
			if len(request.postpath) > 0:
				uri += '/' + '/'.join(request.postpath)
		else:
			uri = path

		print 'uri=', uri
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
		print 'accept=', accept, accept[0]

		if self.plugin.flat_urls.hasURL(uri):
			print 'found in flaturi' #, self.plugin.flat_urls[uri]
			urls = self.plugin.flat_urls.getURL(uri)
			print urls
			for ctype, weight in accept:
				ctype = '%s/%s' % (ctype.mediaType, ctype.mediaSubtype)
				print ctype
				if ctype in urls:
					print 'FOUND:', uri, ctype
					(request.raw_content_type, resource) = self.plugin.flat_urls.getWithBaseContentType((uri, ctype))
					return resource

			return NoResource('Not Found')

		#TODO: really not optimal
		print '* TESTING rx urls'
		for raw, sub in self.plugin.regex_urls.iteritems():
			print '  .', raw, '--', sub
			for ctype, weight in accept:
				ctype = '%s/%s' % (ctype.mediaType, ctype.mediaSubtype)
				print '    - ctype=', ctype
				if ctype in sub:
					(rx, target) = self.plugin.regex_urls[(raw, ctype)]

					m = rx.match(uri)
					if m is not None:
						print '%s MATCH %s' % (uri, raw), target
						print m.groupdict()
						# gamed groups a set as request args
						request.args.update(m.groupdict())

						print 'RETURNING', target, type(target), target.isLeaf,	request.postpath, request.args
						#NOTE: need to empty request.postpath, cause if target is not leaf,
						#twisted will continue until postpath is empty
						if isinstance(target, ClassNode):
							request.postpath=[]

						#TODO: must handle type generalization
						mtype = self.plugin.regex_urls.getMatchContentType(raw, ctype)
						print request.postpath, ',mtype=', mtype
						#request.raw_content_type = ctype
						request.raw_content_type = mtype
						return target

		"""
		for raw, (rx, target) in self.plugin.regex_urls.iteritems():
			m = rx.match(uri)
			if m is not None:
				print '%s MATCH %s' % (uri, raw), target
				# gamed groups a set as request args
				request.args.update(m.groupdict())

				return target
		"""
		# no resource found
		print "NO RESOURCE FOUND"
		"""
		if routing.HTTP_404 in self.plugin.flat_urls:
			return self.plugin.flat_urls[routing.HTTP_404]
		"""
		if self.plugin.flat_urls.hasURL(routing.HTTP_404):
			urls = self.plugin.flat_urls.getURL(routing.HTTP_404)
			for ctype, weight in accept:
				ctype = '%s/%s' % (ctype.mediaType, ctype.mediaSubtype)
				if ctype in urls:
					print 'RES=', self.plugin.flat_urls[(routing.HTTP_404, ctype)]
					return self.plugin.flat_urls[(routing.HTTP_404, ctype)]


		return NoResource('Not Found')
