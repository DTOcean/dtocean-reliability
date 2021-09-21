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
    
    print network.display()
    
    critical_network = network.set_failure_rates()
    systems_metrics = critical_network.get_systems_metrics(720)
    moor_metrics = critical_network.get_subsystem_metrics("M&F sub-system",
                                                          8760)
    
    if HAS_PANDAS:
        
        systems_df = pd.DataFrame(systems_metrics)
        moor_df = pd.DataFrame(moor_metrics)
        
        systems_df = systems_df.set_index("Link")
        moor_df = moor_df.set_index("Link")
        
        print systems_df
        print ""
        print moor_df
    
    else:
        
        pprint.pprint(systems_metrics)
        print ""
        pprint.pprint(moor_metrics)
    
    return


if __name__ == "__main__":
    
    start_logging(level="DEBUG")
    main()
