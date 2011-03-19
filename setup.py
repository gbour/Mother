#!/usr/bin/env python
# -*- coding: utf8 -*-

__version__ = "$Revision$ $Date$"

import os, os.path

from distutils.core                 import setup
from distutils.command.install_data import install_data

class _install_data(install_data):
	excludes = ['.svn']

	def run(self):
		if not self.dry_run:
			dir = os.path.join(self.root, 'var/lib/mother/apps/sample')
			self.mkpath(dir)
			
			excludes = list(self.excludes)
			base     = 'plugins/sample'
			for root, dirs, files in os.walk(base):
				print root, dirs, files, excludes,'\n'
				if root in excludes:
					[excludes.append(os.path.join(root,d)) for d in dirs]; continue

				for d in dirs:
					if d in excludes:
						excludes.append(os.path.join(root, d))
					else:
						self.mkpath(os.path.join(dir, d))

				for f in files:
					if f not in excludes:
						self.copy_file(os.path.join(root, f), os.path.join(dir, root[len(base)+1:], f))

		install_data.run(self)


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

	long_description = """Mother try to bring web applications development as simple as
it could be...blablabla""",


	scripts     = ['bin/mother'],
	package_dir = {'': 'lib'},
	packages    = ['mother'],
	data_files  = [
		('/etc', ['etc/mother.cfg']),
		('share/doc/mother', ['doc/mother.cfg.sample'])
	],
	requires    = [
		'TwistedCore (>=10.1)', 'TwistedWeb (>= 10.1)', 'SimpleParse (>= 2.1.0)', 'Mako (>= 0.4.0)',
		'odict', 'tentacles'
	],

	cmdclass    = {'install_data': _install_data}
)

