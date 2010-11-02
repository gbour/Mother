
UUID = '7c772000-8f12-4594-9730-9e4de53d55d1'

from mother.template import Static
from sample          import *
from plop            import Plop

URLS = {
	'/'                     : Plop.root,
	'/bar2'                 : Sample.foo2,
#	'/plip/{arg1}'          : Plop.plip,
#	'/plup/(?P<arg1>[^/]+)' : Plop.plup,

	r'/static/?.*'          : Static('static/')
}
