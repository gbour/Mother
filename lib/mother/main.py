# -*- coding: utf8 -*-
__version__ = "$Revision$ $Date$"
__author__  = "Guillaume Bour <guillaume@bour.cc>"
__license__ = """
	Mother, Application Server
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

import sys, sqlite3, traceback, logging
import config

from twisted.internet       import reactor
from twisted.web            import server
from twisted.web.resource   import Resource
from twisted.application    import service, internet

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
		self.db = Storage(config.database)

		# load authentification 
		#TODO: should be optional
		import mother.authentication
		self.db.create()


		self.plug = Pluggable(config.plugdir, self.db, Context(self))

		from mother import routing
		import functools
		routing.url = functools.partial(routing.url, self.plug)
		
	def run(self, foreground=False):
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

		wrapper = AuthWrapper(portal, [DigestCredentialFactory('md5', 'example.org')])
		# ssl on
		#wrapper = HTTPAuthSessionWrapper(portal, [DigestCredentialFactory('md5', 'example.org')])
		#wrapper.putChild(root)
		##root    = wrapper
		# /ssl

		self.plug.initialize(root)

		#. FINAL!!! start listening on the network
		site = server.Site(root, logPath=self.config.accesslog)
		self.logger.info('Mother start listening...')
		if foreground:
			reactor.listenTCP(self.config.port, site)
			reactor.run()
			return

		application = service.Application('mother')
		svc = internet.TCPServer(self.config.port, site) #, interface='*')
		svc.setServiceParent(application)

		return application
		
	def list_plugins(self):
		return self.plug.list()


class Context(object):
	def __init__(self, mother):
		self.mother = mother		
		self.db     = mother.db

	def plugins(self):
		return self.mother.list_plugins()

