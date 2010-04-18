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
from mother.network import *

class Pluggable(object):
	def __init__(self, plugin_dir, db):
		if not os.path.isdir(plugin_dir):
			raise Exception("plugin directory %s not found" % plugin_dir)
		sys.path.append(plugin_dir)

		# listing plugins
		self.db     = db
		self.cursor = db.cursor()

		# create tables if not exists
		try:
			self.cursor.execute("SELECT * FROM pluggable__plugins")
		except sqlite3.OperationalError:
			self.cursor.execute("""
				CREATE TABLE pluggable__plugins (
					uuid		TEXT PRIMARY KEY,
					name		TEXT,
					active	INTEGER
				);
			""")


	def initialize(self, root):
		self.cursor.execute("SELECT * FROM pluggable__plugins WHERE active = 1");
		for (uuid, name, active) in self.cursor:
			# try import
			try:
				exec 'import %s' % name
			except ImportError:
				continue
			mod = sys.modules[name]

			netnode = Resource()
			root.putChild(name, netnode)

			# check UUID matching
			if mod.UUID != uuid:
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
			        netnode.putChild(name, FuncNode(obj, True))
			        
			    elif inspect.isclass(obj):
			        self.__initialize_class(mod, obj, None, netnode)

	def __initialize_class(self, module, klass, callbacks, netnode):
	    # why do we need to reimport module ?
	    exec 'import %s' % module.__name__
	    inst = eval("%s.%s(db=self.db)" % (module.__name__, klass.__name__))
	    
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
		
		self.cursor.execute("SELECT * FROM pluggable__plugins WHERE active = 1");
		for (uuid, name, active) in self.cursor:
			try:
				exec 'import %s' % name
			except ImportError:
				traceback.print_exc()
				continue

			plugs.append(name)
			
		return plugs

