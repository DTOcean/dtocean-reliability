"""
DTOcean Reliability Assessment Module (RAM)
Developed by: Renewable Energy Research Group, University of Exeter
              Mathew Topper
"""

# Built in modules
import os
import csv
import math
import pprint
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
                       mttfreq,
                       systype,
                       dbdict,
                       eleclayout=None,
                       elechierdict=None,
                       elecbomdict=None,
                       moorfoundhierdict=None,
                       moorfoundbomdict=None,
                       userhierdict=None,
                       userbomdict=None):
                           
        self.mtime = mtime
        self.mttfreq = mttfreq
        self.systype = systype
        self.eleclayout = eleclayout
        self.elechierdict = self.sanitise_dict(elechierdict)
        self.elecbomdict = deepcopy(elecbomdict)
        self.moorfoundhierdict = self.sanitise_dict(moorfoundhierdict)
        self.moorfoundbomdict = deepcopy(moorfoundbomdict)
        self.userhierdict = deepcopy(userhierdict)
        self.userbomdict = deepcopy(userbomdict)
        self.dbdict = dbdict
        
        return
        
    @classmethod
    def sanitise_dict(cls, raw_dict=None):
        
        """Remove any double nested lists where the outer list has length 1"""
        
        if raw_dict is None: return None

        sane_dict = {}
        
        for key, value in raw_dict.iteritems():
            
            if key=='layout':
                pass
                
            elif isinstance(value, dict):
            
                value = cls.sanitise_dict(value)
              
            elif len(value) == 1 and isinstance(value[0], list):
            
                value = value[0]
              
            sane_dict[key] = value
     
        return sane_dict

        
                
class Main(Syshier):
    """
    #-------------------------------------------------------------------------- 
    #--------------------------------------------------------------------------
    #------------------ WP4 Main class
    #--------------------------------------------------------------------------
    #-------------------------------------------------------------------------- 
    This is the main class of the WP4 module which inherits from the 
    Foundation, Mooring and Substation Foundation sub-modules 

    Functions:
        moorsub: top level mooring module
        
    Args:
        variables: input variables
    
    Attributes:
        deviceid (str) [-]: device identification number
        
    Returns:
        sysmoorinsttab(pandas)       
        
    """
    
    def __init__(self, variables): 
        super(Main, self).__init__(variables)
        
    def __call__(self):
    
        module_logger.info("Start reliability calculation")
        
        self.mttfarrayruns = []
        self.rarrayruns = []
        """ Time step """        
        self.dtime = 24
        self.time = np.linspace(0.0, 2.0 * self._variables.mtime,((2.0 * self._variables.mtime) / self.dtime) + 1.0)
        
        """ Determine which hierarchies/boms are available and create dummy versions for any which are missing """        
        if (self._variables.moorfoundhierdict and self._variables.userhierdict and self._variables.elechierdict):
            self.fullset = 'True'
        else:
            devlist = []
            devonlylist = []
            self.fullset = 'False'
            
            if self._variables.userhierdict: 
                """ If the User has specifed device subsystems but no array-level subsystems generate dummy entries """
                if not 'array' in self._variables.userhierdict:
                    self._variables.userhierdict['array'] = {'Dummy sub-system': ['dummy']}
                    self._variables.userbomdict['array'] = {'Dummy sub-system': {'quantity': Counter({'dummy': 1})}}
                if not 'subhub001' in self._variables.userhierdict:
                    if 'subhub001' in self._variables.elechierdict:  
                        for devs in self._variables.elechierdict:
                            if devs[:6] == 'subhub':
                                self._variables.userhierdict[devs] = {'Dummy sub-system': ['dummy']}
                                self._variables.userbomdict[devs] = {'Dummy sub-system': {'quantity': Counter({'dummy': 1})}}    
                    elif 'subhub001' in self._variables.moorfoundhierdict:  
                        for devs in self._variables.moorfoundhierdict:
                            if devs[:6] == 'subhub':
                                self._variables.userhierdict[devs] = {'Dummy sub-system': ['dummy']}
                                self._variables.userbomdict[devs] = {'Dummy sub-system': {'quantity': Counter({'dummy': 1})}} 
            """ Scan available hierarchies for device numbers """
            if self._variables.elechierdict:
                for devs in self._variables.elechierdict:
                    if devs not in devlist:
                        devlist.append(devs)
                if not self._variables.moorfoundhierdict:
                    self._variables.moorfoundhierdict = {}
                    self._variables.moorfoundbomdict = {}
                    for devs in devlist:
                        if devs == 'array':
                            self._variables.moorfoundhierdict[devs] = {'Substation foundation': ['dummy']}
                            self._variables.moorfoundbomdict[devs] = {'Substation foundation': {'substation foundation type': 'dummy', 'grout type': 'dummy'}}                            
                        elif devs[:6] == 'device':
                            self._variables.moorfoundhierdict[devs] = {'Umbilical': ['dummy'],
                                                                       'Mooring system': ['dummy'],
                                                                       'Foundation': ['dummy']}
                            self._variables.moorfoundbomdict[devs] = {'Umbilical': {'quantity': Counter({'dummy': 1})},
                                                                      'Foundation':  {'quantity': Counter({'dummy': 1})},
                                                                      'Mooring system':  {'quantity': Counter({'dummy': 1})}}                    
                        elif devs[:6] == 'subhub':
                            self._variables.moorfoundhierdict[devs] = {'Substation foundation': ['dummy']}
                            self._variables.moorfoundbomdict[devs] = {'Substation foundation': {'substation foundation type': 'dummy', 'grout type': 'dummy'}}
                if not self._variables.userhierdict:
                    self._variables.userhierdict = {}
                    self._variables.userbomdict = {}
                    for devs in devlist:
                        self._variables.userhierdict[devs] = {'Dummy sub-system': ['dummy']}  
                        self._variables.userbomdict[devs] = {'Dummy sub-system': {'quantity': Counter({'dummy': 1})}}             
            if not self._variables.elechierdict:
                """ For when the electrical network hierarchy doesn't exist """
                self._variables.eleclayout = 'radial'
                self._variables.elechierdict = {}
                self._variables.elecbomdict = {}
                if self._variables.moorfoundhierdict:
                    for devs in self._variables.moorfoundhierdict:
                        if devs not in devlist:
                            devlist.append(devs)                      
                    devsonlylist = [x for x in devlist if x[:6] == 'device']                    
                if self._variables.userhierdict:
                    for devs in self._variables.userhierdict:
                        if devs not in devlist:
                            devlist.append(devs)
                    devsonlylist = [x for x in devlist if x[:6] == 'device']
                if 'array' not in devlist:
                    self._variables.moorfoundhierdict['array'] = {'Substation foundation': ['dummy']}
                    self._variables.moorfoundbomdict['array'] = {'Substation foundation': {'quantity': Counter({'dummy': 1})}}
                    devlist.append('array')
                for devs in devlist:
                    if devs == 'array': 
                        self._variables.elechierdict[devs] = {'Export cable': ['dummy'],
                                                              'Substation': ['dummy'],
                                                              'layout': [devsonlylist]}
                        self._variables.elecbomdict[devs] = {'Substation': {'quantity': Counter({'dummy': 1})},
                                                             'Export cable': {'quantity': Counter({'dummy': 1})}}
                    elif devs[:6] == 'subhub': 
                        self._variables.elechierdict[devs] = {'Export cable': ['dummy'],
                                                              'Substation': ['dummy'],
                                                              'layout': [devsonlylist]}
                        self._variables.elecbomdict[devs] = {'Substation': {'quantity': Counter({'dummy': 1})}}
                    elif devs[:6] == 'device':
                        self._variables.elechierdict[devs] = {'Elec sub-system': ['dummy']}
                        self._variables.elecbomdict[devs] = {'quantity': Counter({'dummy': 1})} 
                if not self._variables.moorfoundhierdict:
                    self._variables.moorfoundhierdict = {}
                    self._variables.moorfoundbomdict = {}
                    for devs in devlist:
                        if devs == 'array':
                            self._variables.moorfoundhierdict[devs] = {'Substation foundation': ['dummy']}
                            self._variables.moorfoundbomdict[devs] = {'Substation foundation': {'quantity': Counter({'dummy': 1})}}
                        elif devs[:6] == 'device':
                            self._variables.moorfoundhierdict[devs] = {'Umbilical': ['dummy'],
                                                                       'Mooring system': ['dummy'],
                                                                       'Foundation': ['dummy']}
                            self._variables.moorfoundbomdict[devs] = {'Umbilical': {'quantity': Counter({'dummy': 1})},
                                                                      'Foundation': {'quantity': Counter({'dummy': 1})},
                                                                      'Mooring system': {'quantity': Counter({'dummy': 1})}} 
                if not self._variables.userhierdict:
                    self._variables.userhierdict = {}
                    self._variables.userbomdict = {}
                    for devs in devlist:
                        self._variables.userhierdict[devs] = {'Dummy sub-system': ['dummy']}    
                        self._variables.userbomdict[devs] = {'Dummy sub-system': {'quantity': Counter({'dummy': 1})}} 
                        
        self.arrayhiersub()
        for scen in range(0, 2):
            if scen == 0:
                self.severitylevel = 'critical'
            elif scen == 1:
                self.severitylevel = 'non-critical'            
            for confid in range(0, 3): 
                if confid == 0:
                    self.calcscenario = 'lower'
                elif confid == 1:
                    self.calcscenario = 'mean'
                elif confid == 2:
                    self.calcscenario = 'upper'   
                self.arrayfrdictasgn(self.severitylevel, self.calcscenario)
                self.arrayfrvalues()
                self.ttf()
                self.rpn()
                if self._variables.eleclayout:
                    self.mttfarrayruns.append(self.mttfarray[1] / 1e6)
                    self.rarrayruns.append(self.rarrayvalue[1])
                    self.reliavals = [self.mttfarrayruns, self.rarrayruns]
                else:
                    self.reliavals = [['n/a' for col in range(6)] for row in range(2)]
        
        self.reliatab = pd.DataFrame(self.reliavals, index=['System MTTF (x10^6 hours)', 'Rarray at ' + str(self._variables.mtime) + ' hours'], columns=['critical,lower', 'critical, mean', 'critical, upper', 'non-critical, lower', 'non-critical, mean', 'non-critical, upper'])
        rsystime = []
        for ts in self.time:
            """ Assumes exponential distribution for complete system reliability """
            rsystime.append([ts, math.exp(-(self.mttfarray[1]**-1)  * ts)])
        
        mttf = self.mttfarray[1]
        
        return mttf, rsystime
 