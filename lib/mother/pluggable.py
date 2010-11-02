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

import sys, os, os.path, re, sqlite3, inspect, traceback
from odict                import odict

from twisted.web.resource import Resource
from twisted.web          import static
from twisted.web.rewrite  import RewriterResource

from tentacles            import *
from tentacles.fields	    import *
from tentacles.queryset   import filter
from mother.network       import *


class Plugin(Object):
	__stor_name__ = 'pluggable__plugins'

	## database fields
	uuid	        = String(pk=True)
	name	        = String()
	#path          = String()
	active        = Boolean(default=True)

	## urls is made of:
	#  . flat urls (exactly match)
	#  . regular expressions
	flat_urls		= {}
	regex_urls  = odict()

	def addurl(self, url, resource):
		# compile regex url
		def argmatch(m):
			return '(?P<%s>[^/]*)' % m.group(1)
		_url = re.sub(r'\{(\w*[a-zA-Z-]+\w*)\}', argmatch, url)

		storin = self.flat_urls
		if re.search(r'[([{.*+^$]', _url) != None:
			# url is a regex
			storin   = self.regex_urls
			resource = (re.compile(url), resource)

		storin[url] = resource

class Pluggable(object):
	def __init__(self, plugin_dir, db):
		if not os.path.isdir(plugin_dir):
			raise Exception("plugin directory %s not found" % plugin_dir)
		sys.path.append(plugin_dir)

		# listing plugins
		self.db	 = db
		self.db.create()

		self.instances = {}

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

			plugin.root = PluginNode(plugin)
			root.putChild(plugin.name, plugin.root)

			# check UUID matching
			if mod.UUID != plugin.uuid:
				print "/!\ plugin UUID does not match database one (%s vs %s)" % \
					(plugin.uuid, mod.UUID)
				continue

			# load URL callbacks
			print "loop on URLS"
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
			

				# resolve unbound methods
				if hasattr(target, 'im_self') and target.im_self is None:
					#callback = getattr(self.instances[callback.im_class], callback.__name__)
					#callback = getattr(self.__classinstance(callback.im_class), callback.__name__)
					target = self.__boundmethod(target)

				if not hasattr(target, '__callable__'):
					raise Exception('%s is not callable' % inst.__name__)
				elif 'url' in target.__callable__:
					raise Exception("%s url cannot be redefined (is %s, try to set %s)" %\
						(target.__name__, target.__callable__['url'], url))
				#print 'callback=', target

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
					node = FuncNode(obj)
					plugin.addurl(node.url, node)
			
				elif inspect.isclass(obj) and issubclass(obj, Callable) and obj is not Callable:
					self.__classinit(obj, plugin)
					
				#TODO case submodule: load subclasses
				# (I've already done this elsewere ?)

		#print "MY URLS="
		#import pprint; pprint.pprint(plugin.flat_urls); pprint.pprint(plugin.regex_urls)
				

	def __classinit(self, klass, plugin):
		# why do we need to reimport module ?
		inst = self.__classinstance(klass)
		
		basename = ''
		if isinstance(inst, Callable):
			klassnode = ClassNode(inst)
			#netnode.putChild(inst.__class__.__name__.lower(), klassnode)
			#netnode = klassnode
			klassurl = '/' + klass.__name__.lower()
			plugin.addurl(klassurl, klassnode)
		
		# if we enumerate class members, we get unbound methods
		# whereas when we enumarate instance members, we get bounded (ie callable) methods
		for (name, obj) in inspect.getmembers(inst):
			if not inspect.ismethod(obj) or not hasattr(obj, '__callable__'):
			#and obj.__callable__.get('autobind', False):
				continue

			fncnode = FuncNode(obj)
			#netnode.putChild(fncnode.name, fncnode)
			plugin.addurl(klassurl + obj.__callable__.get('url', obj.__callable__['_url']), fncnode)

	def __classinstance(self, klass):
		if klass not in self.instances:
			#print klass.__name__, "new instance"; issubclass(klass, Callable)
			exec 'import %s' % klass.__module__ #NOTE: __module__ is module name (str)
			inst = eval("%s.%s(%s)" % (klass.__module__, klass.__name__, 
				'self.db'	if issubclass(klass, Callable) else ''))
			self.instances[klass] = inst

		return self.instances[klass]

	def __boundmethod(self, meth):
		klassinst = self.__classinstance(meth.im_class)
		inst = getattr(klassinst, meth.__name__)

		if not inspect.ismethod(inst):
			raise Exception('%s.%s is not a method', klassinst.__name__, inst.__name__)

		return inst


	def list(self):
		plugs = []
		
		plugins = filter(lambda x: x.active is True, Plugin)
		for plugin in plugins:
			try:
				exec "import %s" % plugin.name in {}, {}
			except ImportError:
				traceback.print_exc()
				continue

			plugs.append(plugin.name)
			
		return plugs
