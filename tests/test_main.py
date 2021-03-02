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

import os
from collections import Counter # Required for eval of text files

import pandas as pd

from dtocean_reliability import Network, SubNetwork
from dtocean_reliability.main import Variables, main

this_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(this_dir, "..", "example_data")

pd.set_option('display.max_columns', None)


def test_network():
    
    dummydb = eval(open(os.path.join(data_dir, 'dummydb.txt')).read())
    dummyelechier = eval(open(os.path.join(data_dir,
                                           'dummyelechiereg8.txt')).read())
    dummyelecbom = eval(open(os.path.join(data_dir,
                                          'dummyelecbomeg6.txt')).read())
    dummymoorhier = eval(open(os.path.join(data_dir,
                                           'dummymoorhiereg8.txt')).read())
    dummymoorbom = eval(open(os.path.join(data_dir,
                                          'dummymoorbomeg6.txt')).read())
    dummyuserhier = eval(open(os.path.join(data_dir,
                                           'dummyuserhiereg6.txt')).read())
    dummyuserbom = eval(open(os.path.join(data_dir,
                                          'dummyuserbomeg6.txt')).read())
    
    electrical_network = SubNetwork(dummyelechier, dummyelecbom)
    moorings_network = SubNetwork(dummymoorhier, dummymoorbom)
    user_network = SubNetwork(dummyuserhier, dummyuserbom)
    
    network = Network(dummydb,
                      electrical_network,
                      moorings_network,
                      user_network)
    
    
    print network.display()
    print len(network)
    #pprint.pprint(_get_indices(network._pool, "device"))
    #pprint.pprint(find_strings(network._pool))
    #pprint.pprint(hublist)
    #pprint.pprint(_get_curtailments(network._pool))
    
    
    import pprint
    
    new_network = network.set_failure_rates()
    
    #metrics = new_network.get_systems_metrics(720)
    metrics = new_network.get_subsystem_metrics("Elec sub-system", 8760)
    
    pprint.pprint(metrics)
    
    for key, value in metrics.iteritems():
        print key, len(value)
    
    #print new_network.display()
    #print pd.DataFrame(new_network.get_subsystem_metrics("M&F sub-system"))
    df = pd.DataFrame(metrics)
    df = df.set_index("Link")
    
    print df
    
    
    assert False


#def test_main():
#    '''Test that main generates a non empty output'''
#    
#    dummydb = eval(open(os.path.join(data_dir, 'dummydb.txt')).read())
#    dummyelechier = eval(open(os.path.join(data_dir,
#                                           'dummyelechiereg8.txt')).read())
#    dummyelecbom = eval(open(os.path.join(data_dir,
#                                          'dummyelecbomeg6.txt')).read())
#    dummymoorhier = eval(open(os.path.join(data_dir,
#                                           'dummymoorhiereg8.txt')).read())
#    dummymoorbom = eval(open(os.path.join(data_dir,
#                                          'dummymoorbomeg6.txt')).read())
#    dummyuserhier = eval(open(os.path.join(data_dir,
#                                           'dummyuserhiereg6.txt')).read())
#    dummyuserbom = eval(open(os.path.join(data_dir,
#                                          'dummyuserbomeg6.txt')).read())
#    
#    input_variables = Variables(20.0 * 365.25 * 24.0,
#                                'tidefloat',
#                                dummydb,
#                                0.4 * 20.0 * 365.25 * 24.0, 
#                                'multiplehubs',
#                                dummyelechier,
#                                dummyelecbom,
#                                dummymoorhier,
#                                dummymoorbom,
#                                dummyuserhier,
#                                dummyuserbom)
#                                
#    mttf, rsystime, reliatab = main(input_variables)
#    
#    assert mttf
#    assert rsystime is not None
#    assert not reliatab.empty


#def test_solo_electrical_radial():
#    '''Test that main generates a non empty output for just the electrical
#    network, with a radial layout.
#    '''
#
#    dummydb = eval(open(os.path.join(data_dir, 'dummydb1.txt')).read())
#    dummyelechier = eval(open(os.path.join(data_dir,
#                                           'dummyelechiereg9.txt')).read())
#    dummyelecbom = eval(open(os.path.join(data_dir,
#                                          'dummyelecbomeg9.txt')).read())
#    
#    input_variables = Variables(20.0 * 365.25 * 24.0, 
#                                'tidefloat',
#                                dummydb,
#                                0.4 * 20.0 * 365.25 * 24.0,
#                                'radial',
#                                dummyelechier,
#                                dummyelecbom)
#                                
#    mttf, rsystime, reliatab = main(input_variables)
#    
#    assert mttf
#    assert rsystime is not None
#    assert not reliatab.empty


#def test_solo_moorings():
#    '''Test that main generates a non empty output for just the moorings
#    network
#    '''
#
#    dummydb = eval(open(os.path.join(data_dir, 'dummydb.txt')).read())
#    dummymoorhier = eval(open(os.path.join(data_dir,
#                                           'dummymoorhiereg8.txt')).read())
#    dummymoorbom = eval(open(os.path.join(data_dir,
#                                          'dummymoorbomeg6.txt')).read())
#    dummyuserhier = eval(open(os.path.join(data_dir,
#                                           'dummyuserhiereg6.txt')).read())
#    dummyuserbom = eval(open(os.path.join(data_dir,
#                                          'dummyuserbomeg6.txt')).read())
#
#    input_variables = Variables(20.0 * 365.25 * 24.0, 
#                                'tidefixed',
#                                dummydb,
#                                0.4 * 20.0 * 365.25 * 24.0,
#                                'multiplehubs',
#                                moorfoundhierdict=dummymoorhier,
#                                moorfoundbomdict=dummymoorbom,
#                                userhierdict=dummyuserhier,
#                                userbomdict=dummyuserbom)
#                                
#    mttf, rsystime, reliatab = main(input_variables)
#    
#    assert mttf
#    assert rsystime is not None
#    assert not reliatab.empty


#def test_solo_user():
#    '''Test that main generates a non empty output for just the user
#    network
#    '''
#
#    dummydb = eval(open(os.path.join(data_dir, 'dummydb.txt')).read())
#    dummyuserhier = eval(open(os.path.join(data_dir,
#                                           'dummyuserhiereg6.txt')).read())
#    dummyuserbom = eval(open(os.path.join(data_dir,
#                                          'dummyuserbomeg6.txt')).read())
#    
#    input_variables = Variables(20.0 * 365.25 * 24.0, 
#                                'tidefloat',
#                                dummydb,
#                                0.4 * 20.0 * 365.25 * 24.0,
#                                'multiplehubs',
#                                userhierdict=dummyuserhier,
#                                userbomdict=dummyuserbom)
#                                
#    mttf, rsystime, reliatab = main(input_variables)
#    
#    assert mttf
#    assert rsystime is not None
#    assert not reliatab.empty
#
#
#def test_solo_user_no_array():
#    '''Test that main generates a non empty output for just the user
#    network without an array key in the hierarchy
#    '''
#
#    dummydb = eval(open(os.path.join(data_dir, 'dummydb.txt')).read())
#    dummyuserhier = eval(open(os.path.join(data_dir,
#                                           'dummyuserhiereg8.txt')).read())
#    dummyuserbom = eval(open(os.path.join(data_dir,
#                                          'dummyuserbomeg6.txt')).read())
#    
#    input_variables = Variables(20.0 * 365.25 * 24.0, 
#                                'tidefloat',
#                                dummydb,
#                                0.4 * 20.0 * 365.25 * 24.0,
#                                'multiplehubs',
#                                userhierdict=dummyuserhier,
#                                userbomdict=dummyuserbom)
#                                
#    mttf, rsystime, reliatab = main(input_variables)
#    
#    assert mttf
#    assert rsystime is not None
#    assert not reliatab.empty
#
#
#def test_electrical_user_no_array():
#    '''Test that main generates a non empty output'''
#    
#    dummydb = eval(open(os.path.join(data_dir, 'dummydb.txt')).read())
#    dummyelechier = eval(open(os.path.join(data_dir,
#                                           'dummyelechiereg8.txt')).read())
#    dummyelecbom = eval(open(os.path.join(data_dir,
#                                          'dummyelecbomeg6.txt')).read())
#    dummyuserhier = eval(open(os.path.join(data_dir,
#                                           'dummyuserhiereg8.txt')).read())
#    dummyuserbom = eval(open(os.path.join(data_dir,
#                                          'dummyuserbomeg6.txt')).read())
#    
#    input_variables = Variables(20.0 * 365.25 * 24.0,
#                                'tidefloat',
#                                dummydb,
#                                0.4 * 20.0 * 365.25 * 24.0, 
#                                'multiplehubs',
#                                dummyelechier,
#                                dummyelecbom,
#                                userhierdict=dummyuserhier,
#                                userbomdict=dummyuserbom)
#                                
#    mttf, rsystime, reliatab = main(input_variables)
#    
#    assert mttf
#    assert rsystime is not None
#    assert not reliatab.empty
#
#
#def test_moorings_user_no_array():
#    '''Test that main generates a non empty output'''
#    
#    dummydb = eval(open(os.path.join(data_dir, 'dummydb.txt')).read())
#    dummymoorhier = eval(open(os.path.join(data_dir,
#                                           'dummymoorhiereg8.txt')).read())
#    dummymoorbom = eval(open(os.path.join(data_dir,
#                                          'dummymoorbomeg6.txt')).read())
#    dummyuserhier = eval(open(os.path.join(data_dir,
#                                           'dummyuserhiereg8.txt')).read())
#    dummyuserbom = eval(open(os.path.join(data_dir,
#                                          'dummyuserbomeg6.txt')).read())
#    
#    input_variables = Variables(20.0 * 365.25 * 24.0,
#                                'tidefloat',
#                                dummydb,
#                                0.4 * 20.0 * 365.25 * 24.0, 
#                                'multiplehubs',
#                                moorfoundhierdict=dummymoorhier,
#                                moorfoundbomdict=dummymoorbom,
#                                userhierdict=dummyuserhier,
#                                userbomdict=dummyuserbom)
#                                
#    mttf, rsystime, reliatab = main(input_variables)
#    
#    assert mttf
#    assert rsystime is not None
#    assert not reliatab.empty
#
#
#def test_solo_electrical_distance():
#    '''Test that main generates a non empty output for just the electrical
#    network, with a radial layout.
#    '''
#
#    dummydb = eval(open(os.path.join(data_dir, 'dummydb1.txt')).read())
#    dummyelechier = eval(open(os.path.join(data_dir,
#                                           'dummyelechiereg9.txt')).read())
#    dummyelecbom = eval(open(os.path.join(data_dir,
#                                          'dummyelecbomeg9.txt')).read())
#    
#    elecsuppath = os.path.join(data_dir,
#                               'dummyelecsupplementary9.csv')
#    dummyelecsup = pd.read_csv(elecsuppath).to_dict()
#    
#    input_variables = Variables(20.0 * 365.25 * 24.0, 
#                                'tidefloat',
#                                dummydb,
#                                0.4 * 20.0 * 365.25 * 24.0,
#                                'radial',
#                                dummyelechier,
#                                dummyelecbom,
#                                elecsupplementary=dummyelecsup)
#                                
#    mttf, rsystime, reliatab = main(input_variables)
#    
#    assert mttf
#    assert rsystime is not None
#    assert not reliatab.empty
