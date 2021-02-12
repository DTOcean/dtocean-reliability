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

"""
DTOcean Reliability Assessment Module (RAM)

.. moduleauthor:: Sam Weller <s.weller@exeter.ac.uk>
.. moduleauthor:: Jon Hardwick <j.p.hardwick@exeter.ac.uk>
.. moduleauthor:: Mathew Topper <mathew.topper@dataonlygreater.com>
"""

# Built in modules
import os
import logging
from copy import deepcopy
from collections import Counter, OrderedDict

this_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(this_dir, "..", "example_data")

# Start logging
module_logger = logging.getLogger(__name__)


class Network(object):
    
    def __init__(self, hierarchy, bill_of_materials):
        
        self.hierarchy = hierarchy
        self.bill_of_materials = bill_of_materials
        
        return


class ArrayNetwork(object):
    
    def __init__(self, electrical_network = None,
                       moorings_network = None,
                       user_network = None):
        
        if (electrical_network is None and
            moorings_network is None and
            user_network is None):
            
            err_msg = "At least one network input must be provided"
            raise ValueError (err_msg)
        
        _check_nodes(electrical_network, None)
    
        (electrical_network,
         moorings_network,
         user_network) = _complete_networks(electrical_network,
                                            moorings_network,
                                            user_network)
        
        (self.array_hierarcy,
         self.device_hierachy) = _combine_networks('fixed',
                                                   electrical_network,
                                                   moorings_network,
                                                   user_network)


def _check_nodes(*networks):
    
    isNone = [True for x in networks if x is None]
    if len(networks) - len(isNone) < 2:
        return
    
    test_nodes = [set(network.hierarchy.keys()) for network in networks]
    
    unique_nodes = list(reduce(set.union, test_nodes) ^
                                        reduce(set.intersection, test_nodes))
    
    if unique_nodes:
        node_str = ", ".join(unique_nodes)
        err_msg = "Unique nodes detected in hierarchies: {}".format(node_str)
        raise ValueError(err_msg)
    
    return

def _complete_networks(electrical_network,
                       moorings_network,
                       user_network):

    # Determine which hierarchies/boms are available and create dummy
    # versions for any which are missing
    
    nodes = []
    
    # Scan available hierarchies for device numbers
    if electrical_network is not None:
        
        for node in electrical_network.hierarchy:
            if node not in nodes:
                nodes.append(node)
    
    else:
        
        for node in moorings_network.hierarchy:
            if node not in nodes:
                nodes.append(node)
    
    if 'array' not in nodes:
        nodes.append('array')
    
    devsonlylist = [x for x in nodes if x[:6] == 'device']
    subsonlylist = [[x] for x in nodes if x[:6] == 'subhub']
    
    # Complete networks
    if electrical_network is None:
        
        hierarchy = {}
        bill_of_materials = {}
        
        for node in nodes:
            
            if node == 'array': 
                
                if subsonlylist:
                    layout = subsonlylist
                else:
                    layout = [devsonlylist]
                
                hierarchy[node] = {'Export cable': ['dummy'],
                                   'Substation': ['dummy'],
                                   'layout': layout}
                bill_of_materials[node] = \
                    {'Substation': {'marker': [-1], 
                                    'quantity': Counter({'dummy': 1})},
                     'Export cable':
                                 {'marker': [-1], 
                                  'quantity': Counter({'dummy': 1})}}
                                 
            elif node[:6] == 'subhub':
                
                hierarchy[node] = {'Elec sub-system': ['dummy'],
                                   'Substation': ['dummy'],
                                   'layout': [devsonlylist]}
                
                bill_of_materials[node] = \
                     {'Elec sub-system': {
                                    'marker': [-1], 
                                    'quantity': Counter({'dummy': 1})},
                     'Substation': {'marker': [-1], 
                                    'quantity': Counter({'dummy': 1})}}
                
                devsonlylist = []
            
            elif node[:6] == 'device':
                
                hierarchy[node] = {'Elec sub-system': ['dummy']}
                bill_of_materials[node] = \
                                    {'marker': [-1], 
                                     'quantity': Counter({'dummy': 1})} 
        
        electrical_network = Network(hierarchy, bill_of_materials)
    
    if moorings_network is None:
        
        hierarchy = {}
        bill_of_materials = {}
        
        for node in nodes:
            
            if 'subhub' in node or node == 'array':
                
                hierarchy[node] = {'Substation foundation': ['dummy']}
                bill_of_materials[node] = \
                            {'Substation foundation': \
                                 {'substation foundation type': 'dummy'}}
                             
            elif node[:6] == 'device':
                
                hierarchy[node] = {'Umbilical': ['dummy'],
                                   'Mooring system': ['dummy'],
                                   'Foundation': ['dummy']}
                bill_of_materials[node] = \
                    {'Umbilical': {'quantity':
                                            Counter({'dummy': 1})},
                     'Foundation': {'quantity':
                                            Counter({'dummy': 1})},
                     'Mooring system': {'quantity':
                                            Counter({'dummy': 1})}}
        
        moorings_network = Network(hierarchy, bill_of_materials)
    
    dummy_hier = {'Dummy sub-system': ['dummy']}
    dummy_bom =  {'Dummy sub-system':
                            {'quantity': Counter({'dummy': 1})}}
    
    # Fill any missing nodes in the user network
    if user_network is None:
        
        hierarchy = {}
        bill_of_materials = {}
        
        for node in nodes:
            
            hierarchy[node] = deepcopy(dummy_hier)
            bill_of_materials[node] = deepcopy(dummy_bom)
        
        user_network = Network(hierarchy, bill_of_materials)
    
    else:
        
        for node in nodes:
            
            if node in user_network.hierarchy: continue
            
            user_network.hierarchy[node] = deepcopy(dummy_hier)
            user_network.bill_of_materials[node] = deepcopy(dummy_bom)
    
    return electrical_network, moorings_network, user_network


def _combine_networks(device_type,
                      electrical_network,
                      moorings_network,
                      user_network):
    
    # Read in sub-system networks and consolidate into device- and array-level 
    # networks
    _check_nodes(electrical_network,
                 moorings_network,
                 user_network)
    
    dev_electrical_hierarchy = deepcopy(electrical_network.hierarchy)
    dev_moorings_hierarchy = deepcopy(moorings_network.hierarchy)
    dev_user_hierarchy = deepcopy(user_network.hierarchy)
    
    device_hierachy = {}
    array_hierarcy = {}
    
    for node, systems in dev_moorings_hierarchy.iteritems():
        
        if (node[0:6] != 'device'): continue
    
        if 'float' in device_type:
            
            if systems['Foundation'] == ['dummy']:
                del systems['Foundation']
                continue
            
            anctype = systems['Foundation']
            
            # Append anchor into each mooring line and delete foundation 
            # field from dictionary
            for i, line in enumerate(systems['Mooring system']):
                systems['Mooring system'][i].append(anctype[i])
            
            del systems['Foundation']
        
        else:
            
            del systems['Mooring system']
            del systems['Umbilical']
    
    for node, systems in dev_electrical_hierarchy.iteritems():
        
        if (node == 'array' or node[0:6] == 'subhub'):
            
            array_hierarcy[node] = systems
            node_moorings = dev_moorings_hierarchy[node]
            substation_foundations = node_moorings['Substation foundation']

            for substf in substation_foundations:
                array_hierarcy[node]['Substation'].append(substf)
        
        elif node[0:6] == 'device':
            
            device_hierachy[node] = {
                    'M&F sub-system': dev_moorings_hierarchy[node], 
                    'Array elec sub-system': dev_electrical_hierarchy[node],
                    'User sub-systems': dev_user_hierarchy[node]}
    
    return array_hierarcy, device_hierachy


if __name__ == "__main__":
    
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
    
    electrical_network = Network(dummyelechier, dummyelecbom)
    moorings_network = Network(dummymoorhier, dummymoorbom)
    user_network = Network(dummyuserhier, dummyuserbom)

    import pprint
    #pprint.pprint(user_network.hierarchy)
    
    _check_nodes(electrical_network, None)
    
    (electrical_network,
     moorings_network,
     user_network) = _complete_networks(electrical_network,
                                        moorings_network,
                                        user_network)
    
    array_hierarcy, device_hierachy = _combine_networks('fixed',
                                                        electrical_network,
                                                        moorings_network,
                                                        user_network)
    
    pprint.pprint(array_hierarcy)
    pprint.pprint(device_hierachy)
    
    from links import build_pool, find_all_labels
    
    pool = build_pool(array_hierarcy, device_hierachy)
    
    print pool['array'].display(pool)
    print find_all_labels("id4", pool)
    print pool[2].display(pool)