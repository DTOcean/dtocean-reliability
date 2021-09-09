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

import math

import pytest
import numpy as np
import graphviz as gv

from dtocean_reliability.graph import Link, Component, Serial, Parallel


@pytest.fixture
def pool_dummy():
    return None


@pytest.fixture
def pool():
    
    comp_zero = Component("zero")
    comp_zero.set_failure_rate(2)
    
    comp_one = Component("one")
    comp_one.set_failure_rate(2)
    
    pool = {0: comp_zero,
            1: comp_one}
    
    return pool


@pytest.fixture
def pool_zero():
    
    comp_zero = Component("zero")
    comp_zero.set_failure_rate(0)
    
    comp_one = Component("one")
    comp_one.set_failure_rate(0)
    
    pool = {0: comp_zero,
            1: comp_one}
    
    return pool


@pytest.fixture
def pool_serial():
    
    comp_zero = Component("zero")
    comp_zero.set_failure_rate(2)
    
    comp_one = Component("one")
    comp_one.set_failure_rate(2)
    
    comp_two = Component("two")
    comp_two.set_failure_rate(2)
    
    serial = Serial()
    serial.add_item(2)
    serial.add_item(3)
    
    pool = {0: comp_zero,
            1: serial,
            2: comp_one,
            3: comp_two}
    
    return pool



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


def test_Component_graph_no_failure_rate(pool_dummy):
    
    label = "test"
    test = Component(label)
    dot = gv.Digraph()
    handle = test.graph(pool_dummy, dot)
    
    assert handle in dot.source
    assert label in dot.source


def test_Component_graph_failure_rate(pool_dummy):
    
    label = "test"
    failure_rate = 2
    
    test = Component(label)
    test.set_failure_rate(failure_rate)
    dot = gv.Digraph()
    handle = test.graph(pool_dummy, dot)
    
    assert handle in dot.source
    assert label in dot.source
    assert str(failure_rate) in dot.source


def test_Component_str():
    label = "test"
    test = Component(label)
    assert label in str(test)


def test_Component_str_kfactor():
    kfactor = 1
    test = Component("test", kfactor=kfactor)
    assert "k-factor" in str(test)
    assert str(kfactor) in str(test)


def test_Serial_init():
    test = Serial("test")
    assert isinstance(test, Serial)


def test_Serial_get_failure_rate_none(pool):
    test = Serial("test")
    assert test.get_failure_rate(pool) is None


def test_Serial_get_mttf_none(pool):
    test = Serial("test")
    assert test.get_mttf(pool) is None


def test_Serial_get_rpn_none(pool):
    test = Serial("test")
    assert test.get_rpn(pool) is None


def test_Serial_get_rpn(pool):
    test = Serial("test")
    test.add_item(0)
    test.add_item(1)
    assert test.get_rpn(pool) == 6


def test_Serial_get_reliability_none(pool):
    test = Serial("test")
    assert test.get_reliability(pool, 1) is None


def test_Serial_get_reliability(pool_zero):
    test = Serial("test")
    test.add_item(0)
    test.add_item(1)
    assert test.get_reliability(pool_zero, 1) == 1


def test_Serial_reset(pool):
    test = Serial("test")
    test.add_item(0)
    test.add_item(1)
    test.reset(pool)
    assert test.get_failure_rate(pool) is None


def test_Serial_display_none(pool_dummy):
    test = Serial("test")
    assert test.display(pool_dummy) == "[test:]"


@pytest.mark.parametrize("label, expected", [
    ('test', 1),
    ('other', 0),
])
def test_Serial_get_probability_proportion_empty(pool_dummy, label, expected):
    test = Serial("test")
    assert test.get_probability_proportion(pool_dummy, label) == expected


def test_Serial_get_probability_proportion(pool):
    test = Serial("test")
    test.add_item(0)
    test.add_item(1)
    assert test.get_probability_proportion(pool, "zero") == 0.5


def test_Serial_get_probability_proportion_serial(pool_serial):
    test = Serial("test")
    test.add_item(0)
    test.add_item(1)
    result = test.get_probability_proportion(pool_serial, "zero")
    assert np.isclose(result, 1. / 3)


def test_Serial_graph_no_failure_rate(pool_dummy):
    
    label = "test"
    test = Serial(label)
    dot = gv.Digraph()
    handle = test.graph(pool_dummy, dot)
    
    assert handle in dot.source
    assert label in dot.source


def test_Serial_graph_failure_rate(pool_zero):
    
    label = "test"
    
    test = Serial(label)
    test.add_item(0)
    test.add_item(1)
    dot = gv.Digraph()
    handle = test.graph(pool_zero, dot)
    
    assert handle in dot.source
    assert label in dot.source
    assert str(0) in dot.source


def test_Serial_graph_system_without_names():
    
    comp_zero = Component("zero")
    comp_zero.set_failure_rate(2)
    
    comp_one = Component("one")
    comp_one.set_failure_rate(2)
    
    comp_two = Component("two")
    comp_two.set_failure_rate(2)
    
    serial = Serial()
    serial.add_item(0)
    
    parallel = Parallel()
    parallel.add_item(1)
    parallel.add_item(2)
    
    pool = {0: comp_zero,
            1: comp_one,
            2: comp_two,
            3: serial,
            4: parallel}
    
    test = Serial()
    test.add_item(3)
    test.add_item(4)
    dot = gv.Digraph()
    handle = test.graph(pool, dot)
    
    assert handle in dot.source
    assert "zero" in dot.source
    assert "two" in dot.source


def test_Serial_graph_system_two_levels():
    
    comp_zero = Component("zero")
    comp_zero.set_failure_rate(2)
    
    comp_one = Component("one")
    comp_one.set_failure_rate(2)
    
    comp_two = Component("two")
    comp_two.set_failure_rate(2)
    
    serial = Serial("name")
    serial_two = Serial("name")
    serial_two.add_item(0)
    serial_two.add_item(1)
    
    parallel = Parallel("name")
    parallel.add_item(2)
    parallel.add_item(3)
    
    pool = {0: comp_zero,
            1: comp_one,
            2: comp_two,
            3: serial_two,
            4: serial,
            5: parallel}
    
    test = Serial("top")
    test.add_item(4)
    test.add_item(5)
    dot = gv.Digraph()
    handle = test.graph(pool, dot, levels=2)
    
    assert handle in dot.source
    assert "two" in dot.source


def test_Serial_graph_system_with_names():
    
    comp_zero = Component("zero")
    comp_zero.set_failure_rate(2)
    
    comp_one = Component("one")
    comp_one.set_failure_rate(2)
    
    comp_two = Component("two")
    comp_two.set_failure_rate(2)
    
    serial = Serial("serial")
    serial.add_item(0)
    
    parallel = Parallel("parallel")
    parallel.add_item(1)
    parallel.add_item(2)
    
    pool = {0: comp_zero,
            1: comp_one,
            2: comp_two,
            3: serial,
            4: parallel}
    
    test = Serial()
    test.add_item(3)
    test.add_item(4)
    dot = gv.Digraph()
    handle = test.graph(pool, dot)
    
    assert handle in dot.source
    assert "serial" in dot.source
    assert "parallel" in dot.source


def test_Serial_graph_system_extra_level():
    
    comp_zero = Component("zero")
    comp_zero.set_failure_rate(2)
    
    comp_one = Component("one")
    comp_one.set_failure_rate(2)
    
    comp_two = Component("two")
    comp_two.set_failure_rate(2)
    
    parallel_two = Parallel("name")
    parallel_two.add_item(0)
    parallel_two.add_item(1)
    
    parallel = Parallel()
    parallel.add_item(2)
    parallel.add_item(3)
    
    pool = {0: comp_zero,
            1: comp_one,
            2: comp_two,
            3: parallel_two,
            4: parallel}

    test = Serial("top")
    test.add_item(4)
    dot = gv.Digraph()
    test.graph(pool, dot)
    
    assert "name" in dot.source


def test_Serial_str():
    label = "test"
    test = Serial(label)
    assert label in str(test)


def test_Parallel_init():
    test = Parallel("test")
    assert isinstance(test, Parallel)


def test_Parallel_get_failure_rate_none(pool):
    test = Parallel("test")
    assert test.get_failure_rate(pool) is None


def test_Parallel_get_mttf_none(pool):
    test = Parallel("test")
    assert test.get_mttf(pool) is None


def test_Parallel_get_mttf(pool):
    test = Parallel("test")
    test.add_item(0)
    test.add_item(1)
    assert np.isclose(test.get_mttf(pool), 3e6 / 4.)


def test_Parallel_get_rpn_none(pool):
    test = Parallel("test")
    assert test.get_rpn(pool) is None


def test_Parallel_get_rpn(pool):
    test = Parallel("test")
    test.add_item(0)
    test.add_item(1)
    assert test.get_rpn(pool) == 6


def test_Parallel_get_reliability_none(pool):
    test = Parallel("test")
    assert test.get_reliability(pool, 1) is None


def test_Parallel_get_reliability(pool):
    test = Parallel("test")
    test.add_item(0)
    test.add_item(1)
    assert test.get_reliability(pool, 1) == math.exp(-4 / 3e6)


def test_Parallel_reset(pool):
    test = Parallel("test")
    test.add_item(0)
    test.add_item(1)
    test.reset(pool)
    assert test.get_failure_rate(pool) is None


def test_Parallel_display_none(pool_dummy):
    test = Parallel("test")
    assert test.display(pool_dummy) == "<test:>"


def test_Parallel_display_failure_rate(pool):
    test = Parallel("test")
    test.add_item(0)
    assert test.display(pool) == "<test: 2.000000e-06: 'zero: 2.000000e-06'>"


def test_Parallel_graph_complex(pool):
    
    comp_zero = Component("zero")
    comp_zero.set_failure_rate(2)
    
    comp_one = Component("one")
    comp_one.set_failure_rate(2)
    
    comp_two = Component("two")
    comp_two.set_failure_rate(2)
    
    serial = Serial("name")
    serial.add_item(0)
    
    parallel = Parallel()
    parallel.add_item(1)
    parallel.add_item(2)
    
    pool = {0: comp_zero,
            1: comp_one,
            2: comp_two,
            3: serial,
            4: parallel}
    
    test = Parallel("top")
    test.add_item(3)
    test.add_item(4)
    dot = gv.Digraph()
    dot.attr(rankdir='LR')
    handle = test.graph(pool, dot, levels=2)
    
    assert handle in dot.source


@pytest.mark.parametrize("label, expected", [
    ('test', 1),
    ('other', 0),
])
def test_Parallel_get_probability_proportion_empty(pool_dummy, label, expected):
    test = Parallel("test")
    assert test.get_probability_proportion(pool_dummy, label) == expected


def test_Parallel_get_probability_proportion(pool):
    test = Parallel("test")
    test.add_item(0)
    test.add_item(1)
    assert test.get_probability_proportion(pool, "zero") == 0.5


def test_Parallel_get_probability_proportion_serial(pool_serial):
    test = Parallel("test")
    test.add_item(0)
    test.add_item(1)
    result = test.get_probability_proportion(pool_serial, "zero")
    assert np.isclose(result, 1. / 3)


def test_Parallel_graph_no_failure_rate(pool_dummy):
    
    label = "test"
    test = Parallel(label)
    dot = gv.Digraph()
    handle = test.graph(pool_dummy, dot)
    
    assert handle in dot.source
    assert label in dot.source


#def test_Parallel_graph_failure_rate(pool_zero):
#    
#    label = "test"
#    
#    test = Parallel(label)
#    test.add_item(0)
#    test.add_item(1)
#    dot = gv.Digraph()
#    handle = test.graph(pool_zero, dot)
#    
#    assert handle in dot.source
#    assert label in dot.source
#    assert str(0) in dot.source


def test_Parallel_str():
    label = "test"
    test = Parallel(label)
    assert label in str(test)
