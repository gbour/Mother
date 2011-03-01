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

import sys, os, os.path, inspect
from twisted.web     import static
from mako            import exceptions
from mako.lookup     import TemplateLookup

from mother import routing

class Static(static.File):
	def __init__(self, path, *args, **kwargs):
		"""
			WARNING: Static() must be reentrant AS File reinstanciate itself via
  			createSimilarFile() method. In consequence, content_type argument MUST be in
	  		kwargs
		"""
		basedir =	os.path.dirname(inspect.getframeinfo(inspect.currentframe().f_back)[0])
		name = None
		if 'name' in kwargs:
			name = kwargs['name']; del kwargs['name']
		if not os.path.isabs(path):
			path = os.path.join(basedir, path)
		static.File.__init__(self, path, *args, **kwargs)

		if name is not None:
			#TODO: used dedicaced module to create anonymous object
			class anonymous(object): pass
			clb = anonymous()
			clb.__callable__ = {'url': '/' + name}

			# get module instance
			app = inspect.getmodule(inspect.currentframe().f_back)
			# clb module is current, aka mother.template
			# we want it to be app, to get correct url() resolution
			clb.__module__ = app.__name__
			setattr(app, name, clb)

		self.content_type = kwargs.get('content_type', '*/*')

		# set default encoding to utf8
		self.contentTypes['.css']  = 'text/css; charset=utf-8'
		self.contentTypes['.html'] = 'text/html; charset=utf-8'


class RenderEngine(object):
	pass


class MakoRenderEngine(RenderEngine):
	def __init__(self, tmplsdir):
		self.engine = TemplateLookup(
			directories=tmplsdir,
			filesystem_checks=True,
			input_encoding='utf-8',
			output_encoding='utf-8',
			encoding_errors='replace'
		)

		self.tmpl_default_args = {
			'url': routing.url
		}

	def render(self, tmpl):
		"""

			@tmpl: template.Template instance
		"""
		_tmpl = self.engine.get_template(tmpl.filename)
		args = self.tmpl_default_args.copy()
		args.update(tmpl.args)

		try:
			ret = _tmpl.render(**args)
		except:
			ret = exceptions.html_error_template().render()

		return ret


class Template(object):
	def __init__(self, filename, content_type='text/html', **kwargs):
		"""

			@filename
			@kwargs
		"""
		self.filename     = filename
		self.content_type = content_type
		self.args         = kwargs
				

