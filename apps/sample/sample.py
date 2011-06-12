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
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA..
"""

from mother.callable import Callable, callback #, COBBuilder
from tentacles import *
from tentacles.fields import *

class Turd(Callable, Object):
	#__metaclass__ = COBBuilder

	id   = Integer(pk=True, autoincrement=True)
	name = String()

 
class Sample(Callable):
	"""
		Sample class base url is '/sample/sample' (pluginname + classname)
	"""
	def __init__(self, context):
		self.context = context

	def GET(self):
		"""

		url = '/sample/sample"
		"""
		return "Sample::GET"

	@callback
	def subsample(self):
		"""
			url = '/sample/sample/subsample'
		"""
		return 'sample::subsample'

	@callback(url='/bar')
	def foo(self):
		"""
			url = '/sample/sample/bar'
		"""
		return 'sample::foo'

	@callback
	def foo2(self):
		"""
			url = '/sample/bar2' (defined in module URLs dict)
		"""
		return 'sample::foo2'

	@callback(url='/bar2/{arg1}')
	def foo3(self, arg1):
		return 'sample::foo3=%s' % arg1


@callback
def sample3():
	"""
		url = '/sample/sample3'
	"""
	return 'this is 3d sample'

@callback(url=r'/smaple4/(?P<arg1>[^/]+)')
def sample4(arg1):
	return 'sample4=', arg1
