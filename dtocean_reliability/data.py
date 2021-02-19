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

from links import Serial, Parallel, Component

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
                systems['Mooring system'][i].extend(anctype[i])
            
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


def _build_pool(array_hierarcy, device_hierachy):
    
    pool = {}
    array_link = Serial("array")
    
    array_dict = array_hierarcy["array"]
    _build_pool_array(array_dict, array_link, pool)
    _build_pool_layouts(array_dict["layout"],
                        array_link,
                        pool,
                        array_hierarcy,
                        device_hierachy)
    
    pool["array"] = array_link
    
    return pool


def _build_pool_array(array_dict, array_link, pool):
    
    array_systems = ('Export cable', 'Substation')
    
    for system in array_systems:
        
        comps = _strip_dummy(array_dict[system])
        if comps is None: continue
        
        system_link = Serial(system)
        _build_pool_comps(comps, system_link, pool)
        
        next_pool_key = len(pool)
        pool[next_pool_key] = system_link
        array_link.add_item(next_pool_key)
    
    return


def _build_pool_layouts(nodes,
                        parent_link,
                        pool,
                        array_hierarcy,
                        device_hierachy):
    
    n_list = len([True for x in nodes if isinstance(x, list)])
    
    if n_list > 1:
        
        new_parallel = Parallel()
        
        for item in nodes:
            
            new_serial = Serial()
            _build_pool_layouts(item,
                                new_serial,
                                pool,
                                array_hierarcy,
                                device_hierachy)
            
            next_pool_key = len(pool)
            pool[next_pool_key] = new_serial
            new_parallel.add_item(next_pool_key)
            
        next_pool_key = len(pool)
        pool[next_pool_key] = new_parallel
        parent_link.add_item(next_pool_key)
        
        return
    
    elif n_list == 1:
        nodes = nodes[0]
    
    for item in nodes:
        
        if isinstance(item, list):
            
            new_serial = Serial()
            _build_pool_layouts(item, new_serial, pool)
            
            next_pool_key = len(pool)
            pool[next_pool_key] = new_serial
            parent_link.add_item(next_pool_key)
        
        if "subhub" in item:
            
            new_subhub = Serial(item)
            _build_pool_subhub(array_hierarcy[item],
                               new_subhub,
                               pool,
                               array_hierarcy,
                               device_hierachy)
            
            next_pool_key = len(pool)
            pool[next_pool_key] = new_subhub
            parent_link.add_item(next_pool_key)
            
        else:
            
            new_device = Serial(item)
            _build_pool_device(device_hierachy[item], new_device, pool)
            
            next_pool_key = len(pool)
            pool[next_pool_key] = new_device
            parent_link.add_item(next_pool_key)
    
    return


def _build_pool_subhub(subhub_dict,
                       subhub_link,
                       pool,
                       array_hierarcy,
                       device_hierachy):
    
    subhub_systems = ('Elec sub-system', 'Substation')
    
    for system in subhub_systems:
        
        comps = _strip_dummy(subhub_dict[system])
        if comps is None: continue
        
        system_link = Serial(system)
        _build_pool_comps(comps, system_link, pool)
        
        next_pool_key = len(pool)
        pool[next_pool_key] = system_link
        subhub_link.add_item(next_pool_key)
    
    _build_pool_layouts(subhub_dict["layout"],
                        subhub_link,
                        pool,
                        array_hierarcy,
                        device_hierachy)
    
    return


def _build_pool_device(device_dict, parent_link, pool):
    
    for label, system in device_dict.iteritems():
        
        system_link = Serial(label)
        temp_pool = deepcopy(pool)
        
        if isinstance(system, dict):
            _build_pool_device(system, system_link, temp_pool)
        else:
            comps = _strip_dummy(system)
            if comps is None: continue
            _build_pool_comps(comps, system_link, temp_pool)
        
        if len(temp_pool) - len(pool) == 0:
            continue
        
        pool.update(temp_pool)
        next_pool_key = len(pool)
        pool[next_pool_key] = system_link
        parent_link.add_item(next_pool_key)
    
    return


def _build_pool_comps(comps, parent_link, pool):
    
    n_list = len([True for x in comps if isinstance(x, list)])
    
    if n_list > 1:
        
        next_pool_key = len(pool)
        new_parallel = Parallel()
        pool[next_pool_key] = new_parallel
        parent_link.add_item(next_pool_key)
        
        for item in comps:
            next_pool_key = len(pool)
            new_serial = Serial()
            pool[next_pool_key] = new_serial
            _build_pool_comps(item, new_serial, pool)
            new_parallel.add_item(next_pool_key)
        
        return
    
    elif n_list == 1:
        comps = comps[0]
    
    for item in comps:
        
        if isinstance(item, list):
            
            new_serial = Serial()
            _build_pool_comps(item, new_serial, pool)
            
            next_pool_key = len(pool)
            pool[next_pool_key] = new_serial
            parent_link.add_item(next_pool_key)
            
        else:
        
            next_pool_key = len(pool)
            new_component = Component(item)
            pool[next_pool_key] = new_component
            parent_link.add_item(next_pool_key)
    
    return


def _strip_dummy(comps):
    
    reduced = []
    
    for check in comps:
    
        if isinstance(check, basestring):
            if check == "dummy":
                reduced.append(None)
            else:
                reduced.append(check)
        else:
            reduced.append(_strip_dummy(check))
        
    complist = [x for x in reduced if x is not None]
    if not complist: complist = None
    
    return complist


def _set_component_failure_rates (pool,
                                  dbdict,
                                  severitylevel,
                                  calcscenario):
    
    # For components with an id number look up respective failure rates 
    # otherwise for designed components (i.e. shallow/gravity foundations, 
    # direct embedment anchors and suction caissons) in addition to 
    # grouted jointed use generic failure rate of 1.0x10^-4 failures 
    # per annum (10 / 876 failures per 10^6 hours)
    
    # Note:
    #  * If no data for a particular calculation scenario, failure rate 
    #    defaults to mean value
    #  * If no non-critical failure rate data is available use critical values
    
    designed_comps = ["dummy",
                      "n/a",
                      "ideal",
                      "gravity",
                      "shallowfoundation",
                      "suctioncaisson",
                      "directembedment",
                      "grout"]
    
    if calcscenario == 'lower':
        cs = 0
    elif calcscenario == 'mean':
        cs = 1
    elif calcscenario == 'upper':
        cs = 2
    else:
        err_str = "Argument 'calcscenario' may only take values 0, 1, or 2"
        raise ValueError(err_str)
    
    for item in pool.values():
        
        if not isinstance(item, Component):
            continue
        
        if item.label in designed_comps:
            item.failure_rate = 10. / 876
            continue
        
        dbitem = deepcopy(dbdict[item.label]['item10'])
        
        if severitylevel == 'critical':
            
            if dbitem['failratecrit'][cs] == 0.0:
                failure_rate = dbitem['failratecrit'][1]
            else:
                failure_rate = dbitem['failratecrit'][cs]
        
        else:
            
            if dbitem['failratenoncrit'][1] == 0.0:
               dbitem['failratenoncrit'] = dbitem['failratecrit']
            
            if dbitem['failratenoncrit'][cs] == 0.0:
                 failure_rate = dbitem['failratenoncrit'][1]
            else:
                 failure_rate = dbitem['failratenoncrit'][cs]
        
        item.failure_rate = failure_rate
    
    return


if __name__ == "__main__":
    
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
    
    array_hierarcy, device_hierachy = _combine_networks('float',
                                                        electrical_network,
                                                        moorings_network,
                                                        user_network)
    
    pprint.pprint(array_hierarcy)
    pprint.pprint(device_hierachy)
    
    pool = _build_pool(array_hierarcy, device_hierachy)
    _set_component_failure_rates(pool,
                                 dummydb,
                                 'critical',
                                 'mean')
    
    from links import find_all_labels
    
    print pool['array'].display(pool)
    #pprint.pprint(find_all_labels("id4", pool))
