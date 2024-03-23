import pytest

from util import *


@pytest.mark.parametrize(
    "block_size, expected",
    [(1, ["s"]), (2, ["s", "e"]), (3, ["s", "m_0", "e"]), (4, ["s", "m_0", "m_1", "e"])],
)
def test_calculate_positions(block_size:int, expected:list[str]):
    assert calculate_positions(block_size) == expected


@pytest.mark.parametrize(
    "block_size, expected",
    [
        (1, ["m_0"]),
        (2, ["m_0", "m_1"]),
        (3, ["m_0", "m_1", "m_2"]),
        (4, ["m_0", "m_1", "m_2", "m_3"]),
    ],
)
def test_calculate_positions_for_block_size_greater3(block_size, expected:list[str]):
    assert calculate_positions_for_block_size_greater3(block_size) == expected
