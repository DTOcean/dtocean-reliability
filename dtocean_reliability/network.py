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
import logging
from copy import copy, deepcopy
from collections import Counter, OrderedDict

from .data import (Component,
                   Parallel,
                   ReliabilityWrapper,
                   Serial,
                   find_all_labels,
                   find_strings)

# Start logging
module_logger = logging.getLogger(__name__)


class SubNetwork(object):
    
    def __init__(self, hierarchy, bill_of_materials):
        
        self.hierarchy = hierarchy
        self.bill_of_materials = bill_of_materials
        
        return


class Network(object):
    
    def __init__(self, database,
                       electrical_network = None,
                       moorings_network = None,
                       user_network = None):
        
        if (electrical_network is None and
            moorings_network is None and
            user_network is None):
            
            err_msg = "At least one network input must be provided"
            raise ValueError (err_msg)
        
        _check_nodes(electrical_network, moorings_network)
        
        (electrical_network,
         moorings_network,
         user_network) = _complete_networks(electrical_network,
                                            moorings_network,
                                            user_network)
        
        (array_hierarcy,
         device_hierachy) = _combine_networks(electrical_network,
                                              moorings_network,
                                              user_network)
        
        self._db = database
        self._pool = _build_pool(array_hierarcy, device_hierachy)
        self._subhub_indices = _get_indices(self._pool, "subhub")
        self._device_indices = _get_indices(self._pool, "device")
        self._curtailments = _get_curtailments(self._pool)
        self._system_root = ["device", "subhub", "array"]
    
    def set_failure_rates(self, severitylevel='critical',
                                calcscenario='mean',
                                inplace=False):
        
        if inplace:
            network = self
        else:
            network = copy(self)
            network._pool = deepcopy(self._pool)
        
        _set_component_failure_rates(network._pool,
                                     network._db,
                                     severitylevel,
                                     calcscenario)
        
        if inplace:
            result = None
        else:
            result = network
        
        return result
    
    def get_systems_metrics(self, time_hours=None):
        
        indices = []
        systems = []
        failure_rates = []
        mttfs = []
        rpns = []
        reliabilities = []
        
        # Array
        array = self._pool["array"]
        indices.append("array")
        systems.append("array")
        failure_rates.append(array.get_failure_rate(self._pool))
        mttfs.append(array.get_mttf(self._pool))
        rpns.append(array.get_rpn(self._pool))
        
        if time_hours is not None:
            reliabilities.append(array.get_reliability(self._pool, time_hours))
        
        # Subhub
        if self._subhub_indices is not None:
            
            subhub_names = sorted(self._subhub_indices.keys())
            
            for name in subhub_names:
                
                idx = self._subhub_indices[name]
                subhub = self._pool[idx]
                
                indices.append(idx)
                systems.append(name)
                failure_rates.append(subhub.get_failure_rate(self._pool))
                mttfs.append(subhub.get_mttf(self._pool))
                rpns.append(subhub.get_rpn(self._pool))
                
                if time_hours is not None:
                    reliabilities.append(subhub.get_reliability(self._pool,
                                                                time_hours))
        
        # Devices
        if self._device_indices is not None:
            
            device_names = sorted(self._device_indices.keys())
            
            for name in device_names:
                
                idx = self._device_indices[name]
                device = self._pool[idx]
                
                indices.append(idx)
                systems.append(name)
                failure_rates.append(device.get_failure_rate(self._pool))
                mttfs.append(device.get_mttf(self._pool))
                rpns.append(device.get_rpn(self._pool))
                
                if time_hours is not None:
                    reliabilities.append(device.get_reliability(self._pool,
                                                                time_hours))
        
        if set(failure_rates) == set([None]): return None
        
        result = OrderedDict()
        result["Link"] = indices
        result["System"] = systems
        result["lambda"] = failure_rates
        result["MTTF"] = mttfs
        result["RPN"] = rpns
    
        if time_hours is not None:
            key = "R ({} hours)".format(time_hours)
            result[key] = reliabilities
        
        return result
    
    def get_subsystem_metrics(self, subsystem_name, time_hours=None):
        
        def get_lowest_system(labels):
            
            for system in self._system_root:
                for label in labels:
                    if system in label:
                        return label
            
            raise ValueError("No system found")
        
        self._check_not_system(subsystem_name)
    
        all_labels, indices = find_all_labels(subsystem_name, self._pool)
        
        if all_labels is None: return None
        
        systems = []
        failure_rates = []
        mttfs = []
        rpns = []
        reliabilities = []
        
        for labels, index in zip(all_labels, indices):
            
            link = self._pool[index]
            
            systems.append(get_lowest_system(labels))
            failure_rates.append(link.get_failure_rate(self._pool))
            mttfs.append(link.get_mttf(self._pool))
            rpns.append(link.get_rpn(self._pool))
            
            if time_hours is not None:
                reliabilities.append(link.get_reliability(self._pool,
                                                          time_hours))
        
        # Build curtailments
        curtailments = []
        
        for system in systems:
            
            if system == "array" or "subhub" in system:
                curtailments.append(self._curtailments[system])
                continue
            
            if subsystem_name in ("Array elec sub-system",
                                  "Elec sub-system"):
                
                curtailments.append(self._curtailments[system])
                continue
            
            curtailments.append([system])
        
        if set(failure_rates) == set([None]): return None

        result = OrderedDict()
        result["Link"] = indices
        result["System"] = systems
        result["lambda"] = failure_rates
        result["MTTF"] = mttfs
        result["RPN"] = rpns
        
        if time_hours is not None:
            key = "R ({} hours)".format(time_hours)
            result[key] = reliabilities
        
        result["Curtails"] = curtailments
        
        return result
    
    def display(self):
        return self._pool['array'].display(self._pool)
    
    def _check_not_system(self, name):
                
        if any([x in name for x in self._system_root]):
            
            reserved_str = ", ".format(self._system_root)
            err_str = ("Subsystem name may not contain reserved keywords: "
                       "{}").format(reserved_str)
            raise ValueError(err_str)
    
    def _find_system_index(self, system_name):
        
        try:
            
            _, index = find_all_labels(system_name,
                                       self._pool,
                                       return_one=True)
        
        except RuntimeError:
            
            try:
                _, index = find_all_labels(system_name,
                                           self._pool,
                                           return_shortest=True)
            except RuntimeError:
                err_str = "No unique subsystem failure rate could be found"
                raise RuntimeError(err_str)
        
        return index
    
    def __getitem__(self, key):
        return ReliabilityWrapper(self._pool, key)
    
    def __len__(self):
        
        result = 0
        
        for s in self._pool:
            if self._pool[s].label is not None:
                result += 1
        
        return result


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


def _combine_networks(electrical_network,
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
        
        elif node[0:6] == 'device':
            
            device_hierachy[node] = {
                    'M&F sub-system': dev_moorings_hierarchy[node], 
                    'Array elec sub-system': dev_electrical_hierarchy[node],
                    'User sub-systems': dev_user_hierarchy[node]}
    
    return array_hierarcy, device_hierachy


def _get_indices(pool, label):
        
    labels, indices = find_all_labels(label, pool, partial_match=True)
    if labels is None: return None
    
    subhub_indices = {}
    subhub_names = [x[-1] for x in labels]
    
    for name, idx in zip(subhub_names, indices):
        subhub_indices[name] = idx
    
    return subhub_indices


def _get_curtailments(pool):
    
    hublist, _ = find_all_labels('device',
                                 pool,
                                 partial_match=True)
    device_strings = find_strings(pool)
    
    curtailments = {}
    device_names = [x[-1] for x in hublist]
    
    # Array
    curtailments["array"] = device_names
    
    # Subhubs
    if len(hublist[0]) == 3:
        
        subhub_names = set([x[1] for x in hublist])
        
        for name in subhub_names:
            curtailments[name] = [x[-1] for x in hublist if x[1] == name]
    
    # devices
    for name in device_names:
        for string in device_strings:
            
            if name in string:
                device_idx = string.index(name)
                dev_curtails = string[device_idx:]
                curtailments[name] = dev_curtails
    
    return curtailments


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
            
        elif isinstance(system[0], dict):
            
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
        elif isinstance(check, list):
            reduced.append(_strip_dummy(check))
        else:
            reduced.append(check)
        
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
    
    critical_key = 'failratecrit'
    non_critical_key = 'failratenoncrit'
    
    if severitylevel == 'critical':
        severity_key = critical_key
        other_key = non_critical_key
        other_severitylevel = 'noncritical'
    elif severitylevel == 'noncritical':
        severity_key = non_critical_key
        other_key = critical_key
        other_severitylevel = 'critical'
    else:
        err_str = ("Argument 'severitylevel' may only take values "
                   "'critical' or 'noncritical'")
        raise ValueError(err_str)
    
    lower_idx = 0
    mean_idx = 1
    upper_idx = 2
    
    if calcscenario == 'lower':
        cs = lower_idx
    elif calcscenario == 'mean':
        cs = mean_idx
    elif calcscenario == 'upper':
        cs = upper_idx
    else:
        err_str = "Argument 'calcscenario' may only take values 0, 1, or 2"
        raise ValueError(err_str)
    
    for item in pool.values():
        
        if not isinstance(item, Component):
            continue
        
        if item.label in designed_comps:
            item.set_failure_rate(10. / 876)
            item.set_severity_level(severitylevel)
            continue
        
        dbitem = deepcopy(dbdict[item.label]['item10'])
        severity_failure_rates = dbitem[severity_key]
        
        if severity_failure_rates[cs] > 0.0:
            failure_rate = severity_failure_rates[cs]
            item.set_failure_rate(failure_rate)
            item.set_severity_level(severitylevel)
            continue
        
        if severity_failure_rates[mean_idx] > 0.0:
            failure_rate = severity_failure_rates[mean_idx]
            item.set_failure_rate(failure_rate)
            item.set_severity_level(severitylevel)
            continue
        
        other_failure_rates = dbitem[other_key]
        
        if other_failure_rates[cs] > 0.0:
            failure_rate = other_failure_rates[cs]
            item.set_failure_rate(failure_rate)
            item.set_severity_level(other_severitylevel)
            continue
        
        if other_failure_rates[mean_idx] > 0.0:
            failure_rate = other_failure_rates[mean_idx]
            item.set_failure_rate(failure_rate)
            item.set_severity_level(other_severitylevel)
            continue
        
        err_str = ("No failure rate data is set for component "
                   "'{}'").format(item.label)
        raise RuntimeError(err_str)
        
        item.set_failure_rate(failure_rate)
    
    return
