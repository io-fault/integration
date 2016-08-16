# Update the JavaScript file in the target data set.
if __name__ == '__main__':
	def install():
		import sys
		from ...filesystem import library as libfs
		from ...routes import library as libroutes
		from ...system import libfactor
		from .. import libif

		cmd, target = sys.argv
		r = libroutes.File.from_path(target)
		js = r / 'application' / 'javascript'

		d = libfs.Dictionary.use(js)
		with libfactor.reduction(None, 'host', 'optimal', module=libif).open('rb') as f:
			d[b'factor.js'] = f.read()

	install()
	del install