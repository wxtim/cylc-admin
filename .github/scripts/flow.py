import pytest
import cylc
import sys
from pathlib import Path

Path('/home/h02/tpilling/metomi/cylc-flow/tests/integration/utils/__init__').touch()

sys.path.append('/home/h02/tpilling/metomi/cylc-flow/tests/integration')

from utils import flow_tools
