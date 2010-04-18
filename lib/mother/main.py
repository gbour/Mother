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

from mother.pluggable        import Pluggable

LEVELS = {
    'debug'     : logging.DEBUG,
    'info'      : logging.INFO,
    'warning'   : logging.WARNING,
    'error'     : logging.ERROR,
    'critical'  : logging.CRITICAL,
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
        
        #. init database
        self.db = sqlite3.connect(config.database)

        #. bootstrap pluggable plugin
        self.plug = Pluggable(config.plugdir, self.db)
        
    def run(self):
        root = Resource()
        self.plug.initialize(root)

        #. FINAL!!! start listening on the network
        self.logger.info('Mother start listening...')
        reactor.listenTCP(self.config.port, server.Site(root))
        reactor.run()
        
    def list_plugins(self):
        return self.plug.list()

