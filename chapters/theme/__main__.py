# Update the CSS file in the target data set.
if __name__ == '__main__':
	def install():
		import sys
		from ...filesystem import library as libfs
		from ...system import libfactor
		from ...system import python
		from ...system import files
		from .. import theme

		cmd, target = sys.argv
		r = files.Path.from_path(target)
		css = r / 'text' / 'css'

		d = libfs.Dictionary.use(css)
		fr = libfactor.inducted(python.Import.from_module(theme)) / 'pf.lnk'
		with fr.open('rb') as f:
			d[b'factor.css'] = f.read()

	install()
	del install
