"""
# Check the XPath functions and some of the XSLT features.
"""
from .. import xslt as library

def test_Factor_duration(test):
	f = library.Factor()

	test/f.duration(None, 6000) == '6µs'

	# Hours are the largest unit in our reports.
	day = library.libtime.Measure.of(day=1)
	test/f.duration(None, str(int(day))) == '24 hours'

	c = library.libtime.Measure.of(day=1, minute=24, second=17, millisecond=403, microsecond=23)
	test/f.duration(None, str(int(c))) == '24 hours 24 minutes 17s 403ms 23µs'

	c = library.libtime.Measure.of(second=17, millisecond=403, microsecond=0, nanosecond=100)
	test/f.duration(None, str(int(c))) == '17s 403ms 100ns'

if __name__ == '__main__':
	from ...development import libtest; import sys
	libtest.execute(sys.modules[__name__])
