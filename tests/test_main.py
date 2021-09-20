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

from collections import Counter # Required for eval of text files

import numpy as np
import pytest

from dtocean_reliability.main import Network
from dtocean_reliability.parse import SubNetwork


@pytest.fixture(scope="module")
def database():
    
    return {'id1': {'item10': {'failratecrit': [4, 5, 6],
                               'failratenoncrit': [1, 2, 3]},
                    },
            'id2': {'item10': {'failratecrit': [4, 5, 6],
                               'failratenoncrit': [1, 2, 3]},
                    },
            'id3': {'item10': {'failratecrit': [4, 5, 6],
                               'failratenoncrit': [1, 2, 3]},
                    }}


@pytest.fixture(scope="module")
def database_partial():
    
    return {'id1': {'item10': {'failratecrit': [-1, -1, -1],
                               'failratenoncrit': [-1, 2, -1]},
                    },
            'id2': {'item10': {'failratecrit': [-1, -1, -1],
                               'failratenoncrit': [-1, 2, -1]},
                    },
            'id3': {'item10': {'failratecrit': [-1, -1, -1],
                               'failratenoncrit': [-1, 2, -1]},
                    }}


@pytest.fixture(scope="module")
def database_empty():
    
    return {'id1': {'item10': {'failratecrit': [-1, -1, -1],
                               'failratenoncrit': [-1, -1, -1]},
                    },
            'id2': {'item10': {'failratecrit': [-1, -1, -1],
                               'failratenoncrit': [-1, -1, -1]},
                    },
            'id3': {'item10': {'failratecrit': [-1, -1, -1],
                               'failratenoncrit': [-1, -1, -1]},
                    }}


@pytest.fixture
def electrical_network():
    
    dummyelechier = {'array': {'Export cable': [['id1']],
                               'Substation': ['id2'],
                               'layout': [['device001']]},
                     'device001': {'Elec sub-system': ['id3']}}
    dummyelecbom = {'array': {'Export cable': {'marker': [[0]],
                                               'quantity':
                                                       Counter({'id1': 1})},
                              'Substation': {'marker': [1],
                                             'quantity': Counter({'id2': 1})}},
                    'device001': {'marker': [2],
                                  'quantity': Counter({'id3': 1})}}
    
    return SubNetwork(dummyelechier, dummyelecbom)


def test_network_no_inputs(database):
    
    with pytest.raises(ValueError) as excinfo:
        Network(database)
    
    assert "At least one network input" in str(excinfo.value)


def test_network_set_failure_rates_inplace(database, electrical_network):
    
    network = Network(database, electrical_network)
    network.set_failure_rates(inplace=True)
    
    test = network.get_subsystem_metrics("Elec sub-system")
    assert test['MTTF'][0] >= 0


@pytest.mark.parametrize("severitylevel, expected", [
    ('critical', 3 * 5 / 1e6),
    ('noncritical', 3 * 2 / 1e6),
])
def test_network_set_failure_rates_severitylevel(database,
                                                 electrical_network,
                                                 severitylevel,
                                                 expected):
    
    network = Network(database, electrical_network)
    network.set_failure_rates(severitylevel=severitylevel, inplace=True)
    
    test = network.get_systems_metrics()
    assert np.isclose(test['lambda'][0], expected)


def test_network_set_failure_rates_k_factors(database,
                                             electrical_network):
    
    k_factors = {0: 2, 1: 2}
    
    network = Network(database, electrical_network)
    network.set_failure_rates(k_factors=k_factors, inplace=True)
    
    test = network.get_systems_metrics()
    assert np.isclose(test['lambda'][0], 25 / 1e6)


def test_network_set_failure_rates_severitylevel_unknown(database,
                                                         electrical_network):
    
    network = Network(database, electrical_network)
    
    with pytest.raises(ValueError) as excinfo:
        network.set_failure_rates(severitylevel="unknown", inplace=True)
    
    assert "may only take values 'critical'" in str(excinfo.value)


@pytest.mark.parametrize("calcscenario, expected", [
    ('lower', 3 * 4 / 1e6),
    ('mean', 3 * 5 / 1e6),
    ('upper', 3 * 6 / 1e6),
])
def test_network_set_failure_rates_calcscenario(database,
                                                electrical_network,
                                                calcscenario,
                                                expected):
    
    network = Network(database, electrical_network)
    network.set_failure_rates(calcscenario=calcscenario, inplace=True)
    
    test = network.get_systems_metrics()
    assert np.isclose(test['lambda'][0], expected)


@pytest.mark.parametrize("calcscenario, expected", [
    ('lower', 3 * 2 / 1e6),
    ('mean', 3 * 2 / 1e6),
    ('upper', 3 * 2 / 1e6),
])
def test_network_set_failure_rates_partial(database_partial,
                                           electrical_network,
                                           calcscenario,
                                           expected):
    
    network = Network(database_partial, electrical_network)
    network.set_failure_rates(calcscenario=calcscenario, inplace=True)
    
    test = network.get_systems_metrics()
    assert np.isclose(test['lambda'][0], expected)


def test_network_set_failure_rates_empty(database_empty,
                                         electrical_network):
    
    network = Network(database_empty, electrical_network)
    
    with pytest.raises(RuntimeError) as excinfo:
        network.set_failure_rates(inplace=True)
    
    assert "No failure rate data is set" in str(excinfo.value)


@pytest.mark.parametrize("severitylevel, expected", [
    ('critical', 8),
    ('noncritical', 3),
])
def test_network_get_systems_metrics_rpn(database,
                                         electrical_network,
                                         severitylevel,
                                         expected):
    
    network = Network(database, electrical_network)
    network.set_failure_rates(severitylevel=severitylevel, inplace=True)
    
    test = network.get_systems_metrics()
    assert np.isclose(test['RPN'][0], expected)


def test_network_get_subsystem_metrics_bad_system_name(database,
                                                       electrical_network):
    
    network = Network(database, electrical_network)
    network.set_failure_rates(inplace=True)
    
    with pytest.raises(ValueError) as excinfo:
        network.get_subsystem_metrics("device")
    
    assert "may not contain reserved keywords" in str(excinfo.value)


def test_network_display(database, electrical_network):
    
    network = Network(database, electrical_network)
    network.set_failure_rates(inplace=True)
    test = network.display()
    
    assert test


def test_network_len(database, electrical_network):
    network = Network(database, electrical_network)
    assert len(network) > 0
