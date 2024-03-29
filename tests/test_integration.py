# -*- coding: utf-8 -*-

#    Copyright (C) 2016-2021 Mathew Topper
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

# pylint: disable=eval-used

import os
import glob
import runpy
from collections import Counter # pylint: disable=unused-import

import pytest

from dtocean_reliability import Network, SubNetwork

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = os.path.join(THIS_DIR, "..", "example_data")
EXAMPLE_DIR =  os.path.join(THIS_DIR, "..", "examples")

SCRIPTS = glob.glob(os.path.join(EXAMPLE_DIR, "*.py"))

@pytest.mark.parametrize('script', SCRIPTS)
def test_examples(script):
    runpy.run_path(script)


def test_full_network():
    
    dummydb = eval(open(os.path.join(DATA_DIR, 'dummydb.txt')).read())
    dummyelechier = eval(open(os.path.join(DATA_DIR,
                                           'dummyelechier.txt')).read())
    dummyelecbom = eval(open(os.path.join(DATA_DIR,
                                          'dummyelecbom.txt')).read())
    dummymoorhier = eval(open(os.path.join(DATA_DIR,
                                           'dummymoorhier.txt')).read())
    dummymoorbom = eval(open(os.path.join(DATA_DIR,
                                          'dummymoorbom.txt')).read())
    dummyuserhier = eval(open(os.path.join(DATA_DIR,
                                           'dummyuserhier.txt')).read())
    dummyuserbom = eval(open(os.path.join(DATA_DIR,
                                          'dummyuserbom.txt')).read())
    
    electrical_network = SubNetwork(dummyelechier, dummyelecbom)
    moorings_network = SubNetwork(dummymoorhier, dummymoorbom)
    user_network = SubNetwork(dummyuserhier, dummyuserbom)
    
    network = Network(dummydb,
                      electrical_network,
                      moorings_network,
                      user_network)
    
    critical_network = network.set_failure_rates()
    
    systems_metrics = critical_network.get_systems_metrics(720)
    elec_metrics = critical_network.get_subsystem_metrics("Elec sub-system",
                                                          8760)
    mooring_metrics = critical_network.get_subsystem_metrics('Station keeping',
                                                             8760)
    pto_metrics = critical_network.get_subsystem_metrics('Pto',
                                                         8760)
    
    assert systems_metrics is not None
    assert elec_metrics is not None
    assert mooring_metrics is not None
    assert pto_metrics is not None


def test_electrical_only():
    
    dummydb = eval(open(os.path.join(DATA_DIR, 'dummydb.txt')).read())
    dummyelechier = eval(open(os.path.join(DATA_DIR,
                                           'dummyelechier.txt')).read())
    dummyelecbom = eval(open(os.path.join(DATA_DIR,
                                          'dummyelecbom.txt')).read())
    
    electrical_network = SubNetwork(dummyelechier, dummyelecbom)
    moorings_network = None
    user_network = None
    
    network = Network(dummydb,
                      electrical_network,
                      moorings_network,
                      user_network)
    
    critical_network = network.set_failure_rates()
    
    systems_metrics = critical_network.get_systems_metrics(720)
    elec_metrics = critical_network.get_subsystem_metrics("Elec sub-system",
                                                          8760)
    mooring_metrics = critical_network.get_subsystem_metrics('Station keeping',
                                                             8760)
    pto_metrics = critical_network.get_subsystem_metrics('Pto',
                                                         8760)
    
    assert systems_metrics is not None
    assert elec_metrics is not None
    assert mooring_metrics is None
    assert pto_metrics is None


def test_moorings_only():
    
    dummydb = eval(open(os.path.join(DATA_DIR, 'dummydb.txt')).read())
    dummymoorhier = eval(open(os.path.join(DATA_DIR,
                                           'dummymoorhier_noelec.txt')).read())
    dummymoorbom = eval(open(os.path.join(DATA_DIR,
                                          'dummymoorbom_noelec.txt')).read())
    
    electrical_network = None
    moorings_network = SubNetwork(dummymoorhier, dummymoorbom)
    user_network = None
    
    network = Network(dummydb,
                      electrical_network,
                      moorings_network,
                      user_network)
    
    critical_network = network.set_failure_rates()
    
    systems_metrics = critical_network.get_systems_metrics(720)
    elec_metrics = critical_network.get_subsystem_metrics("Elec sub-system",
                                                          8760)
    mooring_metrics = critical_network.get_subsystem_metrics('Station keeping',
                                                             8760)
    pto_metrics = critical_network.get_subsystem_metrics('Pto',
                                                         8760)
    
    assert systems_metrics is not None
    assert elec_metrics is None
    assert mooring_metrics is not None
    assert pto_metrics is None


def test_user_only():
    
    dummydb = eval(open(os.path.join(DATA_DIR, 'dummydb.txt')).read())
    dummyuserhier = eval(open(os.path.join(DATA_DIR,
                                           'dummyuserhier.txt')).read())
    dummyuserbom = eval(open(os.path.join(DATA_DIR,
                                          'dummyuserbom.txt')).read())
    
    electrical_network = None
    moorings_network = None
    user_network = SubNetwork(dummyuserhier, dummyuserbom)
    
    network = Network(dummydb,
                      electrical_network,
                      moorings_network,
                      user_network)
    
    critical_network = network.set_failure_rates()
    
    systems_metrics = critical_network.get_systems_metrics(720)
    elec_metrics = critical_network.get_subsystem_metrics("Elec sub-system",
                                                          8760)
    mooring_metrics = critical_network.get_subsystem_metrics('Station keeping',
                                                             8760)
    pto_metrics = critical_network.get_subsystem_metrics('Pto',
                                                         8760)
    
    assert systems_metrics is not None
    assert elec_metrics is None
    assert mooring_metrics is  None
    assert pto_metrics is not None


def test_electrical_user():
    
    dummydb = eval(open(os.path.join(DATA_DIR, 'dummydb.txt')).read())
    dummyelechier = eval(open(os.path.join(DATA_DIR,
                                           'dummyelechier.txt')).read())
    dummyelecbom = eval(open(os.path.join(DATA_DIR,
                                          'dummyelecbom.txt')).read())
    dummyuserhier = eval(open(os.path.join(DATA_DIR,
                                           'dummyuserhier.txt')).read())
    dummyuserbom = eval(open(os.path.join(DATA_DIR,
                                          'dummyuserbom.txt')).read())
    
    electrical_network = SubNetwork(dummyelechier, dummyelecbom)
    moorings_network = None
    user_network = SubNetwork(dummyuserhier, dummyuserbom)
    
    network = Network(dummydb,
                      electrical_network,
                      moorings_network,
                      user_network)
    
    critical_network = network.set_failure_rates()
    
    systems_metrics = critical_network.get_systems_metrics(720)
    elec_metrics = critical_network.get_subsystem_metrics("Elec sub-system",
                                                          8760)
    mooring_metrics = critical_network.get_subsystem_metrics('Station keeping',
                                                             8760)
    pto_metrics = critical_network.get_subsystem_metrics('Pto',
                                                         8760)
    
    assert systems_metrics is not None
    assert elec_metrics is not None
    assert mooring_metrics is None
    assert pto_metrics is not None


def test_moorings_user():
    
    dummydb = eval(open(os.path.join(DATA_DIR, 'dummydb.txt')).read())
    dummymoorhier = eval(open(os.path.join(DATA_DIR,
                                           'dummymoorhier_noelec.txt')).read())
    dummymoorbom = eval(open(os.path.join(DATA_DIR,
                                          'dummymoorbom_noelec.txt')).read())
    dummyuserhier = eval(open(os.path.join(DATA_DIR,
                                           'dummyuserhier.txt')).read())
    dummyuserbom = eval(open(os.path.join(DATA_DIR,
                                          'dummyuserbom.txt')).read())
    
    electrical_network = None
    moorings_network = SubNetwork(dummymoorhier, dummymoorbom)
    user_network = SubNetwork(dummyuserhier, dummyuserbom)
    
    network = Network(dummydb,
                      electrical_network,
                      moorings_network,
                      user_network)
    
    critical_network = network.set_failure_rates()
    
    systems_metrics = critical_network.get_systems_metrics(720)
    elec_metrics = critical_network.get_subsystem_metrics("Elec sub-system",
                                                          8760)
    mooring_metrics = critical_network.get_subsystem_metrics('Station keeping',
                                                             8760)
    pto_metrics = critical_network.get_subsystem_metrics('Pto',
                                                         8760)
    
    assert systems_metrics is not None
    assert elec_metrics is None
    assert mooring_metrics is not None
    assert pto_metrics is not None


def test_integerdb_keys():
    
    dummydb = eval(open(os.path.join(DATA_DIR, 'dummydb_intkey.txt')).read())
    dummyelechier = eval(open(os.path.join(DATA_DIR,
                                           'dummyelechier_intkey.txt')).read())
    dummyelecbom = eval(open(os.path.join(DATA_DIR,
                                          'dummyelecbom_intkey.txt')).read())
    
    electrical_network = SubNetwork(dummyelechier, dummyelecbom)
    moorings_network = None
    user_network = None
    
    network = Network(dummydb,
                      electrical_network,
                      moorings_network,
                      user_network)
    
    critical_network = network.set_failure_rates()
    
    systems_metrics = critical_network.get_systems_metrics(720)
    elec_metrics = critical_network.get_subsystem_metrics("Elec sub-system",
                                                          8760)
    mooring_metrics = critical_network.get_subsystem_metrics('Station keeping',
                                                             8760)
    pto_metrics = critical_network.get_subsystem_metrics('Pto',
                                                         8760)
    
    assert systems_metrics is not None
    assert elec_metrics is not None
    assert mooring_metrics is None
    assert pto_metrics is None


def test_fixed():
    
    dummydb = eval(open(os.path.join(DATA_DIR, 'dummydb.txt')).read())
    dummymoorhier = eval(open(os.path.join(DATA_DIR,
                                           'dummymoorhier_fixed.txt')).read())
    dummymoorbom = eval(open(os.path.join(DATA_DIR,
                                          'dummymoorbom_fixed.txt')).read())
    
    electrical_network = None
    moorings_network = SubNetwork(dummymoorhier, dummymoorbom)
    user_network = None
    
    network = Network(dummydb,
                      electrical_network,
                      moorings_network,
                      user_network)
    
    critical_network = network.set_failure_rates()
    
    systems_metrics = critical_network.get_systems_metrics(720)
    elec_metrics = critical_network.get_subsystem_metrics("Elec sub-system",
                                                          8760)
    foundation_metrics = critical_network.get_subsystem_metrics('Foundation',
                                                                8760)
    pto_metrics = critical_network.get_subsystem_metrics('Pto',
                                                         8760)
    
    assert systems_metrics is not None
    assert elec_metrics is None
    assert foundation_metrics is not None
    assert pto_metrics is None


def test_no_subhubs():
    
    dummydb = eval(open(os.path.join(DATA_DIR, 'dummydb.txt')).read())
    dummyelechier = eval(open(os.path.join(DATA_DIR,
                                           'dummyelechier_nosubs.txt')).read())
    dummyelecbom = eval(open(os.path.join(DATA_DIR,
                                          'dummyelecbom_nosubs.txt')).read())
    
    electrical_network = SubNetwork(dummyelechier, dummyelecbom)
    moorings_network = None
    user_network = None
    
    network = Network(dummydb,
                      electrical_network,
                      moorings_network,
                      user_network)
    
    critical_network = network.set_failure_rates()
    
    systems_metrics = critical_network.get_systems_metrics(720)
    elec_metrics = critical_network.get_subsystem_metrics("Elec sub-system",
                                                          8760)
    mooring_metrics = critical_network.get_subsystem_metrics('Station keeping',
                                                             8760)
    pto_metrics = critical_network.get_subsystem_metrics('Pto',
                                                         8760)
    
    assert systems_metrics is not None
    assert elec_metrics is not None
    assert mooring_metrics is None
    assert pto_metrics is None
