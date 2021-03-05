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

import abc

from .numerics import binomial, reliability, rpn


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


class ReliabilityBase(object):
    __metaclass__ = abc.ABCMeta
    
    def __init__(self):
        self._severity_level = "critical"
        
    def set_severity_level(self, set_severity_level):
        self._severity_level = set_severity_level
    
    @abc.abstractmethod
    def get_failure_rate(self, pool):
        return
    
    @abc.abstractmethod
    def get_mttf(self, pool):
        return
    
    def get_rpn(self, pool):
        
        failure_rate = self.get_failure_rate(pool)
        
        if failure_rate is None:
            return None
        
        return rpn(failure_rate, self._severity_level)
    
    def get_reliability(self, pool, time_hours):
        
        failure_rate = self.get_failure_rate(pool)
        
        if failure_rate is None:
            return None
        
        return reliability(failure_rate, time_hours)
    
    @abc.abstractmethod
    def get_probability_proportion(self, pool, label):
        return
    
    @abc.abstractmethod
    def reset(self, pool):
        return
    
    @abc.abstractmethod
    def display(self, pool, pad=0):
        return


class ReliabilityWrapper(ReliabilityBase):
    
    def __init__(self, pool, key):
        ReliabilityBase.__init__(self)
        self._pool = pool
        self._link = self._pool[key]
    
    def get_failure_rate(self):
        return self._link.get_failure_rate(self._pool)
    
    def get_mttf(self):
        return self._link.get_mttf(self._pool)
    
    def get_rpn(self, pool):
        return self._link.get_rpn(self._pool)
    
    def get_reliability(self, time_hours):
        return self._link.get_reliability(self._pool, time_hours)
    
    def get_probability_proportion(self, label):
        return self._link.get_probability_proportion(self._pool, label)
    
    def reset(self):
        raise NotImplementedError("Reset has no effect on ReliabilityWrapper")
    
    def display(self):
         return self._link.display(self._pool)
     
    def __len__(self):
        return len(self._link)
    
    def __str__(self):
        return self._link.__str__()


class Serial(Link, ReliabilityBase):
    
    def __init__(self, label=None):
        
        Link.__init__(self, label)
        ReliabilityBase.__init__(self)
    
    def get_failure_rate(self, pool):
        
        failure_rates = [pool[x].get_failure_rate(pool) for x in self._items
                             if pool[x].get_failure_rate(pool) is not None]
        
        if not failure_rates:
            return None
        
        return sum(failure_rates)
    
    def get_mttf(self, pool):
        
        failure_rate = self.get_failure_rate(pool)
        
        if failure_rate is None:
            return None
        
        return 1. / failure_rate
    
    def get_probability_proportion(self, pool, label):
        
        if label == self.label:
            return 1
        
        def f(x):
            fr = pool[x].get_failure_rate(pool)
            if fr is None: fr = 1
            return fr
        
        failure_rates = {x: f(x) for x in self._items if f(x) is not None}
        indices, rates = zip(*failure_rates.items())
        
        rates_sum = sum(rates)
        rates_norm = [x / rates_sum for x in rates]
        
        P = 0
        
        for idx, rate in zip(indices, rates_norm):
            
            link = pool[idx]
            
            if label == link.label:
                P += rate
                continue
            
            if isinstance(link, Component):
                continue
            
            P += rate * link.get_probability_proportion(pool, label)
        
        return P
    
    def reset(self, pool):
        
        for x in self._items:
            pool[x].reset(pool)
    
    def display(self, pool, pad=0):
        
        out = "["
        nllen = pad
        
        if self.label is not None:
            failure_rate = self.get_failure_rate(pool)
            if failure_rate is not None:
                out += "{}: {:e}: ".format(self.label, failure_rate)
            else:
                out += "{}: ".format(self.label)
            nllen += len(out)
        for item in self._items:
            link = pool[item]
            out += "{} ".format(link.display(pool, nllen)) + "\n" + " " * nllen
        
        out = out.strip()
        out += "]"
            
        return out
    
    def __str__(self):
        out = "Serial: {}".format(Link.__str__(self))
        return out


class Parallel(Link, ReliabilityBase):
    
    def __init__(self, label=None):
        
        Link.__init__(self, label)
        ReliabilityBase.__init__(self)
    
    def get_failure_rate(self, pool):
        
        mttf = self.get_mttf(pool)
        
        if mttf is None:
            return None
        
        return 1. / mttf
    
    def get_mttf(self, pool):
        
        failure_rates = [pool[x].get_failure_rate(pool) for x in self._items
                             if pool[x].get_failure_rate(pool) is not None]
        
        if not failure_rates:
            return None
        
        return binomial(failure_rates)
    
    def get_probability_proportion(self, pool, label):
        
        if label == self.label:
            return 1
        
        def f(x):
            fr = pool[x].get_failure_rate(pool)
            if fr is None: fr = 1
            return fr
        
        failure_rates = {x: f(x) for x in self._items if f(x) is not None}
        indices, rates = zip(*failure_rates.items())
        
        rates_sum = sum(rates)
        rates_norm = [x / rates_sum for x in rates]
        
        P = 0
        
        for idx, rate in zip(indices, rates_norm):
            
            link = pool[idx]
            
            if label == link.label:
                P += rate
                continue
            
            if isinstance(link, Component):
                continue
            
            P += rate * link.get_probability_proportion(pool, label)
        
        return P
    
    def reset(self, pool):
        
        for x in self._items:
            pool[x].reset(pool)
    
    def display(self, pool, pad=0):
        
        out = "<"
        nllen = 2 + pad
        
        if self.label is not None:
            failure_rate = self.get_failure_rate(pool)
            if failure_rate is not None:
                out += "{}: {:e}: ".format(self.label, failure_rate)
            else:
                out += "{}: ".format(self.label)
            nllen += len(out)
        
        for i, item in enumerate(self._items):
            link = pool[item]
            out += "{} ".format(link.display(pool, nllen)) + \
                                                "\n" + " " * (nllen - 1)
        
        out = out.strip()
        out += ">"
        
        return out
    
    def __str__(self):
        out = "Parallel: {}".format(Link.__str__(self))
        return out


class Component(ReliabilityBase):
    
    def __init__(self, label):
        self.label = label
        self._failure_rate = None
    
    def set_failure_rate(self, failure_rate):
        self._failure_rate = failure_rate
    
    def get_failure_rate(self, pool=None):
        
        if self._failure_rate is None:
            result = None
        else:
            result = self._failure_rate / 1e6
        
        return result
    
    def get_mttf(self, pool):
        
        failure_rate = self.get_failure_rate(pool)
        
        if failure_rate is None:
            return None
        
        return 1 / failure_rate
    
    def get_probability_proportion(self, pool, label):
        
        if label == self.label:
            return 1
        else:
            return 0
    
    def reset(self, pool):
        self._failure_rate = None
    
    def display(self, pool, pad=0):
        if self._failure_rate is not None:
            return "'{}: {:e}'".format(self.label, self.get_failure_rate())
        else:
            return "'{}'".format(self.label)
    
    def __str__(self):
        out = "Component: '{}'".format(self.label)
        return out


def find_all_labels(label,
                    pool,
                    partial_match=False,
                    filter_label=None,
                    return_one=False,
                    return_shortest=False):
    
    all_labels = []
    all_indexes = []
    
    found_labels = -1
    
    while len(all_labels) > found_labels:
        
        found_labels += 1
        labels, index = find_labels(label,
                                    pool,
                                    exclude_labels=all_labels,
                                    partial_match=partial_match)
        
        if (labels is not None and
            (filter_label is None or filter_label in labels)):
            
            all_labels.append(labels)
            all_indexes.append(index)
    
    if return_one:
        
        nlabels = len(all_labels)
        
        if nlabels == 0:
            err_str = "One label expected, but none found."
            raise RuntimeError(err_str)
        elif nlabels > 1:
            err_str = "One label expected, but {} found.".format(nlabels)
            raise RuntimeError(err_str)
        
        return all_labels[0], all_indexes[0]
    
    if return_shortest:
        
        minimum = min(all_labels)
        indices = [i for i, v in enumerate(all_labels) if v == minimum]
        
        if len(indices) > 1:
            err_str = "No unique shortest path was found"
            raise RuntimeError(err_str)
        
        min_idx = indices[0]
        
        return all_labels[min_idx], all_indexes[min_idx]
    
    if not all_labels:
        return None, None
    
    return all_labels, all_indexes


def find_labels(label,
                pool,
                pool_index=None,
                labels=None,
                exclude_labels=None,
                partial_match=False):
    
    if pool_index is None:
        pool_index = "array"
    
    if labels is None:
        labels = []
    else:
        labels = labels[:]
    
    if exclude_labels is None:
        exclude_labels = []
    
    link = pool[pool_index]
    
    if (link.label is not None and
        ((partial_match and
          isinstance(link.label, basestring) and
          label in link.label) or
         (not partial_match and link.label == label))):
        
        check_label = labels[:]
        check_label.append(link.label)
        
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
                                         exclude_labels,
                                         partial_match=partial_match)
        
        if test_labels is not None:
            return test_labels, index
    
    return None, None


def find_strings(pool, link="array"):
    
    all_strings = []
    
    hub = pool[link]
    
    for link in hub.items:
        
        item = pool[link]
        
        if item.label is not None and "device" in item.label:
            all_strings.append(item.label)
            continue
        
        if item.label is None or "subhub" in item.label:
            
            string = find_strings(pool, link)
            
            if string is not None:
                if "device" in string[0]:
                    all_strings.append(string)
                else:
                    all_strings.extend(string)
    
    if not all_strings:
        all_strings = None
    
    return all_strings
