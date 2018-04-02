"""
# Metrics adapter for LLVM instrumentation.

# Manages the initialization of LLVM profile data collection and necessary postprocessing (llvm-profdata merge).
"""
import os
import subprocess
import importlib
import contextlib
import itertools
import collections

from fault.routes import library as libroutes
from fault.development import coverage
from fault.development import metrics
from fault.system import library as libsys

def postprocess(path, output, *inputs, name='llvm-profdata'):
	"""
	# Merge a set of collected LLVM instrumentation metrics into a single file.

	# This command is also used to prepare a single metrics file for data extraction.
	"""

	prefix = [path, 'merge', '-instr', '-output=' + str(output)]
	prefix.extend(inputs)
	return prefix

def extract_counters(llvm, command_path, shared_object, raw_profile_data_path):
	"""
	# Extract the merged profile data written by the LLVM instrumentation.
	"""

	with libroutes.File.temporary() as tmp:
		target = tmp / 'llvm.mpd'
		merged = str(target)
		cmd = postprocess(command_path, merged, str(raw_profile_data_path))
		sp = subprocess.Popen(cmd)
		sp.wait()

		# Extract all the necessary information.
		counters = llvm.extract_counters(str(shared_object), merged)

	return dict(counters)

class Probe(metrics.Probe):
	@contextlib.contextmanager
	def setup(self, context, telemetry, data):
		self.merge_command = data['merge']
		r = None

		try:
			self.module = importlib.import_module('f_telemetry.'+self.name)
			os.environ['LLVM_PROFILE_FILE'] = str(telemetry / '.llvm.profraw')
			r = (yield None)
		finally:
			pass

	@contextlib.contextmanager
	def connect(self, harness, measures):
		try:
			# Update trap file.
			os.environ['LLVM_PROFILE_FILE'] = str(measures / '.llvm.profraw')
			yield None
		finally:
			data = collections.defaultdict(collections.Counter)
			for module in harness.imports:
				if '_fault_metrics_write' in module.__dict__:
					module._llvm_metrics_path = str(measures / self.name / module.__name__)
					module._fault_metrics_set_path(module._llvm_metrics_path)
					module._fault_metrics_write()
					module._fault_metrics_reset()
					module._fault_metrics_set_path(str(measures/'.llvm.profraw'))

	def project(self, telemetry, route, frames):
		data = collections.defaultdict(dict)
		self.regions = {}
		self.function_counters = set()

		for factor, (route, target, sources) in frames.items():
			if not target.exists():
				continue

			region_map = self.module.list_regions(str(target))
			self.function_counters.update([
				(files[0],) + areas[0][:2]
				for (files, record_id, areas) in region_map
			])

			for files, record_id, counters in region_map:
				# Skip the first counter as it always represents the function as a whole.
				for startl, startc, stopl, stopc, xpfile_id, cfile_id, typ in counters[1:]:
					path = files[cfile_id]
					data[path][(startl, startc)] = ((startl, startc, stopl, stopc), typ)

		return data

	def profile(self, targets, measures):
		return ()

	def counters(self, targets, measures):
		"""
		# Postprocess the per-module output and join it with the region information
		# embedded in the system image.
		"""

		for factor, data_file in self.join(measures):
			system_image = targets[factor][1]
			counters = extract_counters(self.module, self.merge_command, system_image, data_file)

			for path, seq in counters.items():
				m = collections.Counter(dict([
					((lineno, colno,), count)
					for (lineno, colno, count) in seq
				]))

				# Initial counters are for functions, not expressions.
				keyset = set([(path,) + k for k in m.keys()])
				profile_keys = self.function_counters.intersection(keyset)
				profile_data = [(key, m.pop(key[1:])) for key in profile_keys]

				yield (path, m)
