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
import math
import logging
from copy import deepcopy
from collections import Counter

# External modules
import pandas as pd
import numpy as np

from .core import Syshier

# Start logging
module_logger = logging.getLogger(__name__)


class Variables(object):
    """
    #-------------------------------------------------------------------------- 
    #--------------------------------------------------------------------------
    #------------------ RAM Variables class
    #--------------------------------------------------------------------------
    #-------------------------------------------------------------------------- 
    Input of variables into this class 

    Args:        
        systype (str) [-]: system type: options:    'tidefloat', 
                                                    'tidefixed', 
                                                    'wavefloat', 
                                                    'wavefixed'
        eleclayout (str) [-]: electrical system architecture: options:   'radial'
                                                                         'singlesidedstring'
                                                                         'doublesidedstring'
                                                                         'multiplehubs'
        mtime (float) [hours]: mission time
        mttfreq (float) [hours]:  required mean time to failure
        moorfoundhierdict (dict): array-level mooring and foundation hierarchy: keys: array: substation foundation: substation foundation components (list) [-]
                                                                                      deviceXXX:  umbilical:   umbilical type (str) [-],
                                                                                                  foundation: foundation components (list) [-],
                                                                                                  mooring system: mooring components (list) [-]
        elechierdict (dict): array-level electrical system hierarchy: keys: array: export cable: export cable components (list) [-],
                                                                                   substation: substation components (list) [-],
                                                                                   layout: device layout
                                                                            deviceXXX: elec sub-system
        
    Attributes: 
        None
        
    Functions:    
    
    """
       
    def __init__(self, mtime,
                       systype,
                       dbdict,
                       mttfreq=None,
                       eleclayout=None,
                       elechierdict=None,
                       elecbomdict=None,
                       moorfoundhierdict=None,
                       moorfoundbomdict=None,
                       userhierdict=None,
                       userbomdict=None,
                       elecsupplementary=None):
                           
        self.mtime = mtime
        self.systype = systype
        self.dbdict = dbdict
        self.mttfreq = mttfreq
        self.eleclayout = eleclayout
        self.elechierdict = self.sanitise_dict(elechierdict)
        self.elecbomdict = deepcopy(elecbomdict)
        self.moorfoundhierdict = self.sanitise_dict(moorfoundhierdict)
        self.moorfoundbomdict = deepcopy(moorfoundbomdict)
        self.userhierdict = deepcopy(userhierdict)
        self.userbomdict = deepcopy(userbomdict)
        self.elecsupplementary = deepcopy(elecsupplementary)
        
        return
        
    @classmethod
    def sanitise_dict(cls, raw_dict=None):
        
        """Remove any double nested lists where the outer list has length 1"""
        
        if raw_dict is None: return None
        
        # Copy the input properly
        copy_dict = deepcopy(raw_dict)

        sane_dict = {}
        
        for key, value in copy_dict.iteritems():
            
            if key=='layout':
                pass
                
            elif isinstance(value, dict):
            
                value = cls.sanitise_dict(value)
              
            elif len(value) == 1 and isinstance(value[0], list):
            
                value = value[0]
              
            sane_dict[key] = value
     
        return sane_dict


def main(variables):
    """
    Reliability module main function
        
    Args:
        variables: input variables
    
    Returns:
    (tuple): tuple containing:
        
        mttf
        rsystime
        reliatab
    
    """
    
    module_logger.info("Start reliability calculation")
    
    mttfarrayruns = []
    rarrayruns = []
    
    # Time step
    dtime = 24
    time = np.linspace(0.0,
                       2.0 * variables.mtime,
                       int(2 * variables.mtime / dtime) + 1)
    
    # Determine which hierarchies/boms are available and create dummy
    # versions for any which are missing
    if (variables.moorfoundhierdict and
        variables.userhierdict and
        variables.elechierdict):
            
        fullset = True
        
    else:

        fullset = False
    
        devlist = []
        dummy_hier = {'Dummy sub-system': ['dummy']}
        dummy_bom =  {'Dummy sub-system':
                                {'quantity': Counter({'dummy': 1})}}
        
        if variables.userhierdict is not None:
            
            # If the User has specifed device subsystems but no
            # array-level subsystems generate dummy entries
            
            if not 'array' in variables.userhierdict:
                variables.userhierdict['array'] = deepcopy(dummy_hier)
                variables.userbomdict['array'] = deepcopy(dummy_bom)
                                                    
            if not 'subhub001' in variables.userhierdict:
                
                if (variables.elechierdict is not None and
                    'subhub001' in variables.elechierdict):  
                    
                    for devs in variables.elechierdict:
                        
                        if devs[:6] == 'subhub':
                            
                            variables.userhierdict[devs] = \
                                                    deepcopy(dummy_hier)
                            variables.userbomdict[devs] = \
                                                    deepcopy(dummy_bom)
                
                elif (variables.moorfoundhierdict is not None and
                      'subhub001' in variables.moorfoundhierdict):
                    
                    for devs in variables.moorfoundhierdict:
                        
                        if devs[:6] == 'subhub':
                            variables.userhierdict[devs] = \
                                                    deepcopy(dummy_hier)
                            variables.userbomdict[devs] = \
                                                    deepcopy(dummy_bom)
        
        # Scan available hierarchies for device numbers
        if variables.elechierdict is not None:
            
            for devs in variables.elechierdict:
                
                if devs not in devlist: devlist.append(devs)
                    
            if variables.moorfoundhierdict is None:
                
                variables.moorfoundhierdict = {}
                variables.moorfoundbomdict = {}
                                    
                for devs in devlist:
                    
                    if 'subhub' in devs or devs == 'array':
                        
                        variables.moorfoundhierdict[devs] = \
                                {'Substation foundation': ['dummy']}
                        variables.moorfoundbomdict[devs] = \
                                {'Substation foundation': \
                                    {'substation foundation type': 'dummy',
                                     'grout type': 'dummy'}}
                                     
                    elif devs[:6] == 'device':
                        
                        variables.moorfoundhierdict[devs] = \
                                            {'Umbilical': ['dummy'],
                                             'Mooring system': ['dummy'],
                                             'Foundation': ['dummy']}
                        variables.moorfoundbomdict[devs] = \
                            {'Umbilical': {'quantity':
                                                    Counter({'dummy': 1})},
                             'Foundation': {'quantity':
                                                    Counter({'dummy': 1})},
                             'Mooring system': {'quantity':
                                                    Counter({'dummy': 1})}}
            
        else:
            
            # For when the electrical network hierarchy doesn't exist
            variables.eleclayout = 'radial'
            variables.elechierdict = {}
            variables.elecbomdict = {}
            
            if variables.moorfoundhierdict is not None:
                
                for devs in variables.moorfoundhierdict:
                    if devs not in devlist:
                        devlist.append(devs)
                        
                devsonlylist = [x for x in devlist if x[:6] == 'device']
                subsonlylist = [[x] for x in devlist if x[:6] == 'subhub']
            
            if variables.userhierdict is not None:
                
                for devs in variables.userhierdict:
                    if devs not in devlist:
                        devlist.append(devs)
                
                devsonlylist = [x for x in devlist if x[:6] == 'device']
            
            if 'array' not in devlist:
                
                variables.moorfoundhierdict['array'] = \
                                {'Substation foundation': ['dummy']}
                variables.moorfoundbomdict['array'] = \
                                {'Substation foundation':
                                    {'quantity': Counter({'dummy': 1})}}
                
                devlist.append('array')
            
            for devs in devlist:
                
                if devs == 'array': 
                    
                    if subsonlylist:
                        layout = subsonlylist
                    else:
                        layout = [devsonlylist]
                    
                    variables.elechierdict[devs] = \
                                            {'Export cable': ['dummy'],
                                             'Substation': ['dummy'],
                                             'layout': layout}
                    variables.elecbomdict[devs] = \
                        {'Substation': {'marker': [-1], 
                                        'quantity': Counter({'dummy': 1})},
                         'Export cable':
                                     {'marker': [-1], 
                                      'quantity': Counter({'dummy': 1})}}
                                     
                elif devs[:6] == 'subhub':
                    
                    variables.eleclayout = 'multiplehubs'
                    variables.elechierdict[devs] = \
                                                {'Elec sub-system': ['dummy'],
                                                 'Substation': ['dummy'],
                                                 'layout': [devsonlylist]}
                    
                    variables.elecbomdict[devs] = \
                         {'Elec sub-system': {
                                        'marker': [-1], 
                                        'quantity': Counter({'dummy': 1})},
                         'Substation': {'marker': [-1], 
                                        'quantity': Counter({'dummy': 1})}}
                    
                    devsonlylist = []
                
                elif devs[:6] == 'device':
                    
                    variables.elechierdict[devs] = \
                                            {'Elec sub-system': ['dummy']}
                    variables.elecbomdict[devs] = \
                                        {'marker': [-1], 
                                         'quantity': Counter({'dummy': 1})} 
            
            if not variables.moorfoundhierdict:
                
                variables.moorfoundhierdict = {}
                variables.moorfoundbomdict = {}
                
                for devs in devlist:
                    
                    if devs == 'array':
                        
                        variables.moorfoundhierdict[devs] = \
                                {'Substation foundation': ['dummy']}
                        variables.moorfoundbomdict[devs] = \
                                {'Substation foundation':
                                    {'quantity': Counter({'dummy': 1})}}
                                    
                    elif devs[:6] == 'device':
                        
                        variables.moorfoundhierdict[devs] = \
                                            {'Umbilical': ['dummy'],
                                             'Mooring system': ['dummy'],
                                             'Foundation': ['dummy']}
                                             
                        variables.moorfoundbomdict[devs] = \
                                {'Umbilical':
                                    {'quantity': Counter({'dummy': 1})},
                                 'Foundation':
                                     {'quantity': Counter({'dummy': 1})},
                                 'Mooring system':
                                     {'quantity': Counter({'dummy': 1})}}
        
        if variables.userhierdict is None:
            
            variables.userhierdict = {}
            variables.userbomdict = {}
            
            for devs in devlist:
                
                variables.userhierdict[devs] = deepcopy(dummy_hier)
                variables.userbomdict[devs] = deepcopy(dummy_bom)

    
    hierarchy = Syshier(variables)
    hierarchy.arrayhiersub()
    
    for scen in range(0, 2):
        
        if scen == 0:
            severitylevel = 'critical'
        elif scen == 1:
            severitylevel = 'non-critical'
            
        for confid in range(0, 3): 
            
            if confid == 0:
                calcscenario = 'lower'
            elif confid == 1:
                calcscenario = 'mean'
            elif confid == 2:
                calcscenario = 'upper'
            
            hierarchy.arrayfrdictasgn(severitylevel, calcscenario, fullset)
            hierarchy.arrayfrvalues()
            hierarchy.ttf()
            hierarchy.rpn(severitylevel)
            
            if variables.eleclayout:
                
                mttfarrayruns.append(hierarchy.mttfarray[1] / 1e6)
                rarrayruns.append(hierarchy.rarrayvalue2[1])
                reliavals = [mttfarrayruns, rarrayruns]
                
            else:
                
                reliavals = [['n/a' for col in range(6)]
                                                    for row in range(2)]
    
    index = ['System MTTF (x10^6 hours)',
             'Rarray at ' + str(variables.mtime) + ' hours']
    columns = ['critical, lower',
               'critical, mean',
               'critical, upper',
               'non-critical, lower',
               'non-critical, mean',
               'non-critical, upper']
    
    reliatab = pd.DataFrame(reliavals,
                            index=index,
                            columns=columns)
    
    rsystime = []
    
    for ts in time:
        # Assumes exponential distribution for complete system reliability
        rsystime.append([ts, math.exp(-(hierarchy.mttfarray[1]**-1)  * ts)])
    
    mttf = hierarchy.mttfarray[1]
    
    return mttf, rsystime, reliatab
