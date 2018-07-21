"""
# Update the JavaScript file in the target data set.
"""

if __name__ == '__main__':
	def install():
		import sys
		from ...filesystem import library as libfs
		from ...system import files
		from ...system import python
		from ...system import libfactor
		from .. import libif

		cmd, target = sys.argv
		r = files.Path.from_path(target)
		js = r / 'application' / 'javascript'

		d = libfs.Dictionary.use(js)
		fr = libfactor.inducted(python.Import.from_module(libif)) / 'pf.lnk'
		with fr.open('rb') as f:
			d[b'factor.js'] = f.read()

	install()
