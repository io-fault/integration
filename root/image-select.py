import sys
import os
from fault.system import identity
from fault.system import factors
from fault.system import files
from fault.project.types import Variants

sysctx = os.environ['SYSTEMCONTEXT']
sysint = os.environ['SYSTEM_PRODUCT']

factors.context.connect(files.root@sysctx)
factors.context.connect(files.root@sysint)
factors.context.load()

fv = Variants(*identity.root_execution_context())
for fp in sys.argv[1:]:
	print(factors.context.image(fv, fp))
