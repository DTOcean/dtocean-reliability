# -*- coding: utf-8 -*-

#    Copyright (C) 2016-2018 Mathew Topper
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

from dtocean_reliability.main import Variables, Main

this_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(this_dir, "..", "example_data")


def test_main():    
    '''Test that main generates a non empty output'''
    
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
    
    input_variables = Variables(20.0 * 365.25 * 24.0,
                                'tidefloat',
                                dummydb,
                                0.4 * 20.0 * 365.25 * 24.0, 
                                'multiplehubs',
                                dummyelechier,
                                dummyelecbom,
                                dummymoorhier,
                                dummymoorbom,
                                dummyuserhier,
                                dummyuserbom)
                                
    test = Main(input_variables)
    mttf, rsystime = test()
    
    assert mttf
    assert rsystime is not None


def test_solo_electrical_radial():
    '''Test that main generates a non empty output for just the electrical
    network, with a radial layout.
    '''

    dummydb = eval(open(os.path.join(data_dir, 'dummydb1.txt')).read())
    dummyelechier = eval(open(os.path.join(data_dir,
                                           'dummyelechiereg9.txt')).read())
    dummyelecbom = eval(open(os.path.join(data_dir,
                                          'dummyelecbomeg9.txt')).read())
    
    input_variables = Variables(20.0 * 365.25 * 24.0, 
                                'tidefloat',
                                dummydb,
                                0.4 * 20.0 * 365.25 * 24.0,
                                'radial',
                                dummyelechier,
                                dummyelecbom)
                                
    test = Main(input_variables)
    mttf, rsystime = test()
    
    assert mttf
    assert rsystime is not None


def test_solo_moorings():
    '''Test that main generates a non empty output for just the moorings
    network
    '''

    dummydb = eval(open(os.path.join(data_dir, 'dummydb.txt')).read())
    dummymoorhier = eval(open(os.path.join(data_dir,
                                           'dummymoorhiereg8.txt')).read())
    dummymoorbom = eval(open(os.path.join(data_dir,
                                          'dummymoorbomeg6.txt')).read())
    
    input_variables = Variables(20.0 * 365.25 * 24.0, 
                                'tidefloat',
                                dummydb,
                                0.4 * 20.0 * 365.25 * 24.0,
                                'multiplehubs',
                                moorfoundhierdict=dummymoorhier,
                                moorfoundbomdict=dummymoorbom)
                                
    test = Main(input_variables)
    mttf, rsystime = test()
    
    assert mttf
    assert rsystime is not None


def test_solo_user():
    '''Test that main generates a non empty output for just the user
    network
    '''

    dummydb = eval(open(os.path.join(data_dir, 'dummydb.txt')).read())
    dummyuserhier = eval(open(os.path.join(data_dir,
                                           'dummyuserhiereg6.txt')).read())
    dummyuserbom = eval(open(os.path.join(data_dir,
                                          'dummyuserbomeg6.txt')).read())
    
    input_variables = Variables(20.0 * 365.25 * 24.0, 
                                'tidefloat',
                                dummydb,
                                0.4 * 20.0 * 365.25 * 24.0,
                                'multiplehubs',
                                userhierdict=dummyuserhier,
                                userbomdict=dummyuserbom)
                                
    test = Main(input_variables)
    mttf, rsystime = test()
    
    assert mttf
    assert rsystime is not None


def test_solo_user_no_array():
    '''Test that main generates a non empty output for just the user
    network without an array key in the hierarchy
    '''

    dummydb = eval(open(os.path.join(data_dir, 'dummydb.txt')).read())
    dummyuserhier = eval(open(os.path.join(data_dir,
                                           'dummyuserhiereg8.txt')).read())
    dummyuserbom = eval(open(os.path.join(data_dir,
                                          'dummyuserbomeg6.txt')).read())
    
    input_variables = Variables(20.0 * 365.25 * 24.0, 
                                'tidefloat',
                                dummydb,
                                0.4 * 20.0 * 365.25 * 24.0,
                                'multiplehubs',
                                userhierdict=dummyuserhier,
                                userbomdict=dummyuserbom)
                                
    test = Main(input_variables)
    mttf, rsystime = test()
    
    assert mttf
    assert rsystime is not None


def test_electrical_user_no_array():
    '''Test that main generates a non empty output'''
    
    dummydb = eval(open(os.path.join(data_dir, 'dummydb.txt')).read())
    dummyelechier = eval(open(os.path.join(data_dir,
                                           'dummyelechiereg8.txt')).read())
    dummyelecbom = eval(open(os.path.join(data_dir,
                                          'dummyelecbomeg6.txt')).read())
    dummyuserhier = eval(open(os.path.join(data_dir,
                                           'dummyuserhiereg8.txt')).read())
    dummyuserbom = eval(open(os.path.join(data_dir,
                                          'dummyuserbomeg6.txt')).read())
    
    input_variables = Variables(20.0 * 365.25 * 24.0,
                                'tidefloat',
                                dummydb,
                                0.4 * 20.0 * 365.25 * 24.0, 
                                'multiplehubs',
                                dummyelechier,
                                dummyelecbom,
                                userhierdict=dummyuserhier,
                                userbomdict=dummyuserbom)
                                
    test = Main(input_variables)
    mttf, rsystime = test()
    
    assert mttf
    assert rsystime is not None


def test_moorings_user_no_array():
    '''Test that main generates a non empty output'''
    
    dummydb = eval(open(os.path.join(data_dir, 'dummydb.txt')).read())
    dummymoorhier = eval(open(os.path.join(data_dir,
                                           'dummymoorhiereg8.txt')).read())
    dummymoorbom = eval(open(os.path.join(data_dir,
                                          'dummymoorbomeg6.txt')).read())
    dummyuserhier = eval(open(os.path.join(data_dir,
                                           'dummyuserhiereg8.txt')).read())
    dummyuserbom = eval(open(os.path.join(data_dir,
                                          'dummyuserbomeg6.txt')).read())
    
    input_variables = Variables(20.0 * 365.25 * 24.0,
                                'tidefloat',
                                dummydb,
                                0.4 * 20.0 * 365.25 * 24.0, 
                                'multiplehubs',
                                moorfoundhierdict=dummymoorhier,
                                moorfoundbomdict=dummymoorbom,
                                userhierdict=dummyuserhier,
                                userbomdict=dummyuserbom)
                                
    test = Main(input_variables)
    mttf, rsystime = test()
    
    assert mttf
    assert rsystime is not None
