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

import itertools


def binomial(frpara):
    # Method from Elsayed, 2012
    
    n = len(frpara)
    frgroup = []
    frterms = []
    
    for frint in range(1, n + 1):
        
        frcomb = []
        frgroup = []
        
        for comb in itertools.combinations(frpara, frint):
            if frint == 1:
                frcomb.append(comb[0] ** -1.0)
            elif frint > 1:
                frcomb.append(comb)
        
        if frint == 1:
            frsum = sum(frcomb) 
        elif frint > 1:
            frcombs = []
            for combs in frcomb:
                frcombs.append(combs)
            frsum = map(sum, frcombs)
            for vals in frsum:
                frgroup.append(vals ** -1.0)
        
        if frint == 1:
            frgroupsum = frsum
        elif frint > 1:
            frgroupsum = sum(frgroup)
        
        if (frint % 2 == 0):
            frgroupsum = -frgroupsum
        
        frterms.append(frgroupsum)
    
    frparacalc = sum(frterms) + ((-1.0) ** (n + 1)) * (frterms[0]) ** -1.0
    
    return frparacalc
