
import os
import re
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
    
    # Pick up installation data
    import ast
    import csv
    from collections import namedtuple
    from itertools import imap
    
    dummyelecdata_path = os.path.join(DATA_DIR, 'dummyelecdata.csv')
    
    dummyelecdata = {}
    
    with open(dummyelecdata_path, mode="rb") as infile:
        
        reader = csv.reader(infile)
        slugs = [urlify(x) for x in next(reader)]
        Data = namedtuple("Data", slugs)
        
        for raw in reader:
            convert = [str, str, float, eval, eval, int]
            raw = [f(x) for f, x in zip(convert, raw)]
            data = Data._make(raw)
            dummyelecdata[int(data.Marker)] = data
    
    electrical_network = SubNetwork(dummyelechier, dummyelecbom)
    moorings_network = SubNetwork(dummymoorhier, dummymoorbom)
    user_network = SubNetwork(dummyuserhier, dummyuserbom)
    
    network = Network(dummydb,
                      electrical_network,
                      moorings_network,
                      user_network,
                      dummyelecdata)
    
    print network.display()
    print ""
    
    critical_network = network.set_failure_rates(use_kfactors=False)
    system = critical_network[14]
    
    print system
    print system.display()
    print ""
    
    critical_network = network.set_failure_rates(use_kfactors=True)
    system = critical_network[14]
    
    print system
    print system.display()
    print ""
    
    print critical_network[10].display()
    
    
    return


def urlify(s):

    # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"[^\w\s]", '', s)

    # Replace all runs of whitespace with a single dash
    s = re.sub(r"\s+", '_', s)

    return s


if __name__ == "__main__":
    
    start_logging(level="DEBUG")
    main()
