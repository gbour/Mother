#!/usr/bin/env python
# -*- coding: utf8 -*-
__version__ = "$Revision: 165 $ $Date: 2011-03-19 17:29:20 +0100 (sam. 19 mars 2011) $"
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
import os, os.path

#from distutils.core                 import setup
#from distutils.command.install_lib  import install_lib
#from distutils.command.install      import install
#from distutils.dist                 import Distribution
from distutils.dir_util             import ensure_relative
from setuptools import setup, Command
from setuptools.command.install_lib  import install_lib
from setuptools.command.install      import install
from setuptools.dist                 import Distribution

class _Distribution(Distribution):
	def __init__(self, *args, **kwargs):
		# add new option for motherapps
		self.motherapps = []

		Distribution.__init__(self, *args, **kwargs)

		# automatically install our install_lib version
		if not 'install' in self.cmdclass:
			self.cmdclass['install']= _install
		if not 'install_lib' in self.cmdclass:
			self.cmdclass['install_lib']= _install_lib


class _install(install):
	def _fix_paths(self):
		self.install_apps = self.install_base
		# manage --prefix option (i.e is set when in an environment created with *virtualenv*)
		if self.prefix_option is None and self.install_base == '/usr': # default prefix
			# TODO: specific install paths may not be changes if explicitly specified by user on command line (--install-scripts and --install-data options)
			(self.install_scripts, self.install_data, self.install_apps) = ('/usr/bin', '/', '/')

		# manage --root option (is set when doing "setup.py bdist")
		if self.root is not None:
			for p in ('scripts','data','apps'):
				setattr(self, 'install_'+p, os.path.join(self.root, ensure_relative(getattr(self, 'install_'+p))))
		
	def finalize_options(self):
		install.finalize_options(self)
		self._fix_paths()

	def run(self):
		self._fix_paths()
		install.run(self)


class _install_lib(install_lib):
	excludes = ['.svn']
	dest     = 'var/lib/mother/apps'
	_pyfiles = []

	def run(self):
		install_lib.run(self)

		if self.dry_run or len(self.distribution.motherapps) == 0:
			return

		inst = self.get_finalized_command('install')

		for app in self.distribution.motherapps:
			self._copy_tree(
				os.path.join(*app.split('.')), 
				os.path.join(inst.install_apps, self.dest)
			)

		self.byte_compile(self._pyfiles)

	def _copy_tree(self, src, dst):
		"""We replace Command.copy_tree() as we need to exclude .svn directories
		"""	
		_excl = list(self.excludes)

		# we keep only the last dir of src path
		dststart = len(src.split(os.sep))-1 
		self.mkpath(os.path.join(dst, *src.split(os.sep)[dststart:]))

		for root, dirs, files in os.walk(src):
			if root in _excl:
				[_excl.append(os.path.join(root,d)) for d in dirs]; continue

			_dst = os.path.join(dst, *root.split(os.sep)[dststart:])
			for d in dirs:
				if d in _excl:
					_excl.append(os.path.join(root, d))
				else:
					self.mkpath(os.path.join(_dst, d))

			[self._copy_file(os.path.join(root, f), os.path.join(_dst, f)) for f in files if f not in _excl]

	def _copy_file(self, src, dst):
		install_lib.copy_file(self,src, dst)
		if dst.endswith('.py'):
			self._pyfiles.append(dst)


setup(
	name         = 'mother',
	version      = '0.1.0',
	description  = 'Mother - Web Applications Framework',
	author       = 'Guillaume Bour',
	author_email = 'guillaume@bour.cc',
	url          = 'http://devedge.bour.cc/wiki/Mother/',
	license      = 'GNU Affero General Public License v3',
	classifiers  = [
		'Development Status :: 3 - Alpha',
		'Environment :: Console',
		'Environment :: No Input/Output (Daemon)',
		'Environment :: Web Environment',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: GNU Affero General Public License v3',
		'Natural Language :: English',
		'Natural Language :: French',
		'Operating System :: OS Independent',
		'Programming Language :: Python',
		'Programming Language :: Python :: 2.5',
		'Programming Language :: Python :: 2.6',
		'Programming Language :: Python :: 2.7',
		'Topic :: Internet',
		'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
		'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
		'Topic :: Internet :: WWW/HTTP :: Site Management',
		'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
		'Topic :: Software Development',
		'Topic :: Software Development :: Libraries :: Application Frameworks',
		'Topic :: Software Development :: User Interfaces',
	],

	long_description = """Mother is a framework made for fasten and easier web-applications developement:
		. url rewriting
		. multiprotocol (HTML, json, xml??)
		. autoexposing tentacles objects
		. arguments validation
		. contents modifiers (py object to json, uppercase, etc)
		. simple programmation
		. work with apps 
		. users/groups/acl managements
		. dashboard (add/remove/disable apps)
		. create/manage user/groups
		. manage acls
		. http/https
		. authentication framework
		. plugins (a app can be hooked)
	""",

	scripts     = ['bin/mother'],
	package_dir = {'': 'lib'},
	packages    = ['mother'],
	data_files  = [
		('etc', ['etc/mother.cfg']),
		('usr/share/doc/python-mother', ['doc/mother.cfg.sample']),
		('etc/init.d', ['etc/init.d/mother']),
	],
	requires    = [
		'TwistedCore (>=10.1)', 'TwistedWeb (>= 10.1)', 'SimpleParse (>= 2.1.0)', 'Mako (>= 0.4.0)',
		'python_cjson', 'odict', 'tentacles'
	],

	distclass   = _Distribution,
	motherapps  = ['apps.sample'],
)

