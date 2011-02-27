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

import sys, os, os.path, re, sqlite3, inspect, traceback, types
# hotpatching inspect.isclass. see
# http://stackoverflow.com/questions/4081819/why-does-python-inspect-isclass-think-an-instance-is-a-class
if sys.version_info < (2, 7):
	inspect.isclass = lambda obj: isinstance(obj, (type, types.ClassType))

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
from mother.eurl          import eURL


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
		self.flat_urls		= eURL() #{}
		self.regex_urls   = eURL() #odict()

	def addurl(self, url, content_type, resource):
		"""Append a new URL resource

			@url: relative to application root. May be:
				- raw url (/my/url)
				- simple regex (/my/{url})
				- true regex   (r'/my/(?<url>[^/]+))
				- HTTPCode class

			@content_type: may be a single value (i.e 'text/plain') or a list (i.e
			('text/html','application/xhtml+xml'))
		"""
		#TODO: should raise exception/warning on duplicates url
		store = self.flat_urls
		if not isinstance(content_type, (tuple, list)):
			content_type = (content_type,)

		if isinstance(url, types.StringTypes):
			if isinstance(resource, template.Static):
				#TODO: if resource is file, not directory, we must not change url to match all
				#sub paths/files
				if url.endswith('$'):
					url = url[:-1]
				url += '.*$'

			# compile regex url
			def argmatch(m):
				return '(?P<%s>%s)' % (m.group(1), '[^/]*' if m.group(2) is None else
						m.group(2))
			_url = re.sub(r'\{(\w*[a-zA-Z-]+\w*)(?::((?:[^{}]+|{\d*,\d*})+))?\}', argmatch, url)

			if re.search(r'[([{.*+^$]', _url) != None:
				# url is a regex
				_url     = "^%s$" % _url     # force bounds
				store    = self.regex_urls
				resource = (re.compile(_url), resource)

		elif inspect.isclass(url) and issubclass(url, routing.ActionURL):
			""" when url is actionURL (LOGIN, LOGOUT),
				we store both object, and string url

				string-url is to resolve a query
			"""
			for ctype in content_type:
				store[(url.url, ctype)] = resource

			#TODO: should not be done here
			if url == routing.LOGIN:
				setattr(resource, 'render_POST', query_builder('POST', resource.func.__callable__['postlogin']))

		elif isinstance(url, routing.ActionURL):
			# keep this order, or you will have the wrong url
			for ctype in content_type:
				store[(url.url, ctype)] = resource
			url = url.__class__ # we want the class definition, not instance
		
		for ctype in content_type:
			store[(url, ctype)] = resource
	
	def objects(self):
		objs = [o for (n, o) in inspect.getmembers(sys.modules[self.name]) if
				inspect.isclass(o) and issubclass(o, Object) and o != Object]
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

		for plugin in plugins:
			# try import
			try:
				exec "import %s" % plugin.name in {}, {}
			except ImportError, e:
				print "/!\ Cannot import %s plugin:" % plugin.name, e
			mod = sys.modules[plugin.name]

			mod.CONTEXT = AppContext(mod)
			mod.PLUGIN  = plugin
			plugin.MODULE = mod

			plugin.root = PluginNode(plugin)
			root.putChild(plugin.name, plugin.root)
			self.plugins[plugin.name] = plugin

			# check UUID matching
			if mod.UUID != plugin.uuid:
				print "/!\ plugin UUID does not match database one (%s vs %s)" % \
					(plugin.uuid, mod.UUID)
				continue

			# set default values 
			#TODO: use a generic directory
			#TODO: should be done earlier, before @callback decorators were called
			if not hasattr(mod, 'AUTHENTICATION'):
				mod.AUTHENTICATION = False

			# load URL callbacks
			raw_urls = mod.__dict__.get('URLS', {})
			for url, target in raw_urls.iteritems():
				"""Looping on URLs

				we must determine if url is:
				. a raw string		(i.e: /foo/bar)
				. a simple regex  (i.e: /foo/{bar})
				. a full regex		(i.e: /foo/(?<bar>[^/]+))
				"""
				if not isinstance(target, (tuple,list)):
					target = (target,)

				for _target in target:
					if isinstance(_target, static.File):
						content_type = _target.content_type if hasattr(_target,'content_type') else '*/*'
						plugin.addurl(url, content_type, _target); 
						continue
					elif isinstance(_target, template.Template):
						plugin.addurl(url, _target.content_type, TemplateNode(mod, _target)); continue
			

					# resolve unbound methods
					if hasattr(_target, 'im_self') and _target.im_self is None:
						#callback = getattr(self.instances[callback.im_class], callback.__name__)
						#callback = getattr(self.__classinstance(callback.im_class), callback.__name__)
						_target = self.boundmethod(_target)

					if not hasattr(_target, '__callable__'):
						raise Exception('%s is not callable' % _target.__name__)
					elif 'url' in _target.__callable__:
						raise Exception("%s url cannot be redefined (is %s, try to set %s)" %\
							(_target.__name__, _target.__callable__['url'], url))

					_target.__callable__['url'] = url
					plugin.addurl(url, _target.__callable__['content_type'], FuncNode(_target))


			# load plugin callbacks
			"""
				mod.__callbacks__ contains callback functions but we don't
				know at which classes it belongs (cause when decorator is called,
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
					plugin.addurl(node.url, obj.__callable__['content_type'], node)
			
				#NOTE: why limited to callable objects only
				elif inspect.isclass(obj) and issubclass(obj, Callable) and obj is not Callable:
					self.__classinit(obj, plugin)
					
				#TODO case submodule: load subclasses
				# (I've already done this elsewere ?)

			import pprint; pprint.pprint(plugin.flat_urls); pprint.pprint(plugin.regex_urls)
			
		# create all plugins storage backend
		self.db.create()

	def __classinit(self, klass, plugin):
		# why do we need to reimport module ?
		inst = self.classinstance(klass)
		# needed for URLS callbacks
		self.instances[klass] = inst
		
		basename = ''
		#NOTE: __classinit is only called if inst is callable
		iscallable = False
		ctypes = []
		klassnode = None

		if isinstance(inst, Callable):
			iscallable = True
			klassnode = ClassNode(inst)
			#netnode.putChild(inst.__class__.__name__.lower(), klassnode)
			#netnode = klassnode
			if klass.url is not None:
				plugin.addurl(klass.url, klass.__content_type__, klassnode)
				ctypes.append(klass.__content_type__)

				"""
				for mod, clb in klass.__modifiers__.iteritems():
					# bounding unbound method
					if inspect.isfunction(clb) and len(inspect.getargspec(clb).args) > 1 and\
						clb.__name__ in klass.__dict__:
							inst.__modifiers__[mod] = getattr(inst, clb.__name__)
					plugin.addurl(klass.url, mod, klassnode)
					ctypes.append(mod)
				"""

		# if we enumerate class members, we get unbound methods
		# whereas when we enumarate instance members, we get bounded (ie callable) methods
		for (name, obj) in inspect.getmembers(inst):
			if not inspect.ismethod(obj):
			#or not hasattr(obj, '__callable__'):
			#and obj.__callable__.get('autobind', False):
				continue

			if name in ('GET','HEAD','POST','PUT','DELETE'):
				if not iscallable:
					raise Exception("%s method name is forbidden outside callable classes" %	name)

				if hasattr(obj, '__callable__'):
					ctypes = []
					opts = obj.__callable__

					if 'content_type' in opts:
						print '/!\ WARNING: content_type cannot be redefined in class HTTP methods	(GET, POST, ...)'

					if 'modifiers' in opts:
						if not isinstance(opts['modifiers'], dict):
							raise Exception("modifiers must be a dictionary")

						for k, clb in opts['modifiers'].iteritems():
							print '__mm', k, k in ctypes
							if k not in ctypes:
								if 'url' in opts:
									plugin.addurl('%s%s' % (klass.url, opts['url']), k, klassnode)
								else:
									plugin.addurl(klass.url, k, klassnode)
								ctypes.append(k)

							# bounding unbound method
							if inspect.isfunction(clb) and len(inspect.getargspec(clb).args) > 1 and\
								 clb.__name__ in klass.__dict__:
								opts['modifiers'][k] = getattr(inst, clb.__name__)
							#TODO: LoopbackSelf. more generic code
							#from plugins.strawberry.link import LoopbackSelf
							#print "loop>",clb, isinstance(clb, LoopbackSelf),	clb.__class__.__name__
							#print "loop>",clb, clb.__class__.__name__, clb.__class__.__name__ == 'LoopbackSelf'
							#if isinstance(clb, LoopbackSelf):
							if clb.__class__.__name__ == '_LoopbackSelf':
								clb = getattr(inst, clb.called)
								opts['modifiers'][k] = clb

				continue

			if not hasattr(obj, '__callable__'):
				continue

			fncnode = FuncNode(obj)
			#netnode.putChild(fncnode.name, fncnode)
			#url = obj.__callable__.get('url', obj.__name__)
			if 'url' not in obj.__callable__:
				obj.__callable__['url'] = obj.__callable__['_url']
			url = obj.__callable__['url']

			if klass.url is not None:
				#TODO: if url is a rx, it is more complex
				url = klass.url + url
			plugin.addurl(url, obj.__callable__['content_type'], fncnode)

			# non special class methods modifiers
			if 'modifiers' in obj.__callable__:
				opts = obj.__callable__['modifiers']

				for k, clb in opts.iteritems():
					plugin.addurl('%s%s' % (klass.url, obj.__callable__.get('url','')), k, fncnode)

					# bounding unbound method
					if inspect.isfunction(clb) and len(inspect.getargspec(clb).args) > 1 and\
						 clb.__name__ in klass.__dict__:
						opts[k] = getattr(inst, clb.__name__)

					#TODO: LoopbackSelf. more generic code
					if clb.__class__.__name__ == '_LoopbackSelf':
						opts[k] = getattr(inst, clb.called)

		# class base modifiers have low priority over methods specific modifiers
		if isinstance(inst, Callable) and klass.url is not None:
			for mod, clb in klass.__modifiers__.iteritems():
				# bounding unbound method
				if inspect.isfunction(clb) and len(inspect.getargspec(clb).args) > 1 and\
					clb.__name__ in klass.__dict__:
						inst.__modifiers__[mod] = getattr(inst, clb.__name__)

				plugin.addurl(klass.url, mod, klassnode)
				ctypes.append(mod)

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

			inst = eval("%s.%s(%s)" % (klass.__module__, klass.__name__, 
				'context=self.context'	if issubclass(klass, Callable) else ''))

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

