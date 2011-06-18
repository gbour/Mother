Mother
======

Mother is a web-applications framework.
Written in python, it is based on Twisted and Tentacles.

###Requirements
* twisted (core + web + web2)
* [Tentacles](http://devedge.bour.cc/wiki/Tentacles)

###Installation
To install:

	easy_install mother

or

	wget [http://devedge.bour.cc/resources/mother/src/mother.latest.tar.gz](http://devedge.bour.cc/resources/mother/src/mother.latest.tar.gz)
	tar xvf mother.latest.tar.gz
	cd mother-* && ./setup.py install

Introduction - ReSTful API
--------------------------

Mother expose apps. Each *app* is a python module with functions and classes. a
function/class/method can be requested by users if only decorated with @callback (or inheriting 
Callable for classes).
Default mime-type/data format is JSON.


	@callback
	def helloworld(**kwargs):
		return 'Hello World'


	class SuperHeroe(Callable):
		def __init__(self, *args, **kwargs):
			super(SuperHeroe, self).__init__(*args, **kwargs)

			self.superheroes = {}

		def GET(self, name):
			try:
				return self.superheroes[name]
			except Exception:
				return routing.HTTP_404

		def PUT(self, name, strength, capacity):
			self.superheroes[name] = {'name': name, 'strength': strength, 'capacity': capacity}

			return routing.HTTP_200
	
		@callback
		def count(self):
			return len(self.superheroes)


Mother is designed to be used with an ORM, in particularly *Tentacles* (though you can use it with
any python ORM).
In a future release, each Tentacle Object will by automatically exposed through standard ReST
methods (GET, PUT, DELETE). But from now, it as to be done manually

	class SuperHeroe(Object, Callable):
		name   = String(pk=True)
		gender = String()
		power  = String()

		# let Object standard __init__()

		def GET(self, name)
			"""Name is the key of superheroes
			"""
			
			try:
				heroe = filter(lambda h: h.name == name, SuperHeroe)[1]

				return {'name': heroe.name, 'gender': heroe.gender, 'power': heroe.power}
			except Exception:
				return routing.HTTP_404	
			
		def PUT(self, name, gender, power):
			"""Add a new superheroe or update existing one

			"""
			if len(filter(lambda h: h.name == name, self.__class__)):
				heroe = filter(lambda h: h.name == name, self.__class__)[1]
			else:
				heroe = SuperHeroe(name)

			heroe.gender = gender
			heroe.power  = power
			heroe.save()

			return routing.HTTP_200

		def DELETE(self, name):
			try:
				heroe = filter(lambda h: h.name == name, self.__class__)[1]
				heroe.delete()
			except:
				return routing.HTTP_404

HTML for humans
---------------

While Mother default format is JSON, you can also handle HTML format (in fact you can handle any
format you want)

Let's take back our «hello world» example, and return HTML content::

	@callback(content_type='text/html')
	def helloworld(
		return """
			<html>
				<head>
					<title>Hello World</title>
				</head>
				<body>
					<em>Welcome to *Mother* webapps framework</em>
				</body>
			</html>
		"""

Callback modifier, one for all
------------------------------

@callback modifier is the master piece of mother:
* tagging a method as callable
* set accepted methods
* change default method url
* set content_type
* set modifiers

Examples::
	@callback(method=('GET','POST')
	...

	@callback(url='/bar')
	def foo():
		...


Any query 
	@callback(content_type='image/png')
	def avatar(name)
		...

	@callback(modifiers={'text/plain': uppercase})
	def poem():
		return "La cigale et la fourmie"

	will display: «LA CIGALE ET LA FOURMIE»




Futures
-------

Mother is still pretty yound and incomplete, and still in alpha stage.
Only a few subset of schedules functionalities are implemented at the moment. Other ones will come
progressively.


About
-----

*Mother* is licensed under GNU GPL v3.
It is written by Guillaume Bour <guillaume@bour.cc>

