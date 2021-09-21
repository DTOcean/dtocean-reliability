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
import re
import logging
from copy import deepcopy
from collections import Counter, OrderedDict

from .graph import Component, Parallel, Serial

# Start logging
module_logger = logging.getLogger(__name__)


class SubNetwork(object):
    
    def __init__(self, hierarchy, bill_of_materials):
        
        self.hierarchy = hierarchy
        self.bill_of_materials = bill_of_materials
        
        return


class MarkedSystem(object):
    
    def __init__(self, ids, markers):
        self.ids = ids
        self.markers = markers
    
    def __nonzero__(self):
        if self.ids: return True
        return False
    
    def __str__(self):
        return str(zip(self.ids, self.markers))
    
    def __repr__(self):
        return self.__str__()


def check_nodes(*networks):
    
    isNone = [True for x in networks if x is None]
    if len(networks) - len(isNone) < 2:
        return
    
    test_nodes = [set(network.hierarchy.keys()) for network in networks]
    unique_nodes = list(reduce(set.union, test_nodes) ^ # pylint: disable=undefined-variable
                                        reduce(set.intersection, test_nodes)) # pylint: disable=undefined-variable
    
    if unique_nodes:
        node_str = ", ".join(unique_nodes)
        err_msg = "Unique nodes detected in hierarchies: {}".format(node_str)
        raise ValueError(err_msg)
    
    return


def mark_networks(*networks):
    
    def get_dummy_markers(comps):
        
        if not comps: return comps
        
        if hasattr(comps[0], '__iter__'):
            return [[-1] * len(x) for x in comps]
        
        return [-1] * len(comps)
    
    for network in networks:
    
        marked_hierarchy = deepcopy(network.hierarchy)
        
        for node, systems in network.hierarchy.iteritems():
            
            for system in systems:
                
                if system == 'layout': continue
                
                if system == 'Elec sub-system' and 'device' in node:
                    data = network.bill_of_materials[node]
                else:
                    data = network.bill_of_materials[node][system]
                
                comps = network.hierarchy[node][system]
                
                if 'marker' not in data:
                    markers = get_dummy_markers(comps)
                else:
                    markers = data['marker']
                    
                marked_hierarchy[node][system] = MarkedSystem(comps, markers)
        
        network.hierarchy = marked_hierarchy


def complete_networks(electrical_network,
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
    
    elif moorings_network is not None:
        
        for node in moorings_network.hierarchy:
            if node not in nodes:
                nodes.append(node)
        
        # Fix empty array key
        if "array" not in nodes:
            
            moorings_network.hierarchy["array"] = {
                                        'Substation foundation': ['dummy']}
            moorings_network.bill_of_materials["array"] = \
                        {'Substation foundation': \
                                 {'substation foundation type': 'dummy'}}
            
            nodes.append("array")
    
    else:
        
        for node in user_network.hierarchy:
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
        
        electrical_network = SubNetwork(hierarchy, bill_of_materials)
    
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
        
        moorings_network = SubNetwork(hierarchy, bill_of_materials)
    
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
        
        user_network = SubNetwork(hierarchy, bill_of_materials)
    
    else:
        
        for node in nodes:
            
            if node in user_network.hierarchy: continue
            
            user_network.hierarchy[node] = deepcopy(dummy_hier)
            user_network.bill_of_materials[node] = deepcopy(dummy_bom)
    
    return electrical_network, moorings_network, user_network


def combine_networks(electrical_network,
                     moorings_network,
                     user_network):
    
    # Read in sub-system networks and consolidate into device- and array-level 
    # networks
    check_nodes(electrical_network,
                moorings_network,
                user_network)
    
    # Store markers alongside component ids
    mark_networks(electrical_network,
                  moorings_network,
                  user_network)
    
    dev_electrical_hierarchy = deepcopy(electrical_network.hierarchy)
    dev_moorings_hierarchy = deepcopy(moorings_network.hierarchy)
    dev_user_hierarchy = deepcopy(user_network.hierarchy)
    
    device_hierachy = {}
    array_hierarcy = {}
    
    for node, systems in dev_moorings_hierarchy.iteritems():
        
        if node[0:6] != 'device': continue
        
        if 'Mooring system' in systems and systems['Mooring system']:
            
            if systems['Mooring system'].ids == ["dummy"]:
                
                systems['Station keeping'] = MarkedSystem(["dummy"], [-1])
                
            else:
                
                systems['Station keeping'] = []
            
                lids = systems['Mooring system'].ids
                lmarkers = systems['Mooring system'].markers
                
                for i, (lid, lmarker) in enumerate(zip(lids, lmarkers)):
                    
                    sk_data = OrderedDict()
                    sk_data["Moorings lines"] = MarkedSystem([lid], [lmarker])
                    
                    fid = systems['Foundation'].ids[i]
                    fmarker = systems['Foundation'].markers[i]
                    
                    sk_data["Foundation"] = MarkedSystem([fid], [fmarker])
                    systems['Station keeping'].append(sk_data)
            
            del systems['Mooring system']
            del systems['Foundation']
        
        else:
            
            systems['Station keeping'] = {"Foundation":
                                                    systems['Foundation']}
            
            del systems['Foundation']
            if 'Mooring system' in systems:
                del systems['Mooring system']
        
        if 'Umbilical' in systems and not systems['Umbilical']:
            del systems['Umbilical']
        
    for node, systems in dev_electrical_hierarchy.iteritems():
        
        if (node == 'array' or node[0:6] == 'subhub'):
            
            array_hierarcy[node] = systems
            node_moorings = dev_moorings_hierarchy[node]
            substation_foundations = node_moorings['Substation foundation']
            
            sids = substation_foundations.ids
            smarkers = substation_foundations.markers
            array_hierarcy[node]['Substation'].ids += sids
            array_hierarcy[node]['Substation'].markers += smarkers
        
        elif node[0:6] == 'device':
            
            device_hierachy[node] = {
                    'M&F sub-system': dev_moorings_hierarchy[node], 
                    'Array elec sub-system': dev_electrical_hierarchy[node],
                    'User sub-systems': dev_user_hierarchy[node]}
    
    return array_hierarcy, device_hierachy


def build_pool(array_hierarcy, device_hierachy):
    
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
        
        array_system = array_dict[system]
        comps = _strip_dummy(array_system)
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
        
        subhub_system = subhub_dict[system]
        comps = _strip_dummy(subhub_system)
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
            
        elif (not isinstance(system, MarkedSystem) and
              isinstance(system[0], dict)):
            
            new_parallel = Parallel()
            
            for item in system:
                
                item_link = Serial()
                _build_pool_device(item, item_link, temp_pool)
                
                next_pool_key = len(temp_pool)
                temp_pool[next_pool_key] = item_link
                new_parallel.add_item(next_pool_key)
            
            next_pool_key = len(temp_pool)
            temp_pool[next_pool_key] = new_parallel
            system_link.add_item(next_pool_key)
            
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


def _build_pool_comps(marked_system, parent_link, pool):
    
    comps = marked_system.ids
    markers = marked_system.markers
    
    n_list = len([True for x in comps if isinstance(x, list)])
    
    if n_list > 1:
        
        next_pool_key = len(pool)
        new_parallel = Parallel()
        pool[next_pool_key] = new_parallel
        parent_link.add_item(next_pool_key)
        
        for idx, item in enumerate(comps):
            
            next_pool_key = len(pool)
            new_serial = Serial()
            pool[next_pool_key] = new_serial
            
            marker = markers[idx]
            item = MarkedSystem([item], [marker])
            
            _build_pool_comps(item, new_serial, pool)
            new_parallel.add_item(next_pool_key)
        
        return
    
    elif n_list == 1:
        comps = comps[0]
        markers = markers[0]
    
    for idx, item in enumerate(comps):
        
        marker = markers[idx]
        next_pool_key = len(pool)
        new_component = Component(item, marker)
        pool[next_pool_key] = new_component
        parent_link.add_item(next_pool_key)
    
    return


def _strip_dummy(marked_system):
    
    compsids = marked_system.ids
    markers = marked_system.markers
    
    reduced_ids = []
    reduced_markers = []
    
    for compid, marker in zip(compsids, markers):
    
        if isinstance(compid, basestring): # pylint: disable=undefined-variable
            if compid == "dummy":
                reduced_ids.append(None)
                reduced_markers.append(None)
            else:
                reduced_ids.append(compid)
                reduced_markers.append(marker)
        elif isinstance(compid, list):
            new_comps = _strip_dummy(MarkedSystem(compid, marker))
            reduced_ids.append(new_comps.ids)
            reduced_markers.append(new_comps.markers)
        else:
            reduced_ids.append(compid)
            reduced_markers.append(marker)
        
    idlist = [x for x in reduced_ids if x is not None]
    markerlist = [x for x in reduced_markers if x is not None]
    
    if not idlist: return None
    
    return MarkedSystem(idlist, markerlist)

