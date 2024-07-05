import pytest


@pytest.mark.parametrize('planet', [('Earth'), ('Venus')])
def test_foo(planet):
    print(f'Hello {planet}')
