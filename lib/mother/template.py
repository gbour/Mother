
import os, inspect
from twisted.web import static

class Static(static.File):
	def __init__(self, path, *args, **kwargs):
		basedir =	os.path.dirname(inspect.getframeinfo(inspect.currentframe().f_back)[0])
		static.File.__init__(self, os.path.join(basedir, path), *args, **kwargs)

