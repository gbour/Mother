# -*- coding: utf8 -*-
__version__ = "$Revision$ $Date$"
__author__  = "Guillaume Bour <guillaume@bour.cc>"
__license__ = """
	Mother, Application Server
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

import sys, sqlite3, traceback, logging
import config

from twisted.internet       import reactor
from twisted.web            import server
from twisted.web.resource   import Resource

from tentacles              import *
from mother.pluggable       import Pluggable, Plugin

LEVELS = {
	'debug'    : logging.DEBUG,
	'info'     : logging.INFO,
	'warning'  : logging.WARNING,
	'error'    : logging.ERROR,
	'critical' : logging.CRITICAL,
}

class Mother(object):
	def __init__(self, config):
		self.config = config
		
		# set logging
		level = LEVELS.get(config.loglevel, logging.NOTSET)
		logging.basicConfig(level=level)
		self.logger = logging.getLogger('mother')
		if config.logfile != '-':
			self.logger.addHandler(logging.FileHandler(config.logfile))
		self.logger.info('Initializing mother')
		
		#.init database
#		self.db = sqlite3.connect(config.database)
#		print config.database, Storage.__objects__
		self.db = Storage(config.database)

		# load authentification 
		#TODO: should be optional
		import mother.authentication
		self.db.create()


		self.plug = Pluggable(config.plugdir, self.db, Context(self))

		from mother import routing
		import functools
		routing.url = functools.partial(routing.url, self.plug)
		
	def run(self):
		root = Resource()

		from mother.authentication import MotherRealm, AuthWrapper
		from twisted.cred.portal   import Portal
		portal = Portal(MotherRealm(root))
		from twisted.cred import checkers, credentials
		mycheck = checkers.InMemoryUsernamePasswordDatabaseDontUse()
		mycheck.addUser('foo', 'bar')
		portal.registerChecker(mycheck)
		# allow anonymous access (for login form)
		#portal.registerChecker(checkers.AllowAnonymousAccess(), credentials.IAnonymous)

		#self.plug.initialize(root)

		from twisted.web.guard import DigestCredentialFactory
		from twisted.web.guard import HTTPAuthSessionWrapper

		#wrapper = HTTPAuthSessionWrapper(portal, [DigestCredentialFactory('md5', 'example.org')])
		wrapper = AuthWrapper(portal, [DigestCredentialFactory('md5', 'example.org')])
		#wrapper.putChild(root)
		root    = wrapper

		self.plug.initialize(root)

		#. FINAL!!! start listening on the network
		self.logger.info('Mother start listening...')
		reactor.listenTCP(self.config.port, server.Site(root, logPath=self.config.accesslog))
		reactor.run()
		
	def list_plugins(self):
		return self.plug.list()

class Context(object):
	def __init__(self, mother):
		self.mother = mother		
		self.db     = mother.db

	def plugins(self):
		return self.mother.list_plugins()
