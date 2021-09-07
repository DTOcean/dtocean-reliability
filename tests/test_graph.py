# -*- coding: utf-8 -*-

#    Copyright (C) 2021 Mathew Topper
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


import pytest

from dtocean_reliability.graph import Link, Component


@pytest.fixture
def pool_dummy():
    return None

def test_Link_len():
    
    link = Link()
    link.add_item("item")
    
    assert len(link) == 1


def test_Link_str():
    
    link = Link("test")
    link.add_item("item")
    
    assert str(link)


def test_Component_init():
    test = Component("test")
    assert isinstance(test, Component)


def test_Component_get_failure_rate_none():
    test = Component("test")
    assert test.get_failure_rate() is None


def test_Component_get_mttf_none(pool_dummy):
    test = Component("test")
    assert test.get_mttf(pool_dummy) is None


def test_Component_get_mttf(pool_dummy):
    test = Component("test")
    test.set_failure_rate(2)
    assert test.get_mttf(pool_dummy) == 0.5 * 1e6


def test_Component_get_rpn_none(pool_dummy):
    test = Component("test")
    assert test.get_rpn(pool_dummy) is None


def test_Component_get_rpn(pool_dummy):
    test = Component("test")
    test.set_failure_rate(2)
    assert test.get_rpn(pool_dummy) == 6


def test_Component_get_reliability_none(pool_dummy):
    test = Component("test")
    assert test.get_reliability(pool_dummy, 1) is None


def test_Component_get_reliability(pool_dummy):
    test = Component("test")
    test.set_failure_rate(0)
    assert test.get_reliability(pool_dummy, 1) == 1


def test_Component_reset(pool_dummy):
    test = Component("test")
    test.set_failure_rate(2)
    test.reset(pool_dummy)
    assert test.get_failure_rate(pool_dummy) is None


def test_Component_display_none(pool_dummy):
    test = Component("test")
    assert test.display(pool_dummy) == "'test'"


@pytest.mark.parametrize("label, expected", [
    ('test', 1),
    ('other', 0),
])
def test_Component_get_probability_proportion(pool_dummy, label, expected):
    test = Component("test")
    assert test.get_probability_proportion(pool_dummy, label) == expected



