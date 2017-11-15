

import os
import pickle
import pprint
from collections import Counter

import numpy as np
import matplotlib.pylab as plt

from dtocean_reliability import start_logging
from dtocean_reliability.main import Variables, Main

mod_path = os.path.realpath(__file__)
mod_dir = os.path.dirname(mod_path)

def main():    
    '''Test that main generates a non empty output'''
    
    # Pick up the pickled inputs
    input_dict_file = os.path.join(mod_dir, "reliability_inputs.pkl")
    
    with open(input_dict_file, "rb") as fstream:
        input_dict = pickle.load(fstream)
        
    pprint.pprint(input_dict["moor_found_network_hier"])
    pprint.pprint(input_dict["moor_found_network_bom"])
    
    input_variables = Variables(input_dict["mission_time_hours"], # mission time in hours
                                input_dict["system_type"], #Options: 'tidefloat', 'tidefixed', 'wavefloat', 'wavefixed'
                                input_dict["compdict"], # database
                                input_dict["mttfreq_hours"], # target mean time to failure in hours
                                input_dict["network_configuration"], 
                                input_dict["electrical_network_hier"], # electrical system hierarchy
                                input_dict["electrical_network_bom"], 
                                input_dict["moor_found_network_hier"], # mooring system hierarchy
                                input_dict["moor_found_network_bom"])
                                        
    test = Main(input_variables)
    mttf, rsystime = test()
    
    return mttf, rsystime
    
def plot(rsystime):
    
    data = np.array(rsystime)
    plt.plot(data[:,0], data[:,1])
    plt.ylabel('System reliability', fontsize=10)
    plt.xlabel('Time [hours]', fontsize=10)     
    plt.show()
    
if __name__ == "__main__":

    start_logging(level="DEBUG")
    
    mttf, rsystime = main()
    
    pprint.pprint('Mean time to failure (hours): {}'.format(mttf))
    pprint.pprint('Mean time to failure (years): {}'.format(mttf/(24.0*365.25)))
    # plot(rsystime)

