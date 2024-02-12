"""
# Structures for supporting the calculations and representations of factor statistics.
"""
from collections.abc import Sequence

from fault.context import tools

@tools.struct()
class Product(object):
	"""
	# Triple of integers representing a total product, subject factor, and integer count.
	# Provides the core structure for the statistical elements used by &..metrics.

	# The (vector) integers are represented using a triple as the vectors are analyzed from
	# three different perspectives in order to collect the information provided by
	# &Statistics.

	# [ Properties ]
	# /total/
		# The integer product calculated by multiplying &subject and &count.
	# /subject/
		# The factor being multiplied by &count.
		# Often, the subject is calculated or recalculated by dividing the
		# total with the count. &rational should be used in order to obtain an
		# accurate &subject value.
	# /count/
		# The number of times &subject occurred in a vector.
		# The factor used to multiply &subject.
	"""
	total:(int)
	subject:(int)
	count:(int)

	@classmethod
	def from_vectors(Class, totals, counts, sum=sum):
		"""
		# Construct an aggregate from a pair of vectors of totals and counts.
		"""
		t = sum(totals)
		c = sum(counts)
		return Class(t, t // c, c)

	@classmethod
	def from_factors(Class, subject, count):
		return Class(subject*count, subject, count)

	@staticmethod
	def frequency(p):
		"""
		# Sort key for frequency profiles.
		"""
		return (p.count, p.subject)

	@staticmethod
	def value(p):
		"""
		# Sort key for subject profiles.
		"""
		return p.subject

	def __repr__(self):
		return ''.join([
			"(product",
			"@", str(self.total),
			"|", str(self.subject),
			"*", str(self.count),
			")",
		])

	@property
	def remainder(self):
		"""
		# The numerator of the average's fractional component.
		# Where &count is the implied denominator.
		"""
		return self.total - (self.count * self.subject)

	@property
	def rational(self):
		"""
		# Calculate the, true, &subject based on &total and &count.
		"""
		return (self.remainder / self.count) + self.subject

	def add(self, values):
		"""
		# Apply a sequence of distinct values to the product's &total.

		# The &subject is re-calculated based on the new total.
		"""
		c = 0
		v = 0
		I = int
		G = getattr
		for i in values:
			c += G(i, 'count', 1)
			v += I(i)

		v += self.total
		c += self.count
		return self.__class__(v, v // c, c)

	def adjust(self, delta):
		"""
		# Increment the &count and perform the corresponding adjustments to the &total.
		# Given delta
		"""
		return self.__class__(
			self.total + (self.subject * delta),
			self.subject,
			self.count + delta
		)

	def __int__(self):
		return self.total

@tools.struct()
class Profile(object):
	"""
	# Common statistics regarding a set of values.

	# [ Properties ]
	# /total/
		# Sum of the ordering key.
	# /edges/
		# The minimums and maximums of the value set.
	"""

	total:(int)
	edges:(Sequence[Product])

	@property
	def minimum(self):
		"""
		# The lowest value recorded in &edges.
		"""
		return self.edges[0].subject

	@property
	def maximum(self):
		"""
		# The highest value recorded in &edges.
		"""
		return self.edges[-1].subject

	@property
	def span(self):
		"""
		# The difference between the maximum and the minimum.
		"""
		return self.edges[0].subject - self.edges[-1].subject

	def imin(self):
		"""
		# Iterator selecting the minimum &Products retained by the profile.
		"""
		return self.edges[:len(self.edges)//2]

	def imax(self):
		"""
		# Iterator selecting the maximum &Products retained by the profile.
		"""
		return self.edges[len(self.edges)//2:]

@tools.struct()
class Statistics(object):
	"""
	# &Profile set and measurements for calculating statistical properties of a vector.

	# [ Properties ]
	# /count/
		# The original unique number of elements that the profiles were built from.
	# /deltas/
		# Sum of the distances from the average.
		# For distance measurement.
	# /areas/
		# Sum of the areas, squares, from the average.
		# For standard deviation measurement.
	# /frequency/
		# Profile of the numbers organized by their frequencies.
		# Totals the counts.
	# /subjective/
		# Profile of the numbers organized by their unique instances.
		# Totals the subjects.
	# /magnitude/
		# Profile of the numbers organized by their total values.
		# Totals the totals.
	"""
	count:(int)
	deltas:(float)
	areas:(float)
	subjective:(Profile)
	magnitude:(Profile)
	frequency:(Profile)

	@property
	def mean(self) -> Product:
		"""
		# The &Product representing the mean of the values.
		# Provides access to the total and count of values.
		"""
		m = self.magnitude
		f = self.frequency
		return Product(m.total, m.total//f.total, f.total)

	def profiles(self):
		yield ('subjective', self.subjective)
		yield ('magnitude', self.magnitude)
		yield ('frequency', self.frequency)

	def __str__(self):
		i = self.summary()
		avg = '%.2f' %(i['average-value'],)
		dis = '%.2f' %(i['distance'],)
		dev = '%.2f' %(i['deviation'],)
		return ''.join(map(str, [
			i['minimum-value'],
			' -> ', avg, '+', dev, '-', dis,
			' -> ', i['maximum-value'],
			': ', i['total'],
			'/', i['count'],
			'/', i['unique'],
		]))

	def summary(self, deviation=2):
		c = self.count
		s = self.subjective
		f = self.frequency
		m = self.mean
		tc = m.count

		return {
			'total': m.total,
			'count': tc,
			'unique': c,
			'minimum-value': s.minimum,
			'average-value': m.rational,
			'maximum-value': s.maximum,
			'average-frequency': f.total / c,
			'deviation': (self.areas / tc) ** (1/deviation),
			'distance': (self.deltas / tc),
		}
