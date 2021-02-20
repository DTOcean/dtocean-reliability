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

import sys

from numerics import binomial


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
        
        if self.label is not None:
            out += "{}: ".format(self.label)
        for item in self._items:
            out += "{} ".format(item)
        
        out = out.strip()
        out += "]"
        
        return out


class Serial(Link):
    
    def get_failure_rate(self, pool):
        result = sum(map(lambda x: pool[x].get_failure_rate(pool),
                         self._items))
        return result
    
    def get_mttf(self, pool):
        return 1 / self.get_failure_rate(pool)
    
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
    
    def __str__(self):
        out = "Serial: {}".format(Link.__str__(self))
        return out


class Parallel(Link):
    
    def get_failure_rate(self, pool):
        return 1 / self.get_mttf(pool)
    
    def get_mttf(self, pool):
        
        failure_rates = map(lambda x: pool[x].get_failure_rate(pool),
                            self._items)
        
        return binomial(failure_rates)
    
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
    
    def __str__(self):
        out = "Parallel: {}".format(Link.__str__(self))
        return out


class Component(object):
    
    def __init__(self, label):
        self.label = label
        self._failure_rate = None
    
    def set_failure_rate(self, failure_rate):
        self._failure_rate = failure_rate
    
    def get_failure_rate(self, pool=None):
        
        if self._failure_rate is None:
            result = sys.float_info.min
        else:
            result = self._failure_rate / 1e6
        
        return result
    
    def get_mttf(self, pool):
        return 1 / self.get_failure_rate()
    
    def display(self, pool, pad=0):
        if self._failure_rate is not None:
            return "'{}: {}'".format(self.label, self.get_failure_rate())
        else:
            return "'{}'".format(self.label)
    
    def __str__(self):
        out = "Component: '{}'".format(self.label)
        return out


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


def find_labels(label,
                pool,
                pool_index=None,
                labels=None,
                exclude_labels=None):
    
    if pool_index is None:
        pool_index = "array"
    
    if labels is None:
        labels = []
    else:
        labels = labels[:]
    
    if exclude_labels is None:
        exclude_labels = []
    
    link = pool[pool_index]
    
    if link.label == label:
        
        check_label = labels[:]
        check_label.append(label)
        
        if check_label not in exclude_labels:
            return check_label, pool_index
        else:
            return None, None
    
    if isinstance(link, Component):
        return None, None
    
    if link.label is not None:
        labels.append(link.label)
    
    for items in link._items:
        
        test_labels, index = find_labels(label,
                                         pool,
                                         items,
                                         labels,
                                         exclude_labels)
        
        if test_labels is not None:
            return test_labels, index
    
    return None, None
