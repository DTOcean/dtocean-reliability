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


class KSystem(object):
    
    def __init__(self, ids, kfactors):
        self.ids = ids
        self.kfactors = kfactors
    
    def __str__(self):
        return str(zip(self.ids, self.kfactors))
    
    def __repr__(self):
        return self.__str__()


def slugify(s):
    
    # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"[^\w\s]", '', s)
    
    # Replace all runs of whitespace with a single dash
    s = re.sub(r"\s+", '_', s)
    
    return str(s)


def check_nodes(*networks):
    
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
                     user_network,
                     electrical_data=None):
    
    # Read in sub-system networks and consolidate into device- and array-level 
    # networks
    check_nodes(electrical_network,
                moorings_network,
                user_network)
    
    # Create dictionary from electrical data
    if electrical_data is not None:
    
        electrical_data_dict = {}
        
        for record in electrical_data:
            electrical_data_dict[record.Marker] = record
        
        electrical_data = electrical_data_dict
    
    dev_electrical_hierarchy = deepcopy(electrical_network.hierarchy)
    dev_moorings_hierarchy = deepcopy(moorings_network.hierarchy)
    dev_user_hierarchy = deepcopy(user_network.hierarchy)
    
    dev_electrical_bom = deepcopy(electrical_network.bill_of_materials)
    
    device_hierachy = {}
    array_hierarcy = {}
    
    for node, systems in dev_moorings_hierarchy.iteritems():
        
        if (node[0:6] != 'device'): continue
        
        if 'Mooring system' in systems and systems['Mooring system']:
            
            if systems['Mooring system'] == ["dummy"]:
                
                systems['Station keeping'] = ["dummy"]
                
            else:
                
                systems['Station keeping'] = []
            
                lines = deepcopy(systems['Mooring system']) 
                
                for i, line in enumerate(lines):
                    
                    sk_data = OrderedDict()
                    sk_data["Moorings lines"] = line
                    
                    if systems['Foundation'] == ['dummy']:
                        systems['Station keeping'].append(sk_data)
                        continue
                    
                    sk_data["Foundation"] = systems['Foundation'][i]
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

            for substf in substation_foundations:
                array_hierarcy[node]['Substation'].append(substf)
            
            if "Export cable" in systems and electrical_data is not None:
                
                markers = dev_electrical_bom[node]["Export cable"]['marker']
                kfactors = _get_cable_kfactors(markers,
                                               electrical_data)
                
                assert len(markers) == len(kfactors)
                
                array_hierarcy[node]["Export cable"] = \
                                 KSystem(array_hierarcy[node]["Export cable"],
                                         kfactors)
            
            if "Elec sub-system" in systems and electrical_data is not None:
                
                markers = dev_electrical_bom[node]["Elec sub-system"]['marker']
                kfactors = _get_cable_kfactors(markers,
                                               electrical_data)
                
                assert len(markers) == len(kfactors)
                
                array_hierarcy[node]["Elec sub-system"] = \
                            KSystem(array_hierarcy[node]["Elec sub-system"],
                                    kfactors)
        
        elif node[0:6] == 'device':
            
            if electrical_data is not None:
            
                markers = dev_electrical_bom[node]['marker']
                kfactors = _get_cable_kfactors(markers, electrical_data)
                
                assert len(markers) == len(kfactors)
                
                dev_electrical_hierarchy[node] = {'Elec sub-system': 
                    KSystem(dev_electrical_hierarchy[node]['Elec sub-system'],
                            kfactors)}
            
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
        
        if isinstance(array_dict[system], KSystem):
            
            array_system = array_dict[system]
            new_ids, new_kfactors = _strip_dummy_k(array_system.ids,
                                                   array_system.kfactors)
            if new_ids is None: continue
            comps = KSystem(new_ids, new_kfactors)
        
        else:
            
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
        
        if isinstance(subhub_dict[system], KSystem):
            
            subhub_system = subhub_dict[system]
            new_ids, new_kfactors = _strip_dummy_k(subhub_system.ids,
                                                   subhub_system.kfactors)
            if new_ids is None: continue
            comps = KSystem(new_ids, new_kfactors)
        
        else:
            
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
            
        elif (not isinstance(system, KSystem) and
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
            
            if isinstance(system, KSystem):
                
                new_ids, new_kfactors = _strip_dummy_k(system.ids,
                                                       system.kfactors)
                if new_ids is None: continue
                comps = KSystem(new_ids, new_kfactors)
            
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
    
    kfactors = None
    
    if isinstance(comps, KSystem):
        kfactors = comps.kfactors
        comps = comps.ids
    
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
            
            if kfactors is not None:
                kfactor = kfactors[idx]
                item = KSystem(item, kfactor)
            
            _build_pool_comps(item, new_serial, pool)
            new_parallel.add_item(next_pool_key)
        
        return
    
    elif n_list == 1:
        comps = comps[0]
        if kfactors is not None: kfactors = kfactors[0]
    
    for idx, item in enumerate(comps):
        
        if isinstance(item, list):
            
            new_serial = Serial()
            
            if kfactors is not None:
                kfactor = kfactors[idx]
                item = KSystem(item, kfactor)
            
            _build_pool_comps(item, new_serial, pool)
            
            next_pool_key = len(pool)
            pool[next_pool_key] = new_serial
            parent_link.add_item(next_pool_key)
            
        else:
            
            if kfactors is None:
                kfactor = None
            else:
                kfactor = kfactors[idx]
            
            next_pool_key = len(pool)
            new_component = Component(item, kfactor)
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
        elif isinstance(check, list):
            reduced.append(_strip_dummy(check))
        else:
            reduced.append(check)
        
    complist = [x for x in reduced if x is not None]
    if not complist: complist = None
    
    return complist


def _strip_dummy_k(compsids, kfactors):
    
    reduced_ids = []
    reduced_kfactors = []
    
    for compid, kfactor in zip(compsids, kfactors):
    
        if isinstance(compid, basestring):
            if compid == "dummy":
                reduced_ids.append(None)
                reduced_kfactors.append(None)
            else:
                reduced_ids.append(compid)
                reduced_kfactors.append(kfactor)
        elif isinstance(compid, list):
            new_compids, new_kfactors = _strip_dummy_k(compid, kfactor)
            reduced_ids.append(new_compids)
            reduced_kfactors.append(new_kfactors)
        else:
            reduced_ids.append(compid)
            reduced_kfactors.append(kfactor)
        
    idlist = [x for x in reduced_ids if x is not None]
    kfactorlist = [x for x in reduced_kfactors if x is not None]
    
    if not idlist:
        idlist = None
        kfactorlist = None
    
    return idlist, kfactorlist


def _get_cable_kfactors(markers, data):
    
    m2km = lambda x: x / 1e3 
    kfactors = []
    
    for item in markers:
        
        if isinstance(item, list):
            kfactors.append(_get_cable_kfactors(item, data))
            continue
        
        item_data = data[item]
        
        if getattr(item_data, "Installation_Type") in ["array", "export"]:
            kfactor = m2km(getattr(item_data, "Quantity"))
        else:
            kfactor = 1
        
        kfactors.append(kfactor)
    
    return kfactors
