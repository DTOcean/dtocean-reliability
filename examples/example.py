
import os
from collections import Counter

from dtocean_reliability import start_logging, Network, SubNetwork

try:
    import pandas as pd
    pd.set_option('display.max_columns', None)
    HAS_PANDAS = True
except ImportError:
    import pprint
    HAS_PANDAS = False

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = os.path.join(THIS_DIR, "..", "example_data")


def main():
    
    dummydb = eval(open(os.path.join(DATA_DIR, 'dummydb.txt')).read())
    dummyelechier = eval(open(os.path.join(DATA_DIR,
                                           'dummyelechiereg8.txt')).read())
    dummyelecbom = eval(open(os.path.join(DATA_DIR,
                                          'dummyelecbomeg6.txt')).read())
    dummymoorhier = eval(open(os.path.join(DATA_DIR,
                                           'dummymoorhiereg8.txt')).read())
    dummymoorbom = eval(open(os.path.join(DATA_DIR,
                                          'dummymoorbomeg6.txt')).read())
    dummyuserhier = eval(open(os.path.join(DATA_DIR,
                                           'dummyuserhiereg6.txt')).read())
    dummyuserbom = eval(open(os.path.join(DATA_DIR,
                                          'dummyuserbomeg6.txt')).read())
    
    electrical_network = SubNetwork(dummyelechier, dummyelecbom)
    moorings_network = SubNetwork(dummymoorhier, dummymoorbom)
    user_network = SubNetwork(dummyuserhier, dummyuserbom)
    
    network = Network(dummydb,
                      electrical_network,
                      moorings_network,
                      user_network)
    
    print network.display()
    
    critical_network = network.set_failure_rates()
    systems_metrics = critical_network.get_systems_metrics(720)
    elec_metrics = critical_network.get_subsystem_metrics("Elec sub-system",
                                                          8760)
    
    if HAS_PANDAS:
        
        systems_df = pd.DataFrame(systems_metrics)
        elec_df = pd.DataFrame(elec_metrics)
        
        systems_df = systems_df.set_index("Link")
        elec_df = elec_df.set_index("Link")
        
        print systems_df
        print ""
        print elec_df
    
    else:
        
        pprint.pprint(systems_metrics)
        print ""
        pprint.pprint(elec_metrics)
    
    print ""
    
    system = critical_network[14]
    
    print system
    print system.display()
    
    print ""
    
    weeks = range(1, 13)
    hours = map(lambda x: x * 24 * 7, weeks)
    R = map(lambda x: system.get_reliability(x), hours)
    
    print "{:>8}{:>8}".format("Week", "R")
    
    for week, Rweek in zip(weeks, R):
        print "{:>8}{:>8.4f}".format(week, Rweek)
    
    return


if __name__ == "__main__":
    
    start_logging(level="DEBUG")
    main()
