import pytest
import cylc
import sys
from pathlib import Path
import os
import asyncio
from cylc.flow.scheduler import Scheduler
from cylc.flow.scheduler_cli import RunOptions

WORKSPACE = Path(os.environ['GITHUB_WORKSPACE'])
UTILS = WORKSPACE / 'cylc-flow/tests/integration/utils'
(UTILS / '__init__').touch()

sys.path.append(UTILS.parent)
from utils import flow_tools

RUN_DIR = WORKSPACE / 'cylc-run'
RUN_DIR.touch()

myflow = flow_tools._make_flow(
    RUN_DIR,
    '',   # We can safely leave this blank if we use id_
    {
        'scheduling': {'graph': {'R1': 'task_foo'}},
        'runtime': {'foo': {}}
    },
    id_='example1'
)

schd = Scheduler(myflow, RunOptions())


async def play():
    async with flow_tools._start_flow(None, schd):
        print(schd)
        [print(t) for t in schd.pool.get_tasks()]

asyncio.run(play())
