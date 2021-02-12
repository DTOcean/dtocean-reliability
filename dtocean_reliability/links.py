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


class Link(object):
    
    def __init__(self, label=None):
        
        self.label = label
        self._items = []
    
    @property
    def items(self):
        return self._items
    
    def add_item(self, item):
        self._items.append(item)
    
    def __len__(self):
        return len(self._items)
    
    def __str__(self):
        out = "["
        nllen = 1
        if self.label is not None:
            out += "{}: ".format(self.label)
            nllen += len(self.label) + 2
        for item in self._items:
            out += "{} ".format(item) + "\n" + " " * nllen
        out = out.strip()
        out += "]"
        return out


class Serial(Link):
    
    def display(self, pool, pad=0):
        
        out = "["
        nllen = 1 + pad
        if self.label is not None:
            out += "{}: ".format(self.label)
            nllen += len(self.label) + 2
        for item in self._items:
            link = pool[item]
            out += "{} ".format(link.display(pool, nllen)) + "\n" + " " * nllen
        out = out.strip()
        out += "]"
        return out


class Parallel(Link):
    
    def display(self, pool, pad=0):
        
        out = "<"
        nllen = 1 + pad
        if self.label is not None:
            out += "{}: ".format(self.label)
            nllen += len(self.label) + 2
        for item in self._items:
            link = pool[item]
            out += "{} ".format(link.display(pool, nllen)) + "\n" + " " * nllen
        out = out.strip()
        out += ">"
        return out


class Component(object):
    
    def __init__(self, label):
        self.label = label
    
    def display(self, pool, pad=0):
        return self.__str__()
    
    def __str__(self):
        out = "'{}'".format(self.label)
        return out


def build_pool(array_hierarcy, device_hierachy):
    
    pool = {}
    array_link = Serial("array")
    
    build_pool_array(array_hierarcy, array_link, pool)
    add_layouts(array_hierarcy["layout"], array_link, pool, array_hierarcy)
    
    
    pool["array"] = array_link
    
    return pool


def build_pool_array(array_hierarcy, array_link, pool):
    
    array_systems = ('Export cable', 'Substation')
    array_dict = array_hierarcy["array"]
    
    for system in array_systems:
        
        comps = strip_dummy(array_dict[system])
        if comps is None: continue
        
        next_pool_key = len(pool)
        system_link = Serial(system)
        pool[next_pool_key] = system_link
        add_comps(comps, system_link, pool)
        
        array_link.add_item(next_pool_key)
    
    return


def add_layouts(nodes, parent_link, pool, array_hierarcy):
    
    n_list = len([True for x in nodes if isinstance(x, list)])
    
    if n_list > 1:
        
        next_pool_key = len(pool)
        new_parallel = Parallel()
        pool[next_pool_key] = new_parallel
        parent_link.add_item(next_pool_key)
        
        for item in nodes:
            next_pool_key = len(pool)
            new_serial = Serial()
            pool[next_pool_key] = new_serial
            add_layouts(item, new_serial, pool)
            new_parallel.add_item(next_pool_key)
        
        return
    
    elif n_list == 1:
        nodes = nodes[0]
    
    for item in nodes:
        
        if isinstance(item, list):
            
            next_pool_key = len(pool)
            new_serial = Serial()
            pool[next_pool_key] = new_serial
            add_layouts(item, new_serial, pool)
            parent_link.add_item(next_pool_key)
        
        elif "subhub" in item:
            
            next_pool_key = len(pool)
            new_subhub = Serial(item)
            pool[next_pool_key] = new_subhub
            build_pool_subhub(subhub_dict, new_subhub, pool, array_hierarcy)
            parent_link.add_item(next_pool_key)
            
        else:
            
            next_pool_key = len(pool)
            new_subhub = Serial(item)
            pool[next_pool_key] = new_subhub
            parent_link.add_item(next_pool_key)
    
    return


def build_pool_subhub(subhub_dict, subhub_link, pool, array_hierarcy):
    
    subhub_systems = ('Elec sub-system', 'Substation')
    
    for system in subhub_systems:
        
        comps = strip_dummy(subhub_dict[system])
        if comps is None: continue
        
        next_pool_key = len(pool)
        system_link = Serial(system)
        pool[next_pool_key] = system_link
        add_comps(comps, system_link, pool)
        
        subhub_link.add_item(next_pool_key)
    
    add_layouts(subhub_dict["layout"], subhub_link, pool, array_hierarcy)
    
    return

def add_comps(comps, parent_link, pool):
    
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
            add_comps(item, new_serial, pool)
            new_parallel.add_item(next_pool_key)
        
        return
    
    elif n_list == 1:
        comps = comps[0]
    
    for item in comps:
        
        if isinstance(item, list):
            
            next_pool_key = len(pool)
            new_serial = Serial()
            pool[next_pool_key] = new_serial
            add_comps(item, new_serial, pool)
            parent_link.add_item(next_pool_key)
        
        else:
            
            next_pool_key = len(pool)
            new_component = Component(item)
            pool[next_pool_key] = new_component
            parent_link.add_item(next_pool_key)
    
    return


def strip_dummy(comps):
    
    reduced = []
    
    for check in comps:
    
        if isinstance(check, basestring):
            if check == "dummy":
                reduced.append(None)
            else:
                reduced.append(check)
        else:
            reduced.append(strip_dummy(check))
        
    complist = [x for x in reduced if x is not None]
    if not complist: complist = None
    
    return complist


def find_all_labels(label, pool):
    
    all_labels = []
    all_indexes = []
    
    found_labels = -1
    
    while len(all_labels) > found_labels:
        
        found_labels += 1
        labels, index = find_labels(label, pool, exclude_labels=all_labels)
        
        if labels is not None:
            all_labels.append(labels)
            all_indexes.append(index)
    
    return all_labels, all_indexes


def find_labels(label, pool, pool_index=None, exclude_labels=None):
    
    labels = []
    
    if exclude_labels is None:
        exclude_labels = []
    
    if pool_index is None:
        pool_index = "array"
    
    link = pool[pool_index]
    
    if link.label == label:
        return label, pool_index
    
    if isinstance(link, Component):
        return None, None
    
    if link.label is not None:
        labels.append(link.label)
    
    for items in link._items:
        
        test_label, index = find_labels(label, pool, items)
        
        if test_label is not None:
            check_label = labels[:]
            if isinstance(test_label, list):
                check_label.extend(test_label)
            else:
                check_label.append(test_label)
            if check_label not in exclude_labels:
                return check_label, index
    
    return None, None
    
    