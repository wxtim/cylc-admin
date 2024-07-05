import pytest


@pytest.mark.parametrize('planet', [('Earth'), ('Venus')])
def test_foo(planet):
    print(f'Hello {planet}')


async def test_cylc_workflow(flow, scheduler, run, complete):
    id_ = flow({
        'scheduling': {'R1': 'foo'},
    })
    schd = scheduler(id_)
    async with schd:
        complete(schd)

