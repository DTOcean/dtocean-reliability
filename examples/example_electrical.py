
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
                                'wavefloat', #Options: 'tidefloat', 'tidefixed', 'wavefloat', 'wavefixed'
                                eval(open(os.path.join(data_dir, 'dummydb1.txt')).read()), # database
                                0.4 * 20.0 * 365.25 * 24.0, # target mean time to failure in hours
                                'radial', #Options: 'radial', 'multiplehubs' 
                                eval(open(os.path.join(data_dir, 'dummyelechiereg9.txt')).read()), # electrical system hierarchy
                                eval(open(os.path.join(data_dir, 'dummyelecbomeg9.txt')).read())) # electrical bom
    
    test = Main(input_variables)
    mttf, rsystime = test()
    
    return mttf, rsystime


if __name__ == "__main__":

    start_logging(level="DEBUG")
    
    mttf, rsystime = main()
    
    pprint.pprint('Mean time to failure (hours): {}'.format(mttf))
    pprint.pprint('Mean time to failure (years): {}'.format(mttf/(24.0*365.25)))
