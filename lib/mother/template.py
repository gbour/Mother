# -*- coding: utf8 -*-

import sys, os, inspect
from twisted.web     import static
from mako.lookup     import TemplateLookup

from mother import routing

class Static(static.File):
	def __init__(self, path, name=None, *args, **kwargs):
		basedir =	os.path.dirname(inspect.getframeinfo(inspect.currentframe().f_back)[0])
		static.File.__init__(self, os.path.join(basedir, path), *args, **kwargs)

		if name is not None:
			#TODO: used dedicaced module to create anonymous object
			class anonymous(object): pass
			clb = anonymous()
			clb.__callable__ = {'url': '/' + name}

			# get module instance
			app = inspect.getmodule(inspect.currentframe().f_back)
			setattr(app, name, clb)


class RenderEngine(object):
	pass


class MakoRenderEngine(RenderEngine):
	def __init__(self, tmplsdir):
		self.engine = TemplateLookup(
			directories=tmplsdir,
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
		print 'args=', args

		return _tmpl.render(**args)


class Template(object):
	def __init__(self, filename, **kwargs):
		"""

			@filename
			@kwargs
		"""
		self.filename = filename
		self.args     = kwargs
				

