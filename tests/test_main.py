

import os
import pprint
import time
from collections import Counter

from dtocean_reliability.main import Variables, Main

this_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(this_dir, "..", "sample_data")

def test_main():    
    '''Test that main generates a non empty output'''
    
    input_variables = Variables(20.0 * 365.25 * 24.0, # mission time in hours
                                0.4 * 20.0 * 365.25 * 24.0, # target mean time to failure in hours
                                'tidefloat', # user-defined bill of materials
                                eval(open(os.path.join(data_dir, 'dummydb.txt')).read()), #Options: 'tidefloat', 'tidefixed', 'wavefloat', 'wavefixed'
                                'multiplehubs', #Options: 'radial', 'singlesidedstring', 'doublesidedstring', 'multiplehubs' 
                                eval(open(os.path.join(data_dir, 'dummyelechiereg8.txt')).read()), # electrical system hierarchy
                                eval(open(os.path.join(data_dir, 'dummyelecbomeg6.txt')).read()), # electrical system bill of materials
                                eval(open(os.path.join(data_dir, 'dummymoorhiereg8.txt')).read()), # mooring and foundation system hierarchy
                                eval(open(os.path.join(data_dir, 'dummymoorbomeg6.txt')).read()), # mooring and foundation system bill of materials
                                eval(open(os.path.join(data_dir, 'dummyuserhiereg6.txt')).read()), # dummy user-defined hierarchy
                                eval(open(os.path.join(data_dir, 'dummyuserbomeg6.txt')).read())) # database
                                
    test = Main(input_variables)
    mttf, rsystime = test()    
    
    assert mttf
    assert rsystime is not None
    
def test_solo_electrical():    
    '''Test that main generates a non empty output for just the electrical
    network
    '''
    
    input_variables = Variables(20.0 * 365.25 * 24.0, # mission time in hours
                                0.4 * 20.0 * 365.25 * 24.0, # target mean time to failure in hours
                                'tidefloat', # user-defined bill of materials
                                eval(open(os.path.join(data_dir, 'dummydb1.txt')).read()), #Options: 'tidefloat', 'tidefixed', 'wavefloat', 'wavefixed'
                                'radial', #Options: 'radial', 'singlesidedstring', 'doublesidedstring', 'multiplehubs' 
                                eval(open(os.path.join(data_dir, 'dummyelechiereg9.txt')).read()), # electrical system hierarchy
                                eval(open(os.path.join(data_dir, 'dummyelecbomeg9.txt')).read())) # database
                                
    test = Main(input_variables)
    mttf, rsystime = test()    
    
    assert mttf
    assert rsystime is not None
