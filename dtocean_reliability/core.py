"""
DTOcean Reliability Assessment Module (RAM)
Developed by: Renewable Energy Research Group, University of Exeter
              Mathew Topper
"""

# Built in modules
import os
import csv
import copy
import math
import time
import logging
import itertools
from collections import Counter, OrderedDict, Sequence, defaultdict

# External module import
import numpy as np
import pandas as pd

# Start logging
module_logger = logging.getLogger(__name__)

 
class Syshier(object):
    """
    System hierarchy class
    """
    def __init__(self, variables):        
        self._variables = variables
        
    def arrayhiersub(self):        
        self.founddelflag = 'False'
        """ Read in sub-system hierarchies and consolidate into device- and array-level hierarchies """        
        self.devhierdict = {}
        self.arrayhierdict = {}                
        for deviceID in self._variables.moorfoundhierdict:          
            self.anctype = []
            if (deviceID[0:6] == 'device'):  
                if self._variables.moorfoundhierdict[deviceID]['Foundation'] == ['dummy']:
                    continue
                else:
                    if self._variables.systype in ('tidefloat','wavefloat'):
                        self.linecomps = []
                        self.anctype = self._variables.moorfoundhierdict[deviceID]['Foundation']   
                                              
                        """ Append anchor into each mooring line and delete foundation field from dictionary """
                        for intline,line in enumerate(self._variables.moorfoundhierdict[deviceID]['Mooring system']):
                            self._variables.moorfoundhierdict[deviceID]['Mooring system'][intline].append(self.anctype[intline][0])
                        del self._variables.moorfoundhierdict[deviceID]['Foundation']    
                        self.founddelflag = 'True'
                    elif self._variables.systype in ('tidefixed','wavefixed'):
                        # if 'Mooring system' in self._variables.moorfoundhierdict.keys():
                        del self._variables.moorfoundhierdict[deviceID]['Mooring system'] 
                    
#        self.arrayhierdict2 = copy.deepcopy( self.arrayhierdict)         
        
        for deviceID in self._variables.elechierdict:
            
            if (deviceID == 'array' or deviceID[0:6] == 'subhub'):
#                """ self._variables.elechierdict is used to define the top level array architecture """
                
                # Break down parallel definitions into serial
                check_dict = self._variables.elechierdict[deviceID]

                self.arrayhierdict[deviceID] = check_dict 
#                """ Append substation foundation """ 
                substation_foundations = self._variables.moorfoundhierdict[
                                            deviceID]['Substation foundation']
                 
                for substf in substation_foundations:
                    self.arrayhierdict[deviceID]['Substation'].append(substf)
                                        
                del self._variables.moorfoundhierdict[
                                            deviceID]['Substation foundation']
                    
            elif deviceID[0:6] == 'device':   
#                """ Create device hierarchy dictionary """
                self.devhierdict[deviceID] = {'M&F sub-system': self._variables.moorfoundhierdict[deviceID], 
                                              'Array elec sub-system': self._variables.elechierdict[deviceID], 
                                              'User sub-systems': self._variables.userhierdict[deviceID]}
                       
    def arrayfrdictasgn(self, severitylevel, calcscenario):                
        """ Read in relevant failure rate data from the mooring and electrical bill of materials """
        self.arrayfrdict = {}   
        self.devicecompscandict = {}
        self.complist = []
        self.compfrvalueslist = [] 

        for deviceID in self._variables.moorfoundhierdict:                
            for subsys in self._variables.moorfoundhierdict[deviceID]:       
                """ Compile list of components """                 
                if subsys == 'Mooring system':    
                    if self._variables.moorfoundbomdict[deviceID][subsys]:
                        for comps in self._variables.moorfoundbomdict[deviceID][subsys]['quantity']:                        
                            if comps not in ["dummy", "n/a"]:
                                self.complist.append(comps)
                    
                if subsys == 'Foundation': 
                    if self._variables.moorfoundbomdict[deviceID][subsys]:
                        for comps in self._variables.moorfoundbomdict[deviceID][subsys]['quantity']:                                
                            if (comps not in ["dummy", "n/a"] or
                                comps in ('gravity', 
                                          'shallowfoundation', 
                                          'suctioncaisson', 
                                          'directembedment',
                                          'grout')):                            
                                self.complist.append(comps) 
                elif subsys == 'Umbilical':
                    if self._variables.moorfoundbomdict[deviceID][subsys]:
                        for comps in self._variables.moorfoundbomdict[deviceID][subsys]['quantity']: 
                            if comps not in ["dummy", "n/a"]:
                                self.complist.append(comps)              
            if self.founddelflag == 'True':
                for subsys in self._variables.moorfoundbomdict[deviceID]: 
                    if subsys == 'Foundation': 
                        for comps in self._variables.moorfoundbomdict[deviceID][subsys]['quantity']:    
                            if (comps not in ["dummy", "n/a"] or
                                comps in ('gravity', 
                                          'shallowfoundation', 
                                          'suctioncaisson', 
                                          'directembedment',
                                          'grout')):                            
                                self.complist.append(comps)
        for deviceID in self._variables.elecbomdict:
            if (deviceID == 'array' or deviceID[0:6] == 'subhub'):            
                for subsys in self._variables.elecbomdict[deviceID]:
                    """ Compile list of components """
                    if subsys == 'Substation':
                        for comps in self._variables.elecbomdict[deviceID][subsys]['quantity']:
                            self.complist.append(comps)
                    elif subsys == 'Export cable':
                        for comps in self._variables.elecbomdict[deviceID][subsys]['quantity']:
                            self.complist.append(comps)                
            else:
                for comps in self._variables.elecbomdict[deviceID]['quantity']:                       
                    self.complist.append(comps)           
        for deviceID in self._variables.userbomdict:
            for subsys in self._variables.userbomdict[deviceID]:
                for comps in self._variables.userbomdict[deviceID][subsys]['quantity']:                       
                    self.complist.append(comps)               
        for deviceID in self.arrayhierdict:
            if (deviceID == 'array' or deviceID[0:6] == 'subhub'):
                for subsys in self.arrayhierdict[deviceID]:
                    if subsys == 'Substation':                        
                        for comps in self.arrayhierdict[deviceID][subsys]:
                            self.complist.append(comps)                           
        self.complist = list(OrderedDict.fromkeys(self.complist))  
        
        if self.fullset == 'False':
            self.complist.append('dummy')
        
        # Will only remove one if this is desired
        if 'n/a' in self.complist: self.complist.remove('n/a')
        
        # Remove "not required"
        self.complist = [comp for comp in self.complist
                                         if "not required" not in str(comp)]
        
        if calcscenario == 'lower':
            cs = 0
        elif calcscenario == 'mean':
            cs = 1
        elif calcscenario == 'upper':
            cs = 2
        for comps in self.complist:          
            self.arrayfrdict[str(comps)] = {}
            if comps not in ["dummy", "n/a", "grout","ideal","shallowfoundation","gravityfoundation","gravity"]:
                for dbitem in self._variables.dbdict: 
                    """ For components with an id number look up respective failure rates """
                    if dbitem == comps:
                        if severitylevel == 'critical':                           
                            if self._variables.dbdict[dbitem]['item10']['failratecrit'][cs] == 0.0:
                                """ If no data for a particular calculation scenario, failure rate defaults to mean value """                             
                                self.arrayfrdict[comps] = self._variables.dbdict[dbitem]['item10']['failratecrit'][1]
                                self.compfrvalueslist.append((comps, self._variables.dbdict[dbitem]['item10']['failratecrit'][1]))
                            else:
                                self.arrayfrdict[comps] = self._variables.dbdict[dbitem]['item10']['failratecrit'][cs]
                                self.compfrvalueslist.append((comps, self._variables.dbdict[dbitem]['item10']['failratecrit'][cs]))
                        else:
                            if self._variables.dbdict[dbitem]['item10']['failratenoncrit'][1] == 0.0:
                                """ If no non-critical failure rate data is available use critical values """
                                self._variables.dbdict[dbitem]['item10']['failratenoncrit'] = self._variables.dbdict[dbitem]['item10']['failratecrit']
                            if self._variables.dbdict[dbitem]['item10']['failratenoncrit'][cs] == 0.0:
                                 """ If no data for a particular calculation scenario, failure rate defaults to mean value """                             
                                 self.arrayfrdict[comps] = self._variables.dbdict[dbitem]['item10']['failratenoncrit'][1]
                                 self.compfrvalueslist.append((comps, self._variables.dbdict[dbitem]['item10']['failratenoncrit'][1]))
                            else:
                                 self.arrayfrdict[comps] = self._variables.dbdict[dbitem]['item10']['failratenoncrit'][cs]
                                 self.compfrvalueslist.append((comps, self._variables.dbdict[dbitem]['item10']['failratenoncrit'][cs]))
            else:
                """ For designed components (i.e. shallow/gravity foundations, direct embedment anchors and 
                    suction caissons) in addition to grouted jointed use generic failure rate of 1.0x10^-4 
                    failures per annum (1.141x10^-14 failures per 10^6 hours) """
                self.arrayfrdict[comps] = 1.141 * 10.0 ** -14.0
                self.compfrvalueslist.append((comps, 1.141 * 10.0 ** -14.0))     
        # logmsg = [""]
        # logmsg.append('self.arrayfrdict {}'.format(self.arrayfrdict))
        # module_logger.info("\n".join(logmsg)) 
    def arrayfrvalues(self): 
        """ Generate list of relevant failure rates in the correct heirarchy positions """           
        self.frvalues = []  
        self.devfrvalues = []
        self.subsystems2 = []
        self.frvalues2 = []
        self.rsysvalues = []
        self.stringlist = []
        self.subhubdevlist = []
        self.subsyslendict = {}   
        nestdevs = []
        
        if self._variables.eleclayout == 'multiplehubs':
            """ Construct nested list for all devices and subhubs """
            subhubnum = len(self.arrayhierdict['array']['layout'])
            for intsubhub, subhub in enumerate(self.arrayhierdict['array']['layout']):       
                nestdevs.append(self.arrayhierdict['subhub'+ '{0:03}'.format(intsubhub+1)]['layout'])
            self.devfrvalues = copy.deepcopy(nestdevs)
        else:   
            # logmsg = [""]
            # logmsg.append('self.arrayhierdict {}'.format(self.arrayhierdict))
            self.devfrvalues.append(copy.deepcopy(self.arrayhierdict['array']['layout']))
            # logmsg.append('self.devfrvalues {}'.format(self.devfrvalues))
            # logmsg.append('self.devhierdict {}'.format(self.devhierdict))
            # module_logger.info("\n".join(logmsg)) 
        # logmsg = [""]
        for intsubhub, subhub in enumerate(self.devfrvalues):  
 
            # logmsg.append('subhub {}'.format(subhub))        
            for intstring, strings in enumerate(subhub):    
                # logmsg.append('strings {}'.format(strings))
                for devs in strings:                          
                    # logmsg.append('devs {}'.format(devs))
                    self.stringlist.append((intstring,devs))    
                    self.subhubdevlist.append((intsubhub,devs))                     
                    self.compvalues = []                        
                    self.subsystems = [] 
                    self.devlist = [] 
                    for subsys in self.devhierdict[devs]: 
                        # logmsg.append('subsys {}'.format(subsys))
                        if subsys in ('M&F sub-system','User sub-systems','Array elec sub-system'):                            
                            if type(self.devhierdict[devs][subsys]) is dict:                                
                                for subsubsys in self.devhierdict[devs][subsys]:
                                    # logmsg.append('subsubsys {}'.format(subsubsys))                                
                                    if type(self.devhierdict[devs][subsys][subsubsys]) is list:
                                        for comps in self.devhierdict[devs][subsys][subsubsys]:  
                                            # logmsg.append('comps 1 {}'.format(comps)) 
                                            if comps in ['n/a', ['n/a']]: 
                                                # self.devhierdict[devs][subsys][subsubsys].remove(comps)
                                                # logmsg.append('comps 2 {}'.format(self.devhierdict[devs][subsys][subsubsys])) 
                                                continue
                                            # if ['n/a'] in self.devhierdict[devs][subsys][subsubsys]: self.devhierdict[devs][subsys][subsubsys].remove(comps)
                                            self.compvalues.append(comps)                                            
                                            if type(comps) is list:
                                                self.subsyslist = []   
                                                self.subsysdevlist = [] 
                                                for indcomp in comps:
                                                    # logmsg.append('comps {}'.format(indcomp)) 
                                                    if indcomp == 'n/a':
                                                        pass
                                                    else:
                                                        if subsys == 'User sub-systems':                                                        
                                                            self.subsyslist.append((subsubsys))
                                                        else:
                                                            self.subsyslist.append((subsys))
                                                        self.subsysdevlist.append((devs))
                                                self.subsystems.append(self.subsyslist)
                                                self.devlist.append(self.subsysdevlist)
                                            else: 
                                                if subsys == 'User sub-systems':                                                    
                                                    self.subsystems.append((subsubsys))
                                                else:
                                                    self.subsystems.append((subsys))
                                                self.devlist.append(devs)
                                    else:
                                        if 'n/a' in self.devhierdict[devs][subsys][subsubsys]: self.devhierdict[devs][subsys][subsubsys].remove('n/a')  
                                        self.compvalues.append(self.devhierdict[devs][subsys][subsubsys])                                         
                                        if type(comps) is list:
                                            self.subsyslist = []   
                                            self.subsysdevlist = [] 
                                            for indcomp in comps:
                                                if subsys == 'User sub-systems':                                                    
                                                    self.subsyslist.append((subsubsys))
                                                else:
                                                    self.subsyslist.append((subsys))
                                                self.subsysdevlist.append((devs))
                                            self.subsystems.append(self.subsyslist)
                                            self.devlist.append(self.subsysdevlist)
                                        else: 
                                            if subsys == 'User sub-systems':
                                                self.subsystems.append((subsubsys))
                                            else:
                                                self.subsystems.append((subsys))
                                            self.devlist.append(devs)
                            else:
                                for comps in self.devhierdict[devs][subsys]:
                                    if 'n/a' in self.devhierdict[devs][subsys]: self.devhierdict[devs][subsys].remove('n/a') 
                                    self.compvalues.append(comps) 
                                    self.subsystems.append(subsys)
                                    self.devlist.append(devs)
                    # module_logger.info("\n".join(logmsg))
                    # logmsg=[""]
                    # logmsg.append('self.self.compvalues {}'.format(self.compvalues))
                    # logmsg.append('self.self.subsystems {}'.format(self.subsystems))  
                    # logmsg.append('self.self.subsyslist {}'.format(self.subsyslist))                  
                    # logmsg.append('self.self.devlist {}'.format(self.devlist))
                    # module_logger.info("\n".join(logmsg)) 
                    """ Place components in correct hierarchy positions """
                    def check(lst, replace):
                        newlst = lst[:]
                        self.complistzip = []
                        for index, item in enumerate(lst):                            
                            if type(item) is list: 
                                lst[index] = check(lst[index], replace)
                            elif type(item) is str:                                  
                                if lst[index] == replace:
                                    if type(self.compvalues) is list:                                        
                                        for intcomp,complist in enumerate(self.compvalues): 
                                            if type(complist) is list and len(self.compvalues[intcomp]) > 1: 
                                                self.complistzip.append(zip(self.compvalues[intcomp],self.subsystems[intcomp], self.devlist[intcomp]))
                                            elif type(complist) is list and len(self.compvalues[intcomp]) == 1:
                                                self.complistzip.append([(self.compvalues[intcomp][0], self.subsystems[intcomp][0], self.devlist[intcomp][0])])
                                            else:
                                                self.complistzip.append((self.compvalues[intcomp], self.subsystems[intcomp], self.devlist[intcomp]))
                                    newlst[index] = self.complistzip                                        
                        return newlst

                    self.devfrvalues = check(self.devfrvalues,devs)

            self.substationlst = []  
            self.substationdevlist = []
            self.substationvalues = []
            self.elecassylst = []  
            self.elecassylstdevlist = []
            self.elecassyvalues = [] 
            self.foundassylst = []  
            
            if self._variables.eleclayout == 'multiplehubs':
                deviceID = 'subhub'+ '{0:03}'.format(intsubhub+1)                       
                for comps in self.arrayhierdict[deviceID]['Substation']:
                    if comps  == 'n/a': 
                        self.arrayhierdict[deviceID]['Substation'].remove('n/a')  
                    self.substationlst.append('Substation')    
                    self.substationdevlist.append(deviceID)
                self.subsyslendict['Substation'] = len(self.substationlst)
                self.substationvalues.append(zip(self.arrayhierdict[deviceID]['Substation'],self.substationlst,self.substationdevlist)) 
                for comps in self.arrayhierdict[deviceID]['Elec sub-system']:   
                    if comps  == 'n/a': 
                        self.arrayhierdict[deviceID]['Elec sub-system'].remove('n/a')  
                    self.elecassylst.append('Elec sub-system')    
                    self.elecassylstdevlist.append(deviceID)
                self.elecassyvalues.append(zip(self.arrayhierdict[deviceID]['Elec sub-system'],self.elecassylst,self.elecassylstdevlist)) 
                self.subhublevelvalues = self.substationvalues[0]+self.elecassyvalues[0]+self.devfrvalues[intsubhub]
                self.frvalues.append([self.subhublevelvalues])
                self.subsyslendict['Elec sub-system'] = len(self.elecassylst)
                self.stringfrvalues = self.devfrvalues   
                
            else: self.stringfrvalues = [x for sublist in self.devfrvalues for x in sublist] 

        self.substationlst = []  
        self.substationdevlist = []
        self.substationvalues = []
        self.exportcablelst = []
        self.exportcabledevlist = []
        self.exportcablevalues = []
        
        for comps in self.arrayhierdict['array']['Substation']:
            if comps  == 'n/a': 
                self.arrayhierdict['array']['Substation'].remove('n/a')  
            self.substationlst.append('Substation')    
            self.substationdevlist.append('array')
            
        self.subsyslendict['Substation'] = len(self.substationlst)
        self.substationvalues.append(zip(self.arrayhierdict['array']['Substation'],self.substationlst,self.substationdevlist))                 
        
        for comps in self.arrayhierdict['array']['Export cable']:
            if comps  == 'n/a': 
                self.arrayhierdict['array']['Export cable'].remove('n/a')  
            self.exportcablelst.append('Export Cable')
            self.exportcabledevlist.append('array')
            
        self.subsyslendict['Export Cable'] = len(self.exportcablelst)
        self.exportcablevalues.append(zip(self.arrayhierdict['array']['Export cable'],self.exportcablelst,self.exportcabledevlist))
        self.arraylevelvalues = self.substationvalues[0]+self.exportcablevalues[0]
        
        if self._variables.eleclayout == 'multiplehubs':
            self.frvalues2 = self.arraylevelvalues + self.frvalues
        else:
            self.frvalues2 = self.arraylevelvalues + self.devfrvalues[0] 
        # logmsg = [""]
        # logmsg.append('self.arrayfrdict  {}'.format(self.arrayfrdict))
        # module_logger.info("\n".join(logmsg))   
        def check2(lst2, replace2):
            """ Replace component names with failure rates """        
            newlst2 = lst2[:]
            for index2, item2 in enumerate(lst2):             
                # logmsg = [""]
                # logmsg.append('item2 {}'.format(item2))
                # module_logger.info("\n".join(logmsg))
                if type(item2) is list:                                                                             
                    lst2[index2] = check2(lst2[index2], replace2)
                else:
                    if lst2[index2][0] == replace2: 
                        if replace2 in ['dummy']:
#                            """ Dummy sub-systems have 'perfect' reliability """
                            newlst2[index2] = (lst2[index2][0],
                                               lst2[index2][1],
                                               lst2[index2][2],
                                               1.0 * 10.0 ** -100.0)
                        else:
#                            """ Convert database failure rates from failures/10^6 hours to failures/hours """ 
                            
                            if replace2 not in self.arrayfrdict:
                                
                                errStr = ("Component with id '{}' is missing "
                                          "from the component dictionary"
                                          ).format(replace2)
                                raise KeyError(errStr)
                            # logmsg = [""]
                            # logmsg.append('lst2[index2] {}'.format(lst2[index2]))
                            # module_logger.info("\n".join(logmsg))
                            newlst2[index2] = (lst2[index2][0],
                                               lst2[index2][1],
                                               lst2[index2][2],
                                               self.arrayfrdict[replace2]
                                                               * 10.0 ** -6.0)                                           
            return newlst2
            
        for comps in self.complist:   
            self.frvalues2 = check2(self.frvalues2,comps)
            self.frvalues3 = check2(self.frvalues2,comps) 
            # logmsg = [""]
            # logmsg.append('self.frvalues3  {}'.format(self.frvalues3))
            # module_logger.info("\n".join(logmsg))
        """ Generation of reliability function equations """
        """ Access individual lists to determine reliability at mission time  """ 
        # logmsg.append('self.devfrvalues {}'.format(self.devfrvalues))
        # module_logger.info("\n".join(logmsg)) 
        def rcompmt(lst3):
            """ Individual component reliabilities calculated """
            newlst3 = lst3[:]
            self.int = []  
            for index3, item3 in enumerate(lst3): 
                # logmsg = [""]
                # logmsg.append('item3 {}'.format(item3))
                # module_logger.info("\n".join(logmsg)) 
                rpara = []                
                if type(item3) is list:                                        
                    if any(isinstance(self.int, list) for self.int in item3): 
                        if (self._variables.eleclayout == 'multiplehubs' and type(item3[0]) is tuple):
                            if item3[0][2][0:6] == 'subhub':      
                                lst3[index3] = ('PAR', rcompmt(lst3[index3]) )
                            else:                                 
                                lst3[index3] = rcompmt(lst3[index3])
                        else:
                            lst3[index3] = rcompmt(lst3[index3]) 
                    else:                        
                        for comps in item3:     
                            comp = comps[0]
                            subsys = comps[1]
                            devs = comps[2]                            
                            frs = comps[3]                     
                            rpara.append(('SER', comp, subsys, devs, math.exp(-frs * self._variables.mtime), frs))                        
                        """ 'PAR' used to define parallel relationship. Top level is always treated as series (main hub and export cable) """
                        if item3[0][2] == 'array':
                            lst3[index3] = ('SER', rpara)  
                        else:                            
                            samesubsys = [i for i, v in enumerate(rpara) if v[2] == rpara[0][2]]
                            if len(rpara) == len(samesubsys):
                                if len(rpara) == 1:
                                    lst3[index3] = ('PAR', rpara)  
                                else:
                                    lst3[index3] = ('PAR', rpara)  
                            else:
                                lst3[index3] = rpara
                else:
                    """ 'SER' used to define series relationship """
                    lst3[index3] = ('SER', item3[0], item3[1], item3[2], math.exp(-item3[3] * self._variables.mtime), item3[3])          
                newlst3[index3] = lst3[index3]            
            return newlst3        
        self.rcompvalues = rcompmt(self.frvalues2)     
        self.rcompvalues2 = copy.deepcopy(self.rcompvalues)        
        self.rcompvalues3 = copy.deepcopy(self.rcompvalues)
        # fil = open('RAM_outputs.txt','w');
        # fil.write('%%%%%%%%%%%%%%%%%%Reliability Values%%%%%%%%%%%%%%%%%%\r\n\r\nself.rcompvalues2\r\n')
        # for i in range(0,len(self.rcompvalues2)):
        # np.savetxt(fil,np.array(self.rcompvalues2),fmt='%s',delimiter='\t')
        # logmsg = [""]
        # logmsg.append('self.rcompvalues2 {}'.format(self.rcompvalues2))
        # module_logger.info("\n".join(logmsg))   

        def rsubsysmt(lst3):
            """ Sub-system level grouping """
            newlst3 = lst3[:]
            newlst4 = []
            self.int = [] 
            self.indlst = []
            sersubass = []
            sersubass2 = [] 
            for index3, item3 in enumerate(lst3):
                if type(item3) is list:                         
                    if any(isinstance(self.int, list) for self.int in item3): 
                        lst3[index3] = rsubsysmt(lst3[index3])
                    elif (self._variables.eleclayout == 'multiplehubs' and item3[0][0] == 'PAR' and item3[0][1][0][3][0:6] == 'subhub'):
                        lst3[index3] = ('PAR', rsubsysmt(item3[0][1]))                   
                    else:                        
                        rgroup = []
                        rgroupser = defaultdict(list)
                        rgrouppara = defaultdict(list)                        
                        rgroupsing = defaultdict(list)    
                        frgroupser = defaultdict(list)
                        frgrouppara = defaultdict(list)                        
                        frgroupsing = defaultdict(list)
                        sersubass = []                
                        rsingdict = defaultdict(list)

                        """ Find parallel assemblies first """  
                        paraind = [i for i, z in enumerate(item3[0:len(item3)]) if z[0] == 'PAR']
                        for subass in paraind:                            
                            rserdict = defaultdict(list)
                            rparadict = defaultdict(list)
                            rsingdict = defaultdict(list)
                            frserdict = defaultdict(list)
                            frparadict = defaultdict(list)
                            frsingdict = defaultdict(list)
                            
                            """ Find components within the same subsystem """ 
                            if [x for x, y in Counter([x[2] for x in item3[subass][1]]).items()]:
                                for comps in item3[subass][1]: 
                                    if comps[0] == 'SER' and comps[2] == x:                                        
                                        rserdict[x].append(comps[4])  
                                        frserdict[x].append(comps[5])                                          
                                    elif comps[0] == 'PAR' and comps[2] == x:
                                        rparadict[x].append(1 - comps[4]) 
                                        frparadict[x].append(comps[5])                                         
                                    elif comps[2] == x and y == 1: 
                                        rsingdict[x] = comps[4]
                                        frsingdict[x] = comps[5]                   
                                if (x == 'M&F sub-system' and self._variables.systype in ('wavefloat', 'tidefloat')):
                                    """ k of n system """
                                    if rserdict[x]: rgroupser[x].append(np.prod(rserdict[x]))
                                    if rparadict[x]: rgrouppara[x].append(np.prod(rparadict[x])) 
                                elif (x == 'M&F sub-system' and self._variables.systype in ('wavefixed', 'tidefixed')):                                    
                                    if rserdict[x]: rgroupser[x].append(np.prod(rserdict[x]))                                        
                                    if rparadict[x]: rgrouppara[x].append(1 - np.prod(rparadict[x]))
                                elif x != 'M&F sub-system':
                                    if rserdict[x]: rgroupser[x].append(np.prod(rserdict[x]))                                        
                                    if rparadict[x]: rgrouppara[x].append(1 - np.prod(rparadict[x]))                                
                                if rsingdict[x]: rgroupsing[x].append(rsingdict[x]) 
                                if frserdict[x]: frgroupser[x].append(sum(frserdict[x]))
                                if frparadict[x]: frgrouppara[x].append(binomial(frparadict[x].values())) 
                                if frsingdict[x]: frgroupsing[x].append(frsingdict[x])
                        if any(rgrouppara): 
                            for subsys in rgrouppara:
                                rgroup.append(('SER', subsys, comps[3], 1 - np.prod(rgrouppara[subsys]), binomial(frgrouppara[subsys])))                        
                        if any(rgroupser): 
                            for subsys in rgroupser:
                                if (self._variables.eleclayout in ('singlesidedstring', 'doublesidedstring') and subsys == 'Array elec sub-system'):
                                    """ Prevent grouping of parallel link """
                                    rgroup.append(('SER', subsys, comps[3], rgroupser[subsys], frgroupser[subsys]))                                    
                                if (subsys == 'M&F sub-system' and self._variables.systype in ('wavefloat', 'tidefloat')):
                                    """ Treat mooring systems as k of n system, i.e. one line failure is permitted for Accident Limit State. All lines treated as having reliability equal to the line with the lowest reliability value"""
                                    rmngroup = [] 
                                    frmngroup = [] 
                                    n = len(rgroupser[subsys])
                                    rgroupsort = np.sort(rgroupser[subsys])
                                    frgroupsort = np.sort(frgroupser[subsys])
                                    rgroupsort = np.fliplr([rgroupsort])[0]
                                    # logmsg = [""]
                                    # logmsg.append('rgroupsersort {}'.format(rgroupsort))
                                    # logmsg.append('frgroupsort {}'.format(frgroupsort))                                    
                                    # module_logger.info("\n".join(logmsg))
                                    k = n - 1
                                    for i in range(k,n+1):                                   
                                        rmngroup.append((math.factorial(n) / (math.factorial(n-i) * math.factorial(i))) * rgroupsort[i-1] ** i * (1 - rgroupsort[i-1]) ** (n - i))
                                        frmngroup.append((i * frgroupsort[i-1]) ** -1.0)
                                    rgroup.append(('SER', subsys, comps[3], sum(rmngroup), sum(frmngroup) ** -1.0))   
                                elif (subsys == 'M&F sub-system' and self._variables.systype in ('wavefixed', 'tidefixed')):
                                    """ Foundation is k of n system where functionality of all foundations is required """
                                    rmngroup = [] 
                                    frmngroup = [] 
                                    n = len(rgroupser[subsys])
                                    k = n
                                    frmngroup = sum(frgroupser[subsys])
                                    rmngroup = np.prod(rgroupser[subsys])
                                    rgroup.append(('SER', subsys, comps[3], rmngroup,frmngroup))   
                                elif subsys in ('Pto', 'Hydrodynamic', 'Control', 'Support structure'):
                                    rgroupserpara = []
                                    """ Parallel components within user-defined sub-systems """
                                    for rparavals in rgroupser[subsys]:                                        
                                        rgroupserpara.append(1 - rparavals)
                                    rgroup.append(('SER', subsys, comps[3], 1.0 - np.prod(rgroupserpara), binomial(frgroupser[subsys])))  
                        """ Single subsystem in parallel configuration """                                                
                        if any(rsingdict): 
                            for subsys in rgroupsing:
                                rgroup.append((comps[0], subsys, comps[3], rsingdict[subsys], frsingdict[subsys]))                        
                        lst3[index3]  = rgroup 
                        
                        """ Find series assemblies """  
                        serind = [i for i, z in enumerate(item3[0:len(item3)]) if z[0] == 'SER']  
                        
                        for subass in serind: 
                            sersubass.append(item3[subass]) 
                        """ Find components within the same subsystem """ 
                        rserdict = defaultdict(list)
                        rparadict = defaultdict(list)
                        rsingdict = defaultdict(list)
                        frserdict = defaultdict(list)
                        frparadict = defaultdict(list)
                        frsingdict = defaultdict(list)
                        rgroupser = defaultdict(list)
                        rgrouppara = defaultdict(list)                        
                        rgroupsing = defaultdict(list) 
                        frgroupser = defaultdict(list)
                        frgrouppara = defaultdict(list)                        
                        frgroupsing = defaultdict(list)
                        
                        for x, y in Counter([x[2] for x in sersubass]).items():                        
                            for comps in sersubass: 
                                if comps[0] == 'SER' and comps[2] == x and y > 1: 
                                    rserdict[x].append(comps[4])     
                                    frserdict[x].append(comps[5])    
                                elif comps[0] == 'PAR' and comps[2] == x and y > 1:
                                    rparadict[x].append(1 - comps[4])
                                    frparadict[x].append(comps[5]) 
                                elif comps[2] == x and y == 1: 
                                    rsingdict[x] = comps[4]        
                                    frsingdict[x] = comps[5]                                 
                            if rserdict[x]: rgroupser[x] = np.prod(rserdict[x])
                            if rparadict[x]: rgrouppara[x]  = 1 - np.prod(rparadict[x]) 
                            if frserdict[x]: frgroupser[x] = sum(frserdict[x])
                            if frparadict[x]: frgrouppara[x].append(binomial(frparadict[x].values()))
                            if rgroupser[x]: rgroup.append(('SER', x, comps[3], rgroupser[x], frgroupser[x])) 
                            if rgrouppara[x]: rgroup.append(('SER', x, comps[3], rgrouppara[x], frgrouppara[x]))                        
                            if rsingdict[x]: rgroup.append((comps[0], x, comps[3], rsingdict[x], frsingdict[x]))

                        lst3[index3]  = rgroup  
                else:                
                    rgroup = []
                    rserdict = defaultdict(list)
                    rparadict = defaultdict(list)
                    rsingdict = defaultdict(list)
                    frserdict = defaultdict(list)
                    frparadict = defaultdict(list)
                    frsingdict = defaultdict(list)
                    rgroupser = defaultdict(list)
                    rgrouppara = defaultdict(list)                        
                    rgroupsing = defaultdict(list) 
                    frgroupser = defaultdict(list)
                    frgrouppara = defaultdict(list)                        
                    frgroupsing = defaultdict(list)
                    
                    sersubass2.append(item3) 
                    """ Find components within the same subsystem """                
                    for comps in sersubass2: 
                        for x, y in Counter([x[2] for x in sersubass2]).items():                          
                            if comps[0] == 'SER' and comps[2] == x and y > 1: 
                                rserdict[x].append(comps[4])
                                frserdict[x].append(comps[5]) 
                            elif comps[0] == 'PAR' and comps[2] == x and y > 1:
                                rparadict[x].append(1 - comps[4])
                                frparadict[x].append(comps[5])
                            elif comps[2] == x and y == 1: 
                                rsingdict[x] = comps[4] 
                                frsingdict[x] = comps[5]
                        if rserdict[x]: rgroupser[x] = np.prod(rserdict[x])
                        if rparadict[x]: rgrouppara[x]  = 1 - np.prod(rparadict[x]) 
                        if frserdict[x]: frgroupser[x] = sum(frserdict[x])
                        if frparadict[x]: frgrouppara[x].append(binomial(frparadict[x].values()))
                    if any(rserdict):
                        for subsys in rserdict:
                            if rgroupser[subsys] and len(rserdict[subsys]) == self.subsyslendict[subsys]: 
                                rgroup.append(('SER', subsys, comps[3], rgroupser[subsys], frgroupser[subsys]))   
                    if any(rparadict):
                        for subsys in rparadict:
                            if rgrouppara[subsys] and len(rparadict[subsys]) == self.subsyslendict[subsys]: 
                                rgroup.append(('SER', subsys, comps[3], rgrouppara[subsys], binomial(frgrouppara[subsys])))                            
                    if any(rsingdict):                 
                        for subsys in rsingdict: 
                            if (subsys == lst3[index3][2] and self.subsyslendict[subsys] == 1): 
                                rgroup.append((comps[0], subsys, comps[3], rsingdict[subsys], frsingdict[subsys]))
                    lst3[index3]  = rgroup 
                newlst3[index3] = lst3[index3]
            newlst4 = filter(None, newlst3)
            return newlst4    
        self.rsubsysvalues = rsubsysmt(self.rcompvalues)
        self.rsubsysvalues2 = copy.deepcopy(self.rsubsysvalues)
        self.rsubsysvalues3 = copy.deepcopy(self.rsubsysvalues)
        # fil.write('self.rsubsysvalues3\r\n')
        # np.savetxt(fil,self.rsubsysvalues3,fmt='%s',delimiter='\t')
        # logmsg = [""]
        # logmsg.append('self.rsubsysvalues3 {}'.format(self.rsubsysvalues2))
        # module_logger.info("\n".join(logmsg))
        
        def rdevmt(lst3):
            """ Device level grouping. Only mooring and user-defined subsystems are grouped """
            newlst3 = lst3[:]
            self.int = []    
            relec = []
            for index3, item3 in enumerate(lst3):
                rpara = []   
                rser = [] 
                frser = []
                frpara = []
                rgroup = []
                if type(item3) is list:  
                    if any(isinstance(self.int, list) for self.int in item3):                       
                        lst3[index3] = rdevmt(lst3[index3]) 
                    else:                         
                        for subsys in item3:                       
                            if subsys[0] == 'SER' and subsys[1] in ('M&F sub-system', 
                                                                    'Pto', 
                                                                    'Hydrodynamic', 
                                                                    'Control', 
                                                                    'Support structure',
                                                                    'Dummy sub-system'): 
                                rser.append((subsys[3]))                                
                                frser.append(subsys[4]) 
                            if subsys[0] == 'PAR' and subsys[1] in ('M&F sub-system', 
                                                                    'Pto', 
                                                                    'Hydrodynamic', 
                                                                    'Control', 
                                                                    'Support structure',
                                                                    'Dummy sub-system'):                                
                                rpara.append((1 - subsys[3])) 
                                frpara.append(subsys[4])
                            if subsys[1] == 'Array elec sub-system':
                                relec = (subsys[0], subsys[1], subsys[2], subsys[3], subsys[4])
                        if rpara: rgroup.append(('PAR', subsys[2], 1 - np.prod(rpara), binomial(frpara), relec))
                        if rser: rgroup.append(('SER', subsys[2], np.prod(rser), sum(frser),relec))
                        if item3[0][1] in ('Substation', 'Export Cable'):                            
                            lst3[index3] = item3[0]                      
                        elif (self._variables.eleclayout == 'multiplehubs' and item3[0][1] == 'Elec sub-system'):                     
                            lst3[index3] = item3[0] 
                        else:
                            lst3[index3] = rgroup[0]
                elif (self._variables.eleclayout == 'multiplehubs' and item3[0] == 'PAR'):
                    lst3[index3] = ('PAR', rdevmt(item3[1]))
                newlst3[index3] = lst3[index3]

            return newlst3
        self.rdevvalues = rdevmt(self.rsubsysvalues)
        self.rdevvalues2 = copy.deepcopy(self.rdevvalues)
        # fil.write('\r\n\r\nself.rdevvalues2\r\n')
        # np.savetxt(fil,self.rdevvalues2,fmt='%s',delimiter='\t')
        # logmsg = [""]
        # logmsg.append('self.rdevvalues2 {}'.format(self.rdevvalues2))
        # module_logger.info("\n".join(logmsg))
        if not self._variables.eleclayout:
            """ Skip stringdev, string and subhub methods if an electrical network hasn't been specified """
            pass
        else:        
            def rstringdevmt(lst3):
                """ String-device level grouping """
                newlst3 = lst3[:]
                self.int = []    
                rdev = []
                
                for index3, item3 in enumerate(lst3):
                    frdev =[]
                    rgroup = []                
                    rstringgroup = []
                    relec = [] 
                    frelec = []
                    relecgrouplhs = []
                    relecmerged = []
                    frelecmerged = []
                    if self._variables.eleclayout in ('radial', 'singlesidedstring', 'doublesidedstring'): 
                        if type(item3) is list:                     
                            if any(isinstance(self.int, list) for self.int in item3):
                                lst3[index3] = rstringdevmt(lst3[index3])  
                            else:                         
                                for subsys in item3:
                                    if (subsys[4] and  
                                        subsys[4][1] == 'Array elec sub-system'):  
                                        relec.append(subsys[4][3]) 
                                        frelec.append(subsys[4][4])                                 
                                if self._variables.eleclayout in ('singlesidedstring', 'doublesidedstring'): 
                                    """ Flatten lists """
                                    for relecval in relec:
                                        if type(relecval) is list:
                                            for relecvals in relecval:
                                                relecmerged.append(relecvals)
                                        else:
                                            relecmerged.append(relecval)
                                    for frelecval in frelec:
                                        if type(frelecval) is list:
                                            for frelecvals in frelecval:
                                                frelecmerged.append(frelecvals)
                                        else:
                                            frelecmerged.append(frelecval)  
                                for index4, subsys in enumerate(item3):
                                    rdev = subsys[0:3]
                                    frdev = subsys[3] 
                                    relecgroup = []
                                    frelecgroup = []
                                    if self._variables.eleclayout  == 'radial':
                                        relecgroup = np.prod(relec[index4-len(relec):])                            
                                        frelecgroup = sum(frelec[index4-len(frelec):])
                                    elif self._variables.eleclayout in ('singlesidedstring', 'doublesidedstring'):  
                                        relecgrouplhs = np.prod(relecmerged[0:index4+1])
                                        frelecgrouplhs = sum(frelecmerged[0:index4+1])                                     
                                        relecgrouprhs = relecmerged[index4+1:]
                                        relecgrouprhs = np.prod(relecgrouprhs) 
                                        frelecgrouprhs = frelecmerged[index4+1:]
                                        frelecgrouprhs = sum(frelecgrouprhs)

                                        """ Compare reliabilities on left hand side and right hand side of network """
                                        relecgroup = max(np.prod(relecgrouplhs), np.prod(relecgrouprhs))
                                        frelecgroup = min(frelecgrouplhs, frelecgrouprhs)
                                    rgroup.append(('SER',rdev[1],np.prod([rdev[2],relecgroup]), sum([frdev,frelecgroup])))                            
                                lst3[index3] = ('PAR',rgroup)
                             
                    elif self._variables.eleclayout == 'multiplehubs': 
                        if item3[0] == 'PAR':
                            if type(item3[1]) is list:
                                for string in item3[1]:
                                    relec = [] 
                                    frelec = []
                                    if type(string) is list:
                                        for subsys in string:
                                            if subsys[4][1] == 'Array elec sub-system':  
                                                relec.append(subsys[4][3]) 
                                                frelec.append(subsys[4][4]) 
                                for string in item3[1]:    
                                    rgroup = [] 
                                    if type(string) is list:
                                        for index4, dev in enumerate(string):
                                            rdev = dev[0:3]
                                            frdev = dev[3] 
                                            relecgroup = []
                                            frelecgroup = []
                                            relecgroup = np.prod(relec[index4-len(relec):])                            
                                            frelecgroup = sum(frelec[index4-len(frelec):])
                                            rgroup.append(('SER',rdev[1],np.prod([rdev[2],relecgroup]), sum([frdev,frelecgroup])))
                                        rstringgroup.append(('PAR', rgroup))
                                    else:
                                        rstringgroup.append(('SER', string[1], string[2], string[3], string[4]))
                                if rstringgroup:
                                    lst3[index3] = [('PAR',rstringgroup)]
                                
                    newlst3[index3] = lst3[index3]  
                return newlst3
            self.rstringdevvalues = rstringdevmt(self.rdevvalues)        
            self.rstringdevvalues2 = copy.deepcopy(self.rstringdevvalues)
            # fil.write('\r\n\r\nself.rstringdevvalues\r\n')
            # np.savetxt(fil,self.rstringdevvalues,fmt='%s',delimiter='\t')
            # logmsg = [""]
            # logmsg.append('self.rstringdevvalues {}'.format(self.rstringdevvalues))
            # module_logger.info("\n".join(logmsg))
            def rstringmt(lst3):
                """ String level grouping """
                newlst3 = lst3[:]            
                self.int = []  
                for index3, item3 in enumerate(lst3):   
                    rgroup = []
                    rpara = []   
                    rser = []
                    rgrouppara = []
                    rgroupser = []
                    frgrouppara = []
                    rstringgroup = []
                    frser = []
                    frpara = []
                    if self._variables.eleclayout in ('radial', 'singlesidedstring', 'doublesidedstring'):
                        
                        if type(item3) is list: 
                            if any(isinstance(self.int, list) for self.int in item3):                       
                                lst3[index3] = rstringmt(lst3[index3])  
                            lst3[index3] = ('SER', rgroup)                        
                        else: 
                            if item3[0] == 'PAR': 
                                
                                for devs in item3[1]:  
                                    
                                    if devs[0] == 'SER':
                                        stringind = [x for x in self.stringlist if devs[1] in x]  
                                        rpara.append(devs[2])
                                        frpara.append(devs[3])  
                                rstringgroup = ('PAR', 'String ' + str(stringind[0][0]), np.prod(rpara), sum(frpara)) 
                                rgroup.append(rstringgroup)
                                lst3[index3] = ('PAR', rgroup)
                            else:
                                rgroup.append(('SER', item3[1], item3[2], item3[3], item3[4]))
                                lst3[index3] = rgroup[0]
                    elif self._variables.eleclayout == 'multiplehubs':
                        if item3[0][0] == 'PAR':                         
                            if type(item3[0][1]) is list: 
                                for subhub in item3[0][1]:
                                    if subhub[0] == 'PAR':
                                        rpara = []
                                        frpara = []
                                        for devs in subhub[1]:
                                            rgrouppara = []
                                            if devs[0] == 'SER':
                                                stringind = [x for x in self.stringlist if devs[1] in x]  
                                                rpara.append(devs[2])
                                                frpara.append(devs[3]) 
                                                subhubind = [x for x in self.subhubdevlist if devs[1] in x] 
                                            rgrouppara = np.prod(rpara)
                                            frgrouppara = sum(frpara)   
                                        rstringgroup.append(['String ' + str(stringind[0][0]), 'subhub'+ '{0:03}'.format(subhubind[0][0]+1), rgrouppara, frgrouppara])
                                       
                                    else:
                                        rgroup.append(subhub)                                   
                                rgroup.append(('PAR', rstringgroup))
                                lst3[index3] = ('PAR', rgroup)
                            else:
                                lst3[index3] = item3
                    newlst3[index3] = lst3[index3] 
                return newlst3
            self.rstringvalues = rstringmt(self.rstringdevvalues) 
            self.rstringvalues2 = copy.deepcopy(self.rstringvalues)
            # fil.write('\r\n\r\nself.rstringvalues2\r\n')
            # np.savetxt(fil,self.rstringvalues2,fmt='%s',delimiter='\t')
            # logmsg = [""]
            # logmsg.append('self.rstringvalues2 {}'.format(self.rstringvalues2))
            # module_logger.info("\n".join(logmsg))
                  
            def rsubhubmt(lst3):
                """ Subhub level grouping (only used when multiple hubs exist) """
                if self._variables.eleclayout in ('radial', 'singlesidedstring', 'doublesidedstring'):
                    pass
                else:
                    newlst3 = lst3[:] 
                    self.int = []
                    rgroup = []
                    rser = []
                    frser = []
                    
                    rgroup = [] 
                    for index3, item3 in enumerate(lst3):
                        rsubhub = [] 
                        rpara = []
                        frpara = []
                        rgroupser = []
                        rgrouppara = []  
                        if item3[0] == 'PAR': 
                            for strings in item3[1]:
                                if strings[0] == 'SER':
                                    rgroupser.append(strings)
                                    subhublabel = strings[2] + ' strings'
                                elif strings[0] == 'PAR':
                                    for string in strings[1]: 
                                        rpara.append(1 - string[2])
                                        frpara.append(string[3])
                            if rgroupser:
                                for subhub in rgroupser:
                                    rsubhub.append(subhub)
                            if rpara:
                                rgrouppara = 1 - np.prod(rpara)
                                frgrouppara = binomial(frpara)
                                rsubhub.append(('SER', subhublabel, rgrouppara,frgrouppara))
                            """ Subhubs are assumed to be connected in parallel with 
                            the main hub """  
                            rgroup.append(('PAR',rsubhub))
                            
                                 
                        elif item3[0] == 'SER':
                            rgroup.append(item3)
                    return rgroup
                    # fil.write('\r\n\r\nself.rsubhubvalues2\r\n')
                    # np.savetxt(fil,self.rsubhubvalues2,fmt='%s',delimiter='\t')
            self.rsubhubvalues = rsubhubmt(self.rstringvalues)
            self.rsubhubvalues2 = copy.deepcopy(self.rsubhubvalues)
            # logmsg = [""]
            # logmsg.append('self.rsubhubvalues2  {}'.format(self.rsubhubvalues2))
            # module_logger.info("\n".join(logmsg))
            
        def rarraymt(lst3):
            """ Array level grouping """
            """ Strings and subhubs assumed to be parallel """ 
            self.int = []
            rgroup = []
            
            rgroupparacomb = []
            rsubhubser = []
            frsubhubser = []
            rarray = [] 
            rarrayser = []
            frarrayser = []
            for index3, item3 in enumerate(lst3):
                rgrouppara = []
                frser = []
                rser = []
                rpara = []
                frpara = []
                rparaser = []
                frparaser = []
                if self._variables.eleclayout in ('radial', 'singlesidedstring', 'doublesidedstring'):
                    if item3[0] == 'PAR': 
                        
                        for devs in item3[1]:  
                            if devs[0] == 'PAR':
                                rpara.append(1 - devs[2])
                                frpara.append(devs[3])  
                            elif devs[0] == 'SER':
                                rparaser.append(devs[2])
                                frparaser.append(devs[3])
                    if item3[0] == 'SER':
                        rser.append(item3[3])
                        frser.append(item3[4])     
                    if rpara:                
                        rgrouppara = 1.0 - np.prod(rpara)
                        frgrouppara = binomial(frpara)
                        rgroupparacomb.append((rgrouppara,frgrouppara))                        
                    if rparaser:                        
                        rgroupparaser = np.prod(rparaser)
                        frgroupparaser = sum(frparaser)
                        rgroupparacomb.append((rgroupparaser,frgroupparaser))
                    if rser:
                        rgroupser = np.prod(rser)
                        frgroupser = sum(frser)
                        rgroup.append((rgroupser,frgroupser))
                elif self._variables.eleclayout == 'multiplehubs':
                    if item3[0] == 'PAR':
                        for subhubs in item3[1]:
                            if subhubs[1][0:6] == 'subhub':
                                rser.append(subhubs[2])
                                frser.append(subhubs[3]) 
                            else:
                                rser.append(subhubs[3])
                                frser.append(subhubs[4])        
                    elif item3[0] == 'SER':
                        rarrayser.append(item3[3])
                        frarrayser.append(item3[4])
                    if rser:    
                        rsubhubser.append(1 - np.prod(rser))
                        frsubhubser.append(sum(frser))

            if rgroupparacomb:  
                rstringcomb = []
                frstringcomb = []

                for strings in rgroupparacomb:
                    rstringcomb.append(1 - strings[0])
                    frstringcomb.append(strings[1])  
                # frstringcomb = np.reciprocal(frstringcomb)
                
                # rgroup.append((1 - np.prod(rstringcomb), np.reciprocal(binomial(frstringcomb))))            
                rgroup.append((1 - np.prod(rstringcomb), binomial(frstringcomb)))

            if self._variables.eleclayout in ('radial', 'singlesidedstring', 'doublesidedstring'):
                rarraycomb = []
                frarraycomb = []
                for arrayelem in rgroup:
                    rarraycomb.append(arrayelem[0])
                    frarraycomb.append(arrayelem[1])
                rarray = (np.prod(rarraycomb), sum(frarraycomb))                
            elif self._variables.eleclayout == 'multiplehubs':
                """ Subhubs are assumed to be connected in parallel with 
                the main hub """
                rarrayser = (1-np.prod(rsubhubser)) * np.prod(rarrayser)
                frarrayser = binomial(frsubhubser) + sum(frarrayser)
                rarray = [rarrayser, frarrayser] 
            return ('array', rarray[0], rarray[1]) 
            
        if self._variables.eleclayout:
            if self._variables.eleclayout in ('radial', 'singlesidedstring', 'doublesidedstring'):
                self.rarrayvalue = rarraymt(self.rstringvalues)          
            elif self._variables.eleclayout == 'multiplehubs':
                self.rarrayvalue = rarraymt(self.rsubhubvalues)
        else:
            self.rarrayvalue = copy.deepcopy(self.rdevvalues)
        self.rarrayvalue2 = copy.deepcopy(self.rarrayvalue)
        # fil.write('\r\n\r\nself.rarrayvalue2\r\n')
        # np.savetxt(fil,self.rarrayvalue2,fmt='%s',delimiter='\t')
        # fil.close()
        # logmsg = [""]
        # logmsg.append('self.rarrayvalue2  {}'.format(self.rarrayvalue2))
        # module_logger.info("\n".join(logmsg))
    """ Calculation of component TTFs and system MTTF """    
    def ttf(self):
        def ttfcompmttf(lst3):
            """ Component level TTFs """
            newlst3 = lst3[:]
            self.int = [] 
            for index3, item3 in enumerate(lst3):  
                ttfcomp = []   
                if type(item3) is list:
                    if (self._variables.eleclayout == 'multiplehubs' and item3[0][0] == 'PAR' and item3[0][1][0][3][0:6] == 'subhub'):
                        lst3[index3] = ttfcompmttf(lst3[index3][0][1])                                        
                    elif (any(isinstance(self.int, list) for self.int in item3)): 
                        lst3[index3] = ttfcompmttf(lst3[index3])                        
                    else:
                        if isinstance(item3, list):                             
                            for comps in item3:
                                if comps[0] == 'PAR':
                                    for subcomps in comps[1]:

                                        frs = subcomps[5]
                                        ttfcomp.append((subcomps[0], subcomps[1], subcomps[2], subcomps[3], frs ** -1.0)) 
                                else: 
                                    frs = comps[5]   
                                    ttfcomp.append((comps[0], comps[1], comps[2], comps[3], frs ** -1.0)) 
                            lst3[index3] = ttfcomp       
                else:
                    lst3[index3] = (item3[0], item3[1], item3[2], item3[3], item3[5] ** -1.0)
                newlst3[index3] = lst3[index3]  
            return newlst3 
        self.mttfcompvalues = ttfcompmttf(self.rcompvalues2) 
        # fil = open('RAM_outputs.txt','a')
        # fil.write('\r\n\r\n%%%%%%%%%%%%%%%MTTF Values%%%%%%%%%%%%%%%%%\r\n\r\nself.mttfcompvalues\r\n')
        # np.savetxt(fil,self.mttfcompvalues,fmt='%s',delimiter='\t')
        # logmsg = [""]
        # logmsg.append(' self.mttfcompvalues  {}'.format( self.mttfcompvalues))
        # module_logger.info("\n".join(logmsg))  

#        
        def subsysmttf(lst3):
            """ Subsystem level MTTF calculation based on PAR/SER hierarchy """
            newlst3 = lst3[:]
            self.int = []          
            for index3, item3 in enumerate(lst3):
                ttfsubsys = []
                if type(item3) is list:  
                    if any(isinstance(self.int, list) for self.int in item3):                       
                        lst3[index3] = subsysmttf(lst3[index3])  
                    else:   
                        if isinstance(item3, list):                             
                            for subsys in item3:
                                if subsys[0] == 'PAR':
                                    for subsubsys in subsys[1]:
                                        frs = subsubsys[4]
                                        ttfsubsys.append((subsubsys[0], subsubsys[1], subsubsys[2], frs ** -1.0)) 
                                else:
                                    if (self._variables.eleclayout in ('singlesidedstring', 'doublesidedstring') and type(subsys[4]) is list):
                                        frs = self.binomial(subsys[4])
                                        ttfsubsys.append((subsys[0], subsys[1], subsys[2], frs ** -1.0)) 
                                    else:
                                        frs = subsys[4]                                       
                                        ttfsubsys.append((subsys[0], subsys[1], subsys[2], frs ** -1.0)) 
                            lst3[index3] = ttfsubsys 
                elif (self._variables.eleclayout == 'multiplehubs' and item3[0] == 'PAR' and item3[1][0][0][2][0:6] == 'subhub'):
                    lst3[index3] = subsysmttf(lst3[index3][1])  
                else:                    
                    lst3[index3] = (item3[0], item3[1], item3[2], item3[4] ** -1.0)
                newlst3[index3] = lst3[index3] 
            return newlst3    
        self.mttfsubsys = subsysmttf(self.rsubsysvalues2)
        # fil.write('\r\n\r\nself.mttfsubsys\r\n')
        # np.savetxt(fil,self.mttfsubsys,fmt='%s',delimiter='\t')
        # logmsg = [""]
        # logmsg.append(' self.mttfsubsys  {}'.format( self.mttfsubsys))
        # module_logger.info("\n".join(logmsg))  
        def devmttf(lst3):
            """ Device level MTTF calculation """
            newlst3 = lst3[:]
            self.int = []          
            for index3, item3 in enumerate(lst3):
                ttfdev = []
                if self._variables.eleclayout in ('radial', 'singlesidedstring', 'doublesidedstring'):
                    if type(item3) is list: 
                        if any(isinstance(self.int, list) for self.int in item3):                       
                            lst3[index3] = devmttf(lst3[index3])  
                        else:   
                            if isinstance(item3, list):                             
                                for dev in item3:
                                    if dev[0] == 'PAR':
                                        for subdev in dev[1]:
                                            frs = subdev[4]
                                            ttfdev.append((subdev[0], subdev[1], frs ** -1.0)) 
                                    elif isinstance(dev[4], tuple):
                                        if (self._variables.eleclayout in ('singlesidedstring', 'doublesidedstring') and type(dev[4][4]) is list):
                                            frs = binomial(dev[4][4])
                                            ttfdev.append((dev[0], dev[1], dev[3] ** -1.0, (dev[4][0], dev[4][1], dev[4][2], frs ** -1.0))) 
                                        else:
                                            frs = dev[4][4]
                                            ttfdev.append((dev[0], dev[1], dev[3] ** -1.0, (dev[4][0], dev[4][1], dev[4][2], frs ** -1.0))) 
                                lst3[index3] = ttfdev                             
                    else:
                        lst3[index3] = (item3[0], item3[1], item3[2], item3[4] ** -1.0)
                
                elif self._variables.eleclayout == 'multiplehubs':                    
                    if item3[0] == 'PAR':
                        for dev in item3[1]:
                            stringgroup = []
                            if type(dev) is not list:   
                                ttfdev.append((dev[0], dev[1], dev[2], dev[3], dev[4])) 
                            else:
                                for stringdev in dev:
                                    if isinstance(stringdev[4], tuple):
                                        frs = stringdev[4][4]                                    
                                        stringgroup.append((stringdev[0], stringdev[1], stringdev[3] ** -1.0, (stringdev[4][0], stringdev[4][1], stringdev[4][2], frs ** -1.0))) 
                                ttfdev.append(stringgroup)
                            lst3[index3] = ttfdev 
                    else:
                        lst3[index3] = (item3[0], item3[1], item3[2], item3[4])
                newlst3[index3] = lst3[index3] 
            return newlst3  
        self.mttfdev = devmttf(self.rdevvalues2) 
        # fil.write('\r\n\r\nself.mttfdev\r\n')
        # np.savetxt(fil,self.mttfdev,fmt='%s',delimiter='\t')
        # logmsg = [""]
        # logmsg.append(' self.mttfdev  {}'.format( self.mttfdev))
        # module_logger.info("\n".join(logmsg)) 
        if not self._variables.eleclayout:
            """ Skip stringdev, string and subhub methods if an electrical network hasn't been specified """
            pass
        else:
            def stringdevmttf(lst3):
                """ String level MTTF calculation """
                newlst3 = lst3[:]
                self.int = []          
                for index3, item3 in enumerate(lst3):
                    ttfstring = []    
                    if self._variables.eleclayout in ('radial', 'singlesidedstring', 'doublesidedstring'):
                        if item3[0] == 'PAR':                    
                            for string in item3[1]:                        
                                frs = string[3]
                                ttfstring.append((string[0], string[1], frs ** -1.0))                        
                            lst3[index3] = ttfstring
                        else:
                            frs = item3[4]   
                            ttfstring.append((item3[0], item3[1], item3[2], frs ** -1.0)) 
                            lst3[index3] = ttfstring
                        newlst3[index3] = lst3[index3] 
                        
                    elif self._variables.eleclayout == 'multiplehubs':
                        if item3[0][0] == 'PAR':                    
                            for string in item3[0][1]:
                                stringgroup = []
                                if string[0] == 'SER':
                                    ttfstring.append((string[0], string[1], string[2], string[3], string[4]))                             
                                elif string[0] == 'PAR':
                                    for devs in string[1]:
                                        frs = devs[3]
                                        stringgroup.append((devs[0], devs[1], frs ** -1.0))                        
                                    ttfstring.append(stringgroup)
                            lst3[index3] = ttfstring
                        newlst3[index3] = lst3[index3] 
                return newlst3    
            self.mttfstringdev = stringdevmttf(self.rstringdevvalues2)
            # fil.write('\r\n\r\nself.mttfstringdev\r\n')
            # np.savetxt(fil,self.mttfstringdev,fmt='%s',delimiter='\t')
            # logmsg = [""]
            # logmsg.append(' self.mttfstringdev  {}'.format( self.mttfstringdev))
            # module_logger.info("\n".join(logmsg))       
            def stringmttf(lst3):
                """ Array level MTTF calculation """
                newlst3 = lst3[:]
                self.int = []          
                for index3, item3 in enumerate(lst3):  
                    ttfstrings = []
                    if self._variables.eleclayout in ('radial', 'singlesidedstring', 'doublesidedstring'):
                        if (item3[0] == 'SER' and item3[2] == 'array'):
                            frs = item3[4]
                            ttfstrings.append((item3[0], item3[1], frs ** -1.0)) 
                        elif item3[0] == 'PAR':
                            frs = item3[1][0][3]   
                            ttfstrings.append((item3[1][0][0], item3[1][0][1], frs ** -1.0))
                    elif self._variables.eleclayout == 'multiplehubs':
                        if (item3[0] == 'SER' and item3[2] == 'array'):
                            frs = item3[4]
                            ttfstrings.append((item3[0], item3[1], frs)) 
                        elif item3[0] == 'PAR':
                            for string in item3[1]:
                                if string[0] == 'PAR':
                                    for strings in string[1]:
                                        frs = strings[3]
                                        ttfstrings.append([(strings[0], strings[1], frs ** -1.0)]) 
                                elif string[0] == 'SER':
                                    frs = string[4]
                                    ttfstrings.append((string[0], string[1], string[2], frs)) 
                    lst3[index3] = ttfstrings
                    newlst3[index3] = lst3[index3]        
                return newlst3             
            self.mttfstring = stringmttf(self.rstringvalues2)
            # fil.write('\r\n\r\nself.mttfstring\r\n')
            # np.savetxt(fil,self.mttfstring,fmt='%s',delimiter='\t')            
            # logmsg = [""]
            # logmsg.append(' self.mttfstring {}'.format( self.mttfstring))
            # module_logger.info("\n".join(logmsg))       
            def subhubmttf(lst3):
                """ Subhub level grouping (only used when multiple hubs exist) """
                if self._variables.eleclayout in ('radial', 'singlesidedstring', 'doublesidedstring'):
                    pass
                elif self._variables.eleclayout == 'multiplehubs':
                    ttfarray = []
                    for index3, item3 in enumerate(lst3):
                        ttfsubhubs = []
                        if (item3[0] == 'SER' and item3[2] == 'array'):
                            frs = item3[4]
                            ttfarray.append((item3[0], item3[1], frs)) 
                        elif item3[0] == 'PAR':
                            for subhubs in item3[1]:
                                if subhubs[1] in ('Substation', 'Elec sub-system'):
                                    frs = subhubs[4]                                
                                else:
                                    frs = subhubs[3]
                                ttfsubhubs.append((subhubs[0], subhubs[1], subhubs[2], frs ** -1.0))
                            if ttfsubhubs:
                                ttfarray.append(('PAR',ttfsubhubs))                           
                    return ttfarray
                    # fil.write('\r\n\r\nself.mttfsubhub\r\n')
                    # np.savetxt(fil,self.mttfsubhub[i],fmt='%s',delimiter='\t')     
            self.mttfsubhub = subhubmttf(self.rsubhubvalues2)
            
            # logmsg = [""]
            # logmsg.append(' self.mttfsubhub {}'.format( self.mttfsubhub))
            # module_logger.info("\n".join(logmsg))       
        def arraymttf(lst3):            
            """ Top level MTTF calculation """
            mttfarray = []
            if self._variables.eleclayout:
                mttfarray = ('array', self.rarrayvalue2[2] ** -1)
            else:
                mttfarray = ('array', 'n/a')
            return mttfarray
        
        """ System MTTF in hours """
        self.mttfarray = arraymttf(self.rarrayvalue2)
        # fil.write('\r\n\r\nself.mttfarray\r\n')
        # np.savetxt(fil,self.mttfarray,fmt='%s',delimiter='\t')
        # fil.close()        
        # logmsg = [""]
        # logmsg.append(' self.mttfarray {}'.format( self.mttfarray))
        # module_logger.info("\n".join(logmsg))
        if self._variables.mttfreq is not None:
        
            logmsg = [""]
            logmsg.append('***************MTTF pass/fail******')
            
            failMsg = "Fail: calculated MTTF less than required value!"
            passMsg = "Pass: calculated MTTF greater than required value"
            
            if self._variables.mttfreq > self.mttfarray[1]:
                logmsg.append(failMsg)
            else:
                logmsg.append(passMsg)
                
            module_logger.info("\n".join(logmsg))

    def rpn(self):
        """ RPN calculation. Frequency definitions can be found in
        Deliverable 7.2
        """
        
        complist = self.compfrvalueslist[:]
        
        probf = [0 for rows in range(0, len(complist))]
        freq = [0 for rows in range(0, len(complist))]
        rpn = [0 for rows in range(0, len(complist))]
        mc = [0 for rows in range(0, len(complist))]
        
        for compind, comps in enumerate(complist):
            
            # Convert failures/10^6 hours to % failures/year
            year_hours = 365.25 * 24.0
            probf[compind] = 100.0 * (1.0 - math.exp(-comps[1] *
                                                  year_hours * 10.0 ** -6.0))
                
            if probf[compind] < 0.01:
                freq[compind] = 0.0
            elif probf[compind] >= 0.01 and probf[compind] < 0.1:
                freq[compind] = 1.0
            elif probf[compind] >= 0.1 and probf[compind] < 1.0:
                freq[compind] = 2.0
            elif probf[compind] >= 1.0 and probf[compind] < 10.0:
                freq[compind] = 3.0
            elif probf[compind] >= 10.0 and probf[compind] < 50.0:
                freq[compind] = 4.0
            elif probf[compind] >= 50.0:
                freq[compind] = 5.0
            
            if self.severitylevel == 'critical':
                rpn[compind] = 2.0 * freq[compind]
            elif self.severitylevel == 'non-critical':
                rpn[compind] = 1.0 * freq[compind]
            if rpn[compind] <= 2.0:
                mc[compind] = 'green'
            elif rpn[compind] > 2.0 and rpn[compind] < 5.0:
                mc[compind] = 'yellow'
            elif rpn[compind] >= 5.0 and rpn[compind] <= 7.0:
                mc[compind] = 'orange'
            elif rpn[compind] > 7.0:
                mc[compind] = 'red'
                
        rpnvalues = zip(*[probf, rpn])
        
        # Filter out dummy values
        self.complist = [x for x in self.complist if x != 'dummy']
        rpnvalues = [x for x, y in zip(rpnvalues, self.complist)
                                                        if y != 'dummy']
        
        self.rpncomptab = pd.DataFrame(rpnvalues,
                                       index=self.complist,
                                       columns=['Probability of failure %',
                                                'Risk Priority Number'])
        
        return


def binomial(frpara):
    """ Method from Elsayed, 2012 """
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
    frparacalc = np.reciprocal(frparacalc)
    return frparacalc   

