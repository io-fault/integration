"""
# Web application for serving a project corpus.
"""
import json
import zipfile
import collections
import itertools
from dataclasses import dataclass

from fault.system import files
from fault.web import service, system
from fault.web import xml

from . import html

def render_factor_html(prefix, depth, styles, type, identifier, chapter:str, Transform=html.transform):
	return Transform(prefix, depth, chapter, styles=styles, identifier=identifier, type=type)

def buffer(iterator, limit=1024*4):
	current = b''
	for i in iterator:
		current += i
		if len(current) >= limit:
			yield current
			current = b''

	if current:
		yield current

	yield b''

@dataclass
class Select(object):
	"""
	# Corpus selection structure separating project, factor, and source.

	# [ Properties ]
	# /project/
		# The first path component of the request URI.
		# Empty string if root.
	# /factor/
		# The second path component of the request URI.
		# &None if there is no second component or it's an empty string.
	# /source/
		# The third and remaining path components as a string.
		# &None if there is no third component or it's an empty string.
	# /index/
		# Boolean designating whether or not a trailing slash was present.
	"""

	project: str = None
	factor: str = None
	source: str = None
	index: bool = None

	@classmethod
	def from_request_uri(Class, rpath, prefix=''):
		"""
		# Identify the project, factor, and source selected by the path.
		"""
		index = rpath[-1:] == '/'
		rpath = rpath.lstrip('/')
		first = rpath.find('/')

		if first == -1:
			return Class(rpath, None, None, index)

		project = rpath[:first]
		remainder = rpath[first+1:]
		factor, *source = remainder.split('/', 1)
		if source:
			source = source[0]
		else:
			source = None

		if project:
			project = prefix + project
		return Class(project, factor, source, index)

	@property
	def depth(self):
		"""
		# The number of path components.
		"""
		if self.project is None:
			return 0

		if self.factor is None:
			return 1

		return 2 + self.source.count('/') if self.source is not None else 1

	def factorpath(self):
		return '.'.join((self.project, self.factor))

	def factorjoin(self, *paths):
		return '/'.join((self.project, self.factor) + paths)

	def archivepath(self, plural, primary, factortype):
		"""
		# Calculate the archive path from the given project, factor, source triple.
		"""
		project = self.project
		factor = self.factor
		source = self.source

		if source is None:
			if factor is not None:
				rsrc = project + '/' + factor
				type = 'factor'
			else:
				rsrc = project
				type = 'project'
		else:
			rsrc = project + '/' + factor + '/' + source
			type = 'source'

		return (rsrc, type)

	def readmeta(self, corpus):
		"""
		# Retrieve the .meta.json entry for the factor being referenced.
		"""
		d = corpus.cp_read(self.factorjoin('.meta.json'))
		return tuple(json.loads(d))

	def readchapter(self, corpus, meta):
		"""
		# Retrieve the chapter for the given identifier.
		"""
		path, type = self.archivepath(*meta)
		rsrc = '/.chapter.txt'
		return corpus.cp_read(path + rsrc).decode('utf-8')

	def catchapters(self, corpus, meta):
		"""
		# Catenate the chapters of all the source files.
		"""
		path, type = self.archivepath(*meta)

		sources = corpus.cp_read_json(path + '/.index.json')
		chapter = "\n[]\n".join(
			corpus.cp_read(srcpath + '/.chapter.txt').decode('utf-8')
			for srcpath in (
				path + '/' + '/'.join(src)
				for src in sources
			)
		)

		return chapter

media_types = {
	'json': b'application/json',
	'txt': b'text/plain',
	'html': b'text/html',
	'css': b'text/css',
	'svg': b'image/svg+xml',
	'png': b'image/png',
}

def r_icon(sx, icons):
	jsstr = icons.get('emoji', '🚧')
	return sx.escape(jsstr)

def removeprefix(prefix, string):
	if string.startswith(prefix):
		return string[len(prefix):]
	return string

def r_projects(prefix, sx, index):
	yield from sx.element('dl',
		itertools.chain.from_iterable(
			sx.element('a',
				sx.element('div',
					itertools.chain(
						sx.element('dt',
							itertools.chain(
								sx.element('span',
									r_icon(sx, x[2]),
									('class', 'icon')
								),
								sx.element('span',
									sx.escape(x[0]),
									('class', 'factor-path'),
								),
							)
						),
						sx.element('dd',
							sx.element('span',
								sx.escape(x[-1]),
								('class', 'index-abstract'),
							)
						),
					),
				),
				('href', removeprefix(prefix, x[0]) + '/'),
			)
			for x in index
		),
		('class', 'project-index'),
	)

def f_icon(sx, type):
	if type == 'python-module':
		return sx.element('img', None, src="/.lib/" + type + ".png")
	elif type in {'extension', 'executable'}:
		return sx.escape(b'\xE2\x9A\x99\xEF\xB8\x8F'.decode('utf-8'))
	elif type == 'chapter':
		return sx.escape("📄")
	else:
		return sx.escape("📜")

def r_factors(sx, index):
	yield from sx.element('dl',
		itertools.chain.from_iterable(
			sx.element('a',
				sx.element('div',
					itertools.chain(
						sx.element('dt',
							itertools.chain(
								sx.element('span',
									f_icon(sx, x[1]),
									('class', 'icon')
								),
								sx.element('span',
									sx.escape(x[0]),
									('class', 'factor-path'),
								),
							)
						),
						sx.element('dd',
							sx.element('span',
								sx.escape(x[1]),
								('class', 'index-abstract'),
							)
						),
					),
				),
				('href', x[0]),
			)
			for x in index
		),
		('class', 'factor-index'),
	)

def r_sources(sx, index, icon=(b"\xf0\x9f\x93\x84".decode('utf-8'))):
	yield from sx.element('dl',
		itertools.chain.from_iterable(
			sx.element('a',
				sx.element('div',
					itertools.chain(
						sx.element('dt',
							itertools.chain(
								sx.element('span',
									sx.escape(icon),
									('class', 'icon')
								),
								sx.element('span',
									sx.escape('/'.join(x)),
									('class', 'source-path'),
								),
							)
						),
						sx.element('dd',
							sx.element('span',
								sx.escape('source'),
								('class', 'index-abstract'),
							)
						),
					),
				),
				('href', '/'.join(x)),
			)
			for x in index
		),
		('class', 'source-index'),
	)

class Corpus(service.Partition):
	"""
	# Corpus application providing access to a set of projects and their factors.
	"""
	Archive = zipfile.ZipFile

	@staticmethod
	def cp_parse_arguments(argv):
		data = collections.defaultdict(list)
		key = None
		for x in argv[1:]:
			if x[:1] == '.':
				key = x[1:]
			else:
				data[key].append(x)

		routes = [files.Path.from_path(x) for x in data.pop(None, ())]
		return argv[0] if argv[0] != '.' else '', routes, {k:dict(zip(v[::2], v[1::2])) for k,v in data.items()}

	def structure(self):
		return ([
			('cp_resources', self.cp_resources),
		], None)

	def cp_update(self, route):
		if self.cp_archive is not None:
			self.cp_archive.close()

		self.cp_archive = self.Archive(str(route))
		self.cp_projects = set(x[0] for x in self.cp_read_json('.index.json'))

	def part_dispatched(self, argv):
		self.cp_archive = None
		self.cp_context, self.routes, self.cp_parameters = self.cp_parse_arguments(argv)
		if self.cp_context:
			self.cp_prefix = self.cp_context + '.'
		else:
			self.cp_prefix = ''

		# CSS files.
		self.cp_resources = {}
		for type, d in self.cp_parameters.items():
			cotype = media_types[type] #* Only .css is used.

			for name, path in d.items():
				key = '.lib/{name}.{type}'.format(name=name, type=type)
				self.cp_resources[key] = (cotype, files.Path.from_absolute(path))

		self.cp_styles = ['/.lib/' + k +'.css' for k in self.cp_parameters['css']]
		self.cp_resources['favicon.ico'] = (None, None)

		self.cp_update(self.routes[0])
		self.cp_available = True

	def cp_read_json(self, path):
		return json.loads(self.cp_read(path))

	def cp_read(self, path):
		"""
		# Read a resource from the configured archive.
		"""
		try:
			out = self.cp_archive.read(path)
		except KeyError:
			# Available archive, but no such entry.
			raise
		except:
			# Attempt to re-open.
			self.cp_update(self.routes[0])
			self.cp_available = True
			try:
				out = self.cp_archive.read(path) # Update failure.
			except KeyError:
				raise
			except:
				self.cp_available = False
				raise

		return out

	def cp_send_resource(self, ctl, path):
		data = self.cp_archive.read(path)

		dot = path.rfind('.')
		if dot == -1:
			# Unknown type really.
			raise KeyError("no such resource")

		ext = path[dot+1:]
		ctl.http_set_response(b'200', b'OK', len(data), cotype=media_types[ext])
		ctl.http_iterate_output([(data,)])

	def cp_send_html(self, ctl, depth, chapter, factorpath, factortype):
		html = render_factor_html(self.cp_prefix, depth, self.cp_styles, factortype, factorpath, chapter)
		ctl.http_set_response(b'200', b'OK', None, cotype=b'text/html')
		ctl.http_iterate_output((x,) for x in buffer(html))

	def cp_project_index(self, ctl, prefix=''):
		"""
		# Handle root HTML requests.
		"""
		idx = [
			x for x in self.cp_read_json('.index.json')
			if x[0].startswith(prefix)
		]
		sx = xml.Serialization(xml_encoding='utf-8')
		doc = sx.element('html',
			itertools.chain(
				sx.element('head',
					itertools.chain(
						sx.element('meta', None, ('charset', 'utf-8')),
						itertools.chain.from_iterable(
							sx.element('link', (), rel='stylesheet', href=x)
							for x in self.cp_styles
						),
					)
				),
				sx.element('body',
					sx.element('main',
						itertools.chain(
							sx.element('h1', sx.escape("Project Index")),
							r_projects(self.cp_prefix, sx, idx),
							sx.element('h1', sx.escape(''), ('class', 'footer')),
						)
					),
					('class', 'index'),
				),
			)
		)

		ctl.http_set_response(b'200', b'OK', None, cotype=b'text/html')
		ctl.http_iterate_output((x,) for x in buffer(doc))

	def cp_factor_index(self, project, ctl, prefix=''):
		"""
		# Handle root HTML requests.
		"""
		idx = [
			x for x in self.cp_read_json(project + '/.index.json')
			if x[0].startswith(prefix)
		]
		sx = xml.Serialization(xml_encoding='utf-8')
		doc = sx.element('html',
			itertools.chain(
				sx.element('head',
					itertools.chain(
						sx.element('meta', None, ('charset', 'utf-8')),
						itertools.chain.from_iterable(
							sx.element('link', (), rel='stylesheet', href=x)
							for x in self.cp_styles
						),
					)
				),
				sx.element('body',
					sx.element('main',
						itertools.chain(
							sx.element('h1',
								itertools.chain(
									sx.element('span', sx.escape(project)),
									sx.element('span',
										sx.escape("factor-index"),
										('class', 'abstract-type')
									)
								)
							),
							r_factors(sx, idx),
							sx.element('h1', sx.escape(''), ('class', 'footer')),
						)
					),
					('class', 'index'),
				),
			)
		)

		ctl.http_set_response(b'200', b'OK', None, cotype=b'text/html')
		ctl.http_iterate_output((x,) for x in buffer(doc))

	def cp_source_index(self, project, factor, ctl, prefix=''):
		"""
		# Handle root HTML requests.
		"""
		fpath = '.'.join((project, factor))
		idx = [
			x for x in self.cp_read_json('/'.join((project, factor)) + '/.index.json')
			if x[0].startswith(prefix)
		]

		sx = xml.Serialization(xml_encoding='utf-8')
		doc = sx.element('html',
			itertools.chain(
				sx.element('head',
					itertools.chain(
						sx.element('meta', None, ('charset', 'utf-8')),
						itertools.chain.from_iterable(
							sx.element('link', (), rel='stylesheet', href=x)
							for x in self.cp_styles
						),
					)
				),
				sx.element('body',
					sx.element('main',
						itertools.chain(
							sx.element('h1',
								itertools.chain(
									sx.element('span', sx.escape(fpath)),
									sx.element('span',
										sx.escape("source-tree"),
										('class', 'abstract-type')
									)
								)
							),
							r_sources(sx, idx),
							sx.element('h1', sx.escape(''), ('class', 'footer')),
						)
					),
					('class', 'index'),
				),
			)
		)

		ctl.http_set_response(b'200', b'OK', None, cotype=b'text/html')
		ctl.http_iterate_output((x,) for x in buffer(doc))

	def part_select(self, ctl):
		try:
			ctl.accept(None) # Never accepts input.

			rpath = ctl.request.pathstring[self.part_depth or 1:]
			if not rpath:
				return self.cp_project_index(ctl)

			if rpath in self.cp_resources:
				typ, data = self.cp_resources[rpath]
				if data is not None:
					ctl.http_write_output(typ.decode('ascii'), data.fs_load())
				else:
					ctl.http_set_response(b'404', b'NOT FOUND', len(b"no such resource"), cotype=b'text/html')
					ctl.http_iterate_output([(b"no such resource",)])
				return

			s = Select.from_request_uri(rpath, prefix=self.cp_prefix)
			if s.factor:
				if s.index and s.source is not None:
					return self.cp_source_index(s.project, s.factor, ctl, prefix=s.source)
			else:
				if s.index:
					return self.cp_factor_index(s.project, ctl)
				else:
					if s.project in self.cp_projects:
						return ctl.http_redirect(rpath + '/')
					else:
						return self.cp_project_index(ctl, prefix=s.project.strip('.')+'.')

			if s.source or rpath.endswith('.index.json'):
				# Check if it's a direct resource request.
				try:
					self.cp_send_resource(ctl, self.cp_prefix + rpath)
					return
				except LookupError:
					# No such resource in archive.
					pass

			try:
				meta = s.readmeta(self)
				if s.source:
					chapter = s.readchapter(self, meta)
				else:
					chapter = s.catchapters(self, meta)
			except KeyError:
				pass
			else:
				return self.cp_send_html(ctl, s.depth, chapter, s.factorpath(), meta[2])

			html = b'<html><head><title>Not Found</title></head><body>no such resource</body></html>'
			ctl.http_set_response(b'404', b'NOT FOUND', len(html), cotype=b'text/html')
			ctl.http_iterate_output([(html,)])
		except:
			import traceback
			traceback.print_exc()
			ctl.http_write_text("error")
