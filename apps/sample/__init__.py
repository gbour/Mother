# -* coding: utf-8 -*-
__version__ = "$Revision$ $Date$"
__author__  = "Guillaume Bour <guillaume@bour.cc>"
__license__ = """
	Copyright (C) 2011, Guillaume Bour <guillaume@bour.cc>

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

# HOW TO USE IT
#	  1) install your application
#      $> mother --apps-add=/var/lib/mother/apps/sample
#         INFO:mother:Initializing mother
#         . App «sample» added. Please restart mother daemon
#
#      NOTE: sample mother app path may be different depending on the way you
#      install mother
#
#   2) you can check *sample* is correctly installed with following command:
#      $> mother --apps-list
#         INFO:mother:Initializing mother
#         Plugins:
#       	 .       sample [active=1, path=/tmp/pytests/var/lib/mother/apps]
#
#   3) run mother daemon
#      $> mother
#
#   4) open your browser to the default url of this application:
#      http://localhost:8080/sample
#
#      NOTE: adapt server ip/port to your configuration


# UUID is per-app specific (must be unique through all apps loaded in mother)
# you can generate your UUID using
UUID = '7c772000-8f12-4594-9730-9e4de53d55d1'

from mother          import routing
from mother.callable import callback, Callable
from mother.template import Static, Template

# ** Exposing your 1st function **

# To expose a function to the clients, simply add "@callback" decorator
#   * default url is '/appname/funcname' (in our case /sample/root')
#   * default accepted content type is 'text/html' (you can view the result in your browser)
#
# @callback accept few optional arguments. Among these:
#   * url (string): set callback url (different from function name) 
#                   this url MUST begin with '/', and is ALWAYS relative to app base
#                   (in our case, is prefixed with '/sample'
#
# callable function DO receive few named arguments. At the moment, we just accept
# these anonymously
#                   
# Here we expose root() function as '/' url (routing.ROOT is a special url matching
# both '/sample' and '/sample/' uris)
@callback(url=routing.ROOT)
def root(**kwargs):
	return """
		<html>
			<head>
				<title>Welcome to Mother Sample Application</title>
			</head>
			<body>
				This is the homepage of <b>Mother Sample Application</b>.<br/>
				<br>
				<em>You are welcome to watch my source code to see how to build your first
				<strong>Mother</strong> application</em>.
			</body>
		</html>
	"""

# ** Serve a specific content-type **

# A second @callback option is:
#   * content_type (string): taken among thoses defined at http://en.wikipedia.org/wiki/Internet_media_type#List_of_common_media_types) 
#     (or a generic form, i.e 'text/*')
#
# Mother will execute callable function only if query match this content type 
# (match is done through *Accept* HTTP header)
#
# A callable function will match the specified content type and its generic forms
# (here we match 'text/plain', 'text/*' and '*/*')
@callback(url='/foo', content_type='text/plain')
def foo(**kwargs):
	return 'foo:: plain text'


# ** One uri, Several content_types **

# You can "attach" more than one callback to the same url, using different content-types.

# So, if client query '/sample/foo' with 'Accept: text/plain' header, foo1() result
# is returned, whereas with 'Accept: application/json', foo2() result is returned.
@callback(url='/foo', content_type='application/json')
def foo(**kwargs):
	return ['foo', 'json tree']

@callback(url='/foo', content_type='text/html')
def foo(**kwargs):
	return '<html><body><b>foo</b>:: html content</body></html>'


# ** Passing arguments **

# You can provide arguments to your callback. Just add those as named arguments to
# the function
# callback url will be invoked with argument as param. eg:
#  http://foo/sample/bar?age=42
#
# NOTE: argument are all received as strings.
#       Its up to you to check if type match what you're waiting
@callback
def bar(age, **args):
	try:
		age = int(age)
	except:
		return routing.HTTP_404('age MUST be integer')

	return 'the captain is %d years old' % age


# ** Use a class as callback **

# If your class inherit from Callable, it will be accessible from outside
# the resulting url is composed of app name and class name (lowercased), eg '/sample/captain'
class Captain(Callable):
	def __init__(self, **kwargs):
		super(Captain, self).__init__(**kwargs)
		self._age = 54

	# special methods GET, POST, PUT, DELETE are directly mapped to '/sample/captain' url
	def GET(self, **kwargs):
		return 'Captain::GET'

	# You can also expose non-special class/instance methods with the callback modified
	# Here we learn a new @callback option, named 'method'
	#
	@callback
	def age(self, **kwargs):
		return self._age

	# Here we discover a new @callback argument, named 'method'
	# taking either a string among 'GET', 'POST','PUT','DELETE' or a list of these
	#
	# This argument set HTTP method(s) callback is accessible through (default is GET)
	@callback(url='/setage', method='POST')
	def age_post(self, age, **kwargs):
		try:
			self._age = int(age)
		except:
			return routing.HTTP_404('age MUST be integer')

		return routing.HTTP_200('')

# ** URLS dictionary **

# the URLS dict is another way to set your functions/classes callable
@callback
def hello(**kwargs):
	return 'hello'

URLS = {
	# expose function
	'/hel-lo'							: hello,
	# expose static content (directory)
	'/static'             : Static('static-content/'),
	# expose template file
	# NOTES
	#   . template files MUST be stored in a templates/ sub-directory
	#   . Mako is the only available template engine at present
	'/template'						: Template('sample.html', title='template sample title',
																	content="""You\'re viewing a template sample
																	page, rendered with <em>Mako</em>""")

	#	'/'                     : Plop.root,
	#	'/bar2'                 : Sample.foo2,
#	'/plip/{arg1}'          : Plop.plip,
#	'/plup/(?P<arg1>[^/]+)' : Plop.plup,

#//r'/static/?.*'          : Static('static/')
}
