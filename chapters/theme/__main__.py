# Update the CSS file in the target data set.
if __name__ == '__main__':
	def install():
		import sys
		from ...filesystem import library as libfs
		from ...routes import library as libroutes
		from ...system import libfactor
		from .. import theme

		cmd, target = sys.argv
		r = libroutes.File.from_path(target)
		css = r / 'text' / 'css'

		d = libfs.Dictionary.use(css)
		fr = libfactor.reduction(None, 'host', 'optimal', theme)
		with fr.open('rb') as f:
			d[b'factor.css'] = f.read()
	install()
	del install
