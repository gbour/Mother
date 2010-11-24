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
	51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import sys, os, os.path, re, sqlite3, inspect, traceback, types
from odict                import odict

from twisted.web.resource import Resource
from twisted.web          import static
from twisted.web.rewrite  import RewriterResource

from tentacles            import *
from tentacles.fields	    import *
from tentacles.queryset   import filter
from mother.network       import *
from mother.context       import AppContext
from mother               import template


class Plugin(Object):
	__stor_name__ = 'pluggable__plugins'

	## database fields
	uuid	        = String(pk=True)
	name	        = String()
	#path          = String()
	active        = Boolean(default=True)

	def __init__(self, *args, **kwargs):
		super(Plugin, self).__init__(*args, **kwargs)
	
		## urls is made of:
		#  . flat urls (exactly match)
		#  . regular expressions
		self.flat_urls		= {}
		self.regex_urls   = odict()

	def addurl(self, url, resource):
		"""Append a new URL resource

			@url: relative to application root. May be:
				- raw url (/my/url)
				- simple regex (/my/{url})
				- true regex   (r'/my/(?<url>[^/]+))
				- HTTPCode class
		"""
		store = self.flat_urls

		if isinstance(url, types.StringTypes):
			if isinstance(resource, template.Static):
				#TODO: if resource is file, not directory, we must not change url to match all
				#sub paths/files
				if url.endswith('$'):
					url = url[:-1]
				url += '.*$'

			# compile regex url
			def argmatch(m):
				return '(?P<%s>[^/]*)' % m.group(1)
			_url = re.sub(r'\{(\w*[a-zA-Z-]+\w*)\}', argmatch, url)

			if re.search(r'[([{.*+^$]', _url) != None:
				# url is a regex
				_url     = "^%s$" % _url     # force bounds
				store    = self.regex_urls
				resource = (re.compile(_url), resource)

		store[url] = resource
	
	def objects(self):
		objs = [o for (n, o) in inspect.getmembers(sys.modules[self.name]) if
				inspect.isclass(o) and issubclass(o, Object) and o != Object]
		#print "OBJS=", objs
		return objs


class Pluggable(object):
	def __init__(self, plugin_dir, db, context):
		if not os.path.isdir(plugin_dir):
			raise Exception("plugin directory %s not found" % plugin_dir)
		sys.path.append(plugin_dir)

		# listing plugins
		self.db	 = db
		self.db.create()

		self.context   = context

		self.instances = {}
		self.plugins   = {}

	def initialize(self, root):
		plugins = filter(lambda x: x.active is True, Plugin)
		print plugins

		for plugin in plugins:
			# try import
			try:
				exec "import %s" % plugin.name in {}, {}
			except ImportError, e:
				print "/!\ Cannot import %s plugin:" % plugin.name, e
			print "? plugin %s imported" % plugin.name
			mod = sys.modules[plugin.name]

			mod.CONTEXT = AppContext(mod)
			mod.PLUGIN  = plugin

			plugin.root = PluginNode(plugin)
			root.putChild(plugin.name, plugin.root)
			self.plugins[plugin.name] = plugin

			# check UUID matching
			if mod.UUID != plugin.uuid:
				print "/!\ plugin UUID does not match database one (%s vs %s)" % \
					(plugin.uuid, mod.UUID)
				continue

			# load URL callbacks
			#print "loop on URLS"
			raw_urls = mod.__dict__.get('URLS', {})
			for url, target in raw_urls.iteritems():
				"""Looping on URLs

				we must determine if url is:
				. a raw string		(i.e: /foo/bar)
				. a simple regex  (i.e: /foo/{bar})
				. a full regex		(i.e: /foo/(?<bar>[^/]+))
				"""
				if isinstance(target, static.File):
					plugin.addurl(url, target); continue
				elif isinstance(target, template.Template):
					plugin.addurl(url, TemplateNode(mod, target)); continue
			

				# resolve unbound methods
				if hasattr(target, 'im_self') and target.im_self is None:
					#callback = getattr(self.instances[callback.im_class], callback.__name__)
					#callback = getattr(self.__classinstance(callback.im_class), callback.__name__)
					target = self.boundmethod(target)

				if not hasattr(target, '__callable__'):
					raise Exception('%s is not callable' % inst.__name__)
				elif 'url' in target.__callable__:
					raise Exception("%s url cannot be redefined (is %s, try to set %s)" %\
						(target.__name__, target.__callable__['url'], url))

				#print 'callback=', target
				print 'tt=', target, target.__callable__, url
				target.__callable__['url'] = url
				print 'tt=', target, target.__callable__
				plugin.addurl(url, FuncNode(target))
				"""
				if isinstance(callback, static.File):
					plugin.root.resource.putChild(url, callback)
				elif url == '/':
					# special «root» url
					plugin.root.resource.set_callback(callback)
				else:
					plugin.root.resource.putChild(url, FuncNode(callback))

				plugin.urls[url] = callback
				"""

			# load plugin callbacks
			"""
				mod.__callbacks__ contains callback functions but we don't
				know at wich classes it belongs (cause when decorator is called,
				class methods are not yet binded to its class)
				
				What we try to do here is to find method parent class.
				
				NOTE: for the moment, we only search at level 1 (no recursion)
			"""
			for (name, obj) in inspect.getmembers(mod):
				if inspect.isfunction(obj) and '__callable__' in dir(obj):
					#netnode.putChild(name, FuncNode(obj))
					# get original url if not set explicitly
					if 'url' not in obj.__callable__:
						obj.__callable__['url'] = obj.__callable__['_url']

					node = FuncNode(obj)
					plugin.addurl(node.url, node)
			
				elif inspect.isclass(obj) and issubclass(obj, Callable) and obj is not Callable:
					self.__classinit(obj, plugin)
					
				#TODO case submodule: load subclasses
				# (I've already done this elsewere ?)

			#print "MY URLS="
			#import pprint; pprint.pprint(plugin.flat_urls); pprint.pprint(plugin.regex_urls)
			
		# create all plugins storage backend
		self.db.create()

	def __classinit(self, klass, plugin):
		# why do we need to reimport module ?
		inst = self.classinstance(klass)
		# needed for URLS callbacks
		self.instances[klass] = inst
		
		basename = ''
		if isinstance(inst, Callable):
			klassnode = ClassNode(inst)
			#netnode.putChild(inst.__class__.__name__.lower(), klassnode)
			#netnode = klassnode
			if klass.url is not None:
				print "EEE", klass.url, klassnode, inst
				plugin.addurl(klass.url, klassnode)
		
		# if we enumerate class members, we get unbound methods
		# whereas when we enumarate instance members, we get bounded (ie callable) methods
		for (name, obj) in inspect.getmembers(inst):
			if not inspect.ismethod(obj) or not hasattr(obj, '__callable__'):
			#and obj.__callable__.get('autobind', False):
				continue

			fncnode = FuncNode(obj)
			#netnode.putChild(fncnode.name, fncnode)
			#url = obj.__callable__.get('url', obj.__name__)
			if 'url' not in obj.__callable__:
				obj.__callable__['url'] = obj.__callable__['_url']
			url = obj.__callable__['url']

			print 'UU', url, klass.url
			if klass.url is not None:
				#TODO: if url is a rx, it is more complex
				url = klass.url + url
			plugin.addurl(url, fncnode)

	def classinstance(self, klass):
		if klass not in self.instances:
			#print klass.__name__, "new instance"; issubclass(klass, Callable)
			exec 'import %s' % klass.__module__ #NOTE: __module__ is module name (str)

			# NOTE: As we can't do it in CallableBuilde, I put it here; but I'm not satisfied of
			# this
			#
			# NOTE: a None url means we don't prepend klass url to methods ones
			if not hasattr(klass, 'url'):
				klass.url = '/' + klass.__name__.lower()
			elif klass.url is not None and not klass.url.startswith('/'):
				raise Exception("Invalid %s as %s class url: MUST start with '/'" % (klass.url,
					klass.__name__))
			##

			inst = eval("%s.%s(%s)" % (klass.__module__, klass.__name__, 
				'self.context'	if issubclass(klass, Callable) else ''))

			self.instances[klass] = inst

		return self.instances[klass]

	def boundmethod(self, meth):
		klassinst = self.classinstance(meth.im_class)
		inst = getattr(klassinst, meth.__name__)

		if not inspect.ismethod(inst):
			raise Exception('%s.%s is not a method', klassinst.__name__, inst.__name__)

		return inst


	def list(self):
		return list(map(lambda p: {'name': p.name, 'uuid': p.uuid, 'active': p.active}, Plugin))
