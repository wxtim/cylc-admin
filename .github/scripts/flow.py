import pytest
import cylc
import sys


@pytest.mark.parametrize('planet', [('Earth'), ('Venus')])
def test_foo(planet):
    print(cylc.__file__, file=sys.stderr)
    print(f'Hello {planet}')


async def test_cylc_workflow(flow, scheduler, run, complete):
    id_ = flow({
        'scheduling': {'R1': 'foo'},
    })
    schd = scheduler(id_)
    async with schd:
        complete(schd)

