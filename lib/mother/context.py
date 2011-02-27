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
import sys, os, inspect
from mother import template

class AppContext(object):
	def __init__(self, app):
		"""

			@app: application module
		"""	
		assert inspect.ismodule(app), "AppContext *app* init parameter must be a module"
		self.app       = app

		appdir         = os.path.dirname(os.path.abspath(sys.modules[app.__name__].__file__))
		self.tplengine = template.MakoRenderEngine(os.path.join(appdir, 'templates/'))

	def render(self, tmpl):
		"""Render template
		
			Return result (string)
		"""
		return self.tplengine.render(tmpl)


class UserContext(object):
	pass

