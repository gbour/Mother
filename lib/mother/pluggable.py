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

import sys, os, os.path, sqlite3, inspect, traceback
from twisted.web.resource   import Resource

from tentacles			  import Object
from tentacles.fields	   import *
from mother.network		 import *

class Plugin(Object):
	__stor_name__ = 'pluggable__plugins'

	uuid	= String(pk=True)
	name	= String()
	active  = Boolean(default=True)

class Pluggable(object):
	def __init__(self, plugin_dir, db):
		if not os.path.isdir(plugin_dir):
			raise Exception("plugin directory %s not found" % plugin_dir)
		sys.path.append(plugin_dir)

		# listing plugins
		self.db	 = db
		self.db.create()

	def initialize(self, root):
		plugins = filter(lambda x: x.active is True, Plugin)
		for plugin in plugins:
			# try import
			try:
				exec "import %s" % plugin.name in {}, {}
			except ImportError:
				continue
			mod = sys.modules[plugin.name]

			netnode = Resource()
			root.putChild(plugin.name, netnode)

			# check UUID matching
			if mod.UUID != plugin.uuid:
				continue

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
					netnode.putChild(name, FuncNode(obj))
			
				elif inspect.isclass(obj) and issubclass(obj, Callable) and obj is not Callable:
					self.__initialize_class(mod, obj, None, netnode)
					
				#TODO case submodule: load subclasses
				# (I've already done this elsewere ?)

	def __initialize_class(self, module, klass, callbacks, netnode):
		# why do we need to reimport module ?
		exec 'import %s' % module.__name__
		inst = eval("%s.%s(self.db)" % (module.__name__, klass.__name__))
		
		if isinstance(inst, Callable):
			klassnode = ClassNode(inst)
			netnode.putChild(inst.__class__.__name__.lower(), klassnode)
			netnode = klassnode
		
		# if we enumerate class members, we get unbound methods
		# whereas when we enumarate instance members, we get bounded (ie callable) methods
		for (name, obj) in inspect.getmembers(inst):
			if inspect.ismethod(obj) and '__callable__' in dir(obj):
				netnode.putChild(name, FuncNode(obj))


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

