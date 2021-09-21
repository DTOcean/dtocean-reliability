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
from collections import OrderedDict

from .graph import (Component,
                    ReliabilityWrapper,
                    find_all_labels,
                    find_strings)
from .parse import (check_nodes,
                    complete_networks,
                    combine_networks,
                    build_pool)

# Start logging
module_logger = logging.getLogger(__name__)


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
        
        check_nodes(electrical_network, moorings_network)
        
        (electrical_network,
         moorings_network,
         user_network) = complete_networks(electrical_network,
                                           moorings_network,
                                           user_network)
        
        (array_hierarcy,
         device_hierachy) = combine_networks(electrical_network,
                                             moorings_network,
                                             user_network)
        
        self._db = database
        self._pool = build_pool(array_hierarcy, device_hierachy)
        self._subhub_indices = _get_indices(self._pool, "subhub")
        self._device_indices = _get_indices(self._pool, "device")
        self._curtailments = _get_curtailments(self._pool)
        self._system_root = ["device", "subhub", "array"]
    
    def set_failure_rates(self, severitylevel='critical',
                                calcscenario='mean',
                                k_factors=None,
                                inplace=False):
        
        # pylint: disable=protected-access
        
        if inplace:
            network = self
        else:
            network = copy(self)
            network._pool = deepcopy(self._pool)
        
        _set_component_failure_rates(network._pool,
                                     network._db,
                                     severitylevel,
                                     calcscenario,
                                     k_factors=k_factors)
        
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
            
            reserved_str = ", ".join(self._system_root)
            err_str = ("Subsystem name may not contain reserved keywords: "
                       "{}").format(reserved_str)
            raise ValueError(err_str)
    
    def __getitem__(self, key):
        return ReliabilityWrapper(self._pool, key)
    
    def __len__(self):
        
        result = 0
        
        for s in self._pool:
            if self._pool[s].label is not None:
                result += 1
        
        return result


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


def _set_component_failure_rates(pool,
                                 dbdict,
                                 severitylevel,
                                 calcscenario,
                                 k_factors=None):
    
    # For components with an id number look up respective failure rates 
    # otherwise for designed components (i.e. shallow/gravity foundations, 
    # direct embedment anchors and suction caissons) in addition to 
    # grouted jointed use generic failure rate of 1.0x10^-4 failures 
    # per annum (10 / 876 failures per 10^6 hours)
    
    # Note:
    #  * If no data for a particular calculation scenario, failure rate 
    #    defaults to mean value
    #  * If no non-critical failure rate data is available use critical values
    
    def set_failure_rate(item, failure_rate, severitylevel, k_factors=None):
        
        item.set_severity_level(severitylevel)
        
        if k_factors is not None and item.marker in k_factors:
            failure_rate *= k_factors[item.marker]
        
        item.set_failure_rate(failure_rate)
        
        return
    
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
            item.set_severity_level(severitylevel)
            continue
        
        if item.label in designed_comps:
            item.set_severity_level(severitylevel)
            item.set_failure_rate(10. / 876)
            continue
        
        dbitem = deepcopy(dbdict[item.label]['item10'])
        severity_failure_rates = dbitem[severity_key]
        
        if severity_failure_rates[cs] > 0.0:
            failure_rate = severity_failure_rates[cs]
            set_failure_rate(item, failure_rate, severitylevel, k_factors)
            continue
        
        if severity_failure_rates[mean_idx] > 0.0:
            failure_rate = severity_failure_rates[mean_idx]
            set_failure_rate(item, failure_rate, severitylevel, k_factors)
            continue
        
        other_failure_rates = dbitem[other_key]
        
        if other_failure_rates[cs] > 0.0:
            
            failure_rate = other_failure_rates[cs]
            set_failure_rate(item,
                             failure_rate,
                             other_severitylevel,
                             k_factors)
            
            continue
        
        if other_failure_rates[mean_idx] > 0.0:
            
            failure_rate = other_failure_rates[mean_idx]
            set_failure_rate(item,
                             failure_rate,
                             other_severitylevel,
                             k_factors)
            
            continue
        
        err_str = ("No failure rate data is set for component "
                   "'{}'").format(item.label)
        raise RuntimeError(err_str)
    
    return
