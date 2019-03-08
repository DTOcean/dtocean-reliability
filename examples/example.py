
import os
import pprint
from collections import Counter

from dtocean_reliability import start_logging
from dtocean_reliability.main import Variables, Main

this_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(this_dir, "..", "example_data")


def main():
    '''Test that main generates a non empty output'''
    
    input_variables = Variables(20.0 * 365.25 * 24.0, # mission time in hours
                                'tidefloat', #Options: 'tidefloat', 'tidefixed', 'wavefloat', 'wavefixed'
                                eval(open(os.path.join(data_dir, 'dummydb.txt')).read()), # database
                                0.4 * 20.0 * 365.25 * 24.0, # target mean time to failure in hours
                                'multiplehubs', #Options: 'radial', 'multiplehubs' 
                                eval(open(os.path.join(data_dir, 'dummyelechiereg8.txt')).read()), # electrical system hierarchy
                                eval(open(os.path.join(data_dir, 'dummyelecbomeg6.txt')).read()), # electrical system bill of materials
                                eval(open(os.path.join(data_dir, 'dummymoorhiereg8.txt')).read()), # mooring and foundation system hierarchy
                                eval(open(os.path.join(data_dir, 'dummymoorbomeg6.txt')).read()), # mooring and foundation system bill of materials
                                eval(open(os.path.join(data_dir, 'dummyuserhiereg6.txt')).read()), # dummy user-defined hierarchy
                                eval(open(os.path.join(data_dir, 'dummyuserbomeg6.txt')).read())) # user-defined bill of materials
    
    test = Main(input_variables)
    mttf, rsystime = test()
    
    return mttf, rsystime


if __name__ == "__main__":

    start_logging(level="DEBUG")
    
    mttf, rsystime = main()
    
    pprint.pprint('Mean time to failure (hours): {}'.format(mttf))
    pprint.pprint('Mean time to failure (years): {}'.format(mttf/(24.0*365.25)))
