"""
# Utility functions and classes for project and factor filtering cases.
"""
from fault.project import system as lsf
from fault.project import graph

class SQueue(object):
	"""
	# Queue implementation providing completion signalling interfaces consistent
	# with &graph.Queue.
	"""

	def __init__(self, sequence):
		self.items = list(sequence)
		self.count = len(self.items)

	def take(self, i):
		r = self.items[:i]
		del self.items[:i]
		return r

	def finish(self, *items):
		pass

	def terminal(self):
		return not self.items

	def status(self):
		return (self.count - len(self.items), self.count)

def check_keywords(keywords, name, Table=str.maketrans('_.-', '   ')):
	name_str = str(name)
	name_set = set(str(name).translate(Table).split())
	empty_constraints = 0

	for k in keywords:
		ccode = k[:1]

		if ccode == '@':
			if name_str == k[1:]:
				return True
		elif ccode == '.':
			if name_str.endswith(k[1:]):
				return True
		elif ccode == '+':
			# Whitelist
			if k[1:] in name_set:
				return True
		elif ccode == '-':
			# Blacklist
			if k[1:] in name_set:
				return False
		elif k in name_str:
			return True
		else:
			if k.strip() == '':
				empty_constraints += 1

	# False, normally. True when all the keywords were whitespace.
	return len(keywords) == empty_constraints

def projectvector(factors, projectname):
	try:
		# Exact project factor.
		return [
			factors.split(x)[1].identifier
			for x in [lsf.types.factor@projectname]
		]
	except LookupError:
		# Presume factor prefix match.
		return [
			pj.identifier for pj in factors.iterprojects()
			if str(pj.factor).startswith(projectname)
		]

def projectgraph(factors, projects):
	if projects:
		pvector = []
		for projectname in projects:
			pvector.extend(projectvector(factors, projectname))
		q = SQueue(pvector)
	else:
		q = graph.Queue()
		q.extend(factors)

	return q
