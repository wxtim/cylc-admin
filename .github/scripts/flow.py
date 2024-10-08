import pytest
import cylc
import sys
from pathlib import Path
import os
import asyncio
from cylc.flow.scheduler import Scheduler
from cylc.flow.scheduler_cli import RunOptions

WORKSPACE = Path('/home/runner/work/cylc-admin/cylc-admin/')

UTILS = WORKSPACE / 'cylc-flow/tests/integration/utils'
(UTILS / '__init__').touch()
(UTILS.parent / '__init__').touch()

sys.path.append(str(UTILS.parent))
from utils import flow_tools

RUN_DIR = WORKSPACE / 'cylc-run'
RUN_DIR.mkdir()

myflow = flow_tools._make_flow(
    RUN_DIR,
    '',   # We can safely leave this blank if we use id_
    {
        'scheduling': {'graph': {'R1': 'task_foo'}},
        'runtime': {'foo': {}}
    },
    id_='example1'
)

[print(i) for i in RUN_DIR.rglob('*')]

schd = Scheduler(myflow, RunOptions())


async def play():
    async with flow_tools._start_flow(None, schd):
        print(schd)
        [print(t) for t in schd.pool.get_tasks()]

asyncio.run(play())
