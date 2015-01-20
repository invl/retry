import pytest

from retry import retry


def test_tries():
    hit = [0]

    @retry(tries=3, delay=0.1)
    def f():
        hit[0] += 1
        1 / 0

    with pytest.raises(ZeroDivisionError):
        f()
    assert hit[0] == 4
