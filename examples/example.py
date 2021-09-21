# -*- coding: utf-8 -*-

#    Copyright (C) 2016 Sam Weller, Jon Hardwick
#    Copyright (C) 2017-2021 Mathew Topper
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
from collections import Counter # pylint: disable=unused-import

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
    sk_metrics = critical_network.get_subsystem_metrics("Station keeping",
                                                        8760)
    
    if HAS_PANDAS:
        
        systems_df = pd.DataFrame(systems_metrics)
        sk_df = pd.DataFrame(sk_metrics)
        
        systems_df = systems_df.set_index("Link")
        sk_df = sk_df.set_index("Link")
        
        print systems_df
        print ""
        print sk_df
    
    else:
        
        pprint.pprint(systems_metrics)
        print ""
        pprint.pprint(sk_metrics)
    
    print ""
    
    system = critical_network[49]
    
    print system
    print system.display()
    
    print ""
    
    weeks = range(1, 13)
    hours = [x * 24 * 7 for x in weeks]
    R = [system.get_reliability(x) for x in hours]
    
    print "{:>8}{:>8}".format("Week", "R")
    
    for week, Rweek in zip(weeks, R):
        print "{:>8}{:>8.4f}".format(week, Rweek)
    
    print ""
    
    PFoundation = system.get_probability_proportion("Foundation")
    PMoorings = system.get_probability_proportion("Moorings lines")
    
    print "P (Foundation): ", PFoundation
    print "P (Moorings lines): ", PMoorings
    print "P (Total): ", PFoundation + PMoorings
    
    return


if __name__ == "__main__":
    
    start_logging(level="DEBUG")
    main()
