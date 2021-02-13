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
import copy
import math
import logging
import itertools
from collections import Counter, OrderedDict, defaultdict

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
        self.mttfpass = None
        
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
        
        for deviceID in self._variables.elechierdict:
            
            if (deviceID == 'array' or deviceID[0:6] == 'subhub'):
#                """ self._variables.elechierdict is used to define the top level array architecture """
                
                # Break down parallel definitions into serial
                check_dict = self._variables.elechierdict[deviceID]
                
                self.arrayhierdict[deviceID] = check_dict
                
                if ('Substation foundation' not in
                    self._variables.moorfoundhierdict[deviceID]): continue
                
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
    
    def arrayfrdictasgn(self, severitylevel, calcscenario, fullset):
        """ Read in relevant failure rate data from the mooring and electrical bill of materials """
        self.arrayfrdict = {}   
        self.devicecompscandict = {}
        self.complist = []
        
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
                                
        for deviceID, deveelecbom in self._variables.elecbomdict.iteritems():
            
            if (deviceID == 'array' or deviceID[0:6] == 'subhub'):
                
                for subsys, subelecbom in deveelecbom.iteritems():
                    
                    for comps in subelecbom['quantity']:
                        self.complist.append(comps)
                
            else:
                
                for comps in deveelecbom['quantity']:
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
        
        if not fullset: self.complist.append('dummy')
        
        # Will only remove one if this is desired
        if 'n/a' in self.complist: self.complist.remove('n/a')
        
        # Remove "not required"
        self.complist = [comp for comp in self.complist
                                         if "not required" not in str(comp)]
        
        self.arrayfrdict = get_arrayfrdict (self._variables.dbdict,
                                            self.complist,
                                            severitylevel,
                                            calcscenario)
        
        # logmsg = [""]
        # logmsg.append('self.arrayfrdict {}'.format(self.arrayfrdict))
        # module_logger.info("\n".join(logmsg)) 
    
    def arrayfrvalues(self): 
        """ Generate list of relevant failure rates in the correct heirarchy
        positions """
        
        frvalues = []  
        devfrvalues = []
        frvalues2 = []
        stringlist = []
        subhubdevlist = []
        subsyslendict = {}
        nestdevs = []
        
        if self._variables.eleclayout == 'multiplehubs':
            """ Construct nested list for all devices and subhubs """
            subhubnum = len(self.arrayhierdict['array']['layout'])
            for intsubhub, subhub in enumerate(self.arrayhierdict['array']['layout']):
                nestdevs.append(self.arrayhierdict['subhub'+ '{0:03}'.format(intsubhub+1)]['layout'])
            devfrvalues = copy.deepcopy(nestdevs)
        else:   
            # logmsg = [""]
            # logmsg.append('self.arrayhierdict {}'.format(self.arrayhierdict))
            devfrvalues.append(copy.deepcopy(self.arrayhierdict['array']['layout']))
            # logmsg.append('devfrvalues {}'.format(devfrvalues))
            # logmsg.append('self.devhierdict {}'.format(self.devhierdict))
            # module_logger.info("\n".join(logmsg)) 
        # logmsg = [""]
        
        
        import pprint
        pprint.pprint( self.devhierdict )
        pprint.pprint( self.arrayhierdict )

        
        for intsubhub, subhubstrings in enumerate(devfrvalues):
            
            for intstring, strings in enumerate(subhubstrings):
                
                for dev in strings:
                    
                    stringlist.append((intstring, dev))
                    subhubdevlist.append((intsubhub,dev))
                    
                    compvalues = []
                    subsystems = [] 
                    subsystems = [] 
                    
                    for subsys in self.devhierdict[dev]:
                        
                        if subsys not in ('M&F sub-system',
                                          'User sub-systems',
                                          'Array elec sub-system'): continue
                        
                        devsubsys = self.devhierdict[dev][subsys]
                    
                        if type(devsubsys) is dict:
                            
                            for subsubsys in devsubsys:
                                
                                syscomps = devsubsys[subsubsys]
                                
                                if type(syscomps) is list:
                                    
                                    for comps in syscomps:
                                        
                                        if comps in ['n/a', ['n/a']]: 
                                            continue
                                        
                                        compvalues.append(comps)
                                        
                                        if type(comps) is list:
                                            
                                            subsyslist = []   
                                            subsysdevlist = []
                                            
                                            for indcomp in comps:
                                                
                                                if indcomp == 'n/a':
                                                    pass
                                                else:
                                                    if subsys == 'User sub-systems':
                                                        subsyslist.append((subsubsys))
                                                    else:
                                                        
                                                        subsyslist.append((subsys))
                                                    
                                                    subsysdevlist.append((dev))
                                                    
                                            subsystems.append(subsyslist)
                                            subsystems.append(subsysdevlist)
                                            
                                        else:
                                            
                                            if subsys == 'User sub-systems':
                                                subsystems.append((subsubsys))
                                            else:
                                                subsystems.append((subsys))
                                                
                                            subsystems.append(dev)
                                else:
                                    if 'n/a' in self.devhierdict[dev][subsys][subsubsys]: self.devhierdict[dev][subsys][subsubsys].remove('n/a')  
                                    compvalues.append(self.devhierdict[dev][subsys][subsubsys])                                         
                                    if type(comps) is list:
                                        subsyslist = []   
                                        subsysdevlist = [] 
                                        for indcomp in comps:
                                            if subsys == 'User sub-systems':                                                    
                                                subsyslist.append((subsubsys))
                                            else:
                                                subsyslist.append((subsys))
                                            subsysdevlist.append((dev))
                                        subsystems.append(subsyslist)
                                        subsystems.append(subsysdevlist)
                                    else: 
                                        if subsys == 'User sub-systems':
                                            subsystems.append((subsubsys))
                                        else:
                                            subsystems.append((subsys))
                                        subsystems.append(dev)
                        else:
                            for comps in self.devhierdict[dev][subsys]:
                                if 'n/a' in self.devhierdict[dev][subsys]: self.devhierdict[dev][subsys].remove('n/a') 
                                compvalues.append(comps) 
                                subsystems.append(subsys)
                                subsystems.append(dev)
                    # module_logger.info("\n".join(logmsg))
                    # logmsg=[""]
                    # logmsg.append('compvalues {}'.format(compvalues))
                    # logmsg.append('subsystems {}'.format(subsystems))  
                    # logmsg.append('subsyslist {}'.format(subsyslist))                  
                    # logmsg.append('self.subsystems {}'.format(subsystems))
                    # module_logger.info("\n".join(logmsg)) 
                    """ Place components in correct hierarchy positions """
                    def check(lst, replace):
                        newlst = lst[:]
                        complistzip = []
                        for index, item in enumerate(lst):                            
                            if type(item) is list: 
                                lst[index] = check(lst[index], replace)
                            elif type(item) is str:                                  
                                if lst[index] == replace:
                                    if type(compvalues) is list:                                        
                                        for intcomp,complist in enumerate(compvalues): 
                                            if type(complist) is list and len(compvalues[intcomp]) > 1: 
                                                complistzip.append(zip(compvalues[intcomp],subsystems[intcomp], subsystems[intcomp]))
                                            elif type(complist) is list and len(compvalues[intcomp]) == 1:
                                                complistzip.append([(compvalues[intcomp][0], subsystems[intcomp][0], subsystems[intcomp][0])])
                                            else:
                                                complistzip.append((compvalues[intcomp], subsystems[intcomp], subsystems[intcomp]))
                                    newlst[index] = complistzip                                        
                        return newlst
                    

                    devfrvalues = check(devfrvalues,dev)

            
            substationlst = []  
            substationdevlist = []
            substationvalues = []
            elecassylst = []  
            elecassylstdevlist = []
            elecassyvalues = []
            
            if self._variables.eleclayout == 'multiplehubs':
                deviceID = 'subhub'+ '{0:03}'.format(intsubhub+1)
                for comps in self.arrayhierdict[deviceID]['Substation']:
                    if comps  == 'n/a': 
                        self.arrayhierdict[deviceID]['Substation'].remove('n/a')  
                    substationlst.append('Substation')    
                    substationdevlist.append(deviceID)
                subsyslendict['Substation'] = len(substationlst)
                substationvalues.append(zip(self.arrayhierdict[deviceID]['Substation'],substationlst,substationdevlist)) 
                for comps in self.arrayhierdict[deviceID]['Elec sub-system']:   
                    if comps  == 'n/a': 
                        self.arrayhierdict[deviceID]['Elec sub-system'].remove('n/a')  
                    elecassylst.append('Elec sub-system')    
                    elecassylstdevlist.append(deviceID)
                elecassyvalues.append(zip(self.arrayhierdict[deviceID]['Elec sub-system'],elecassylst,elecassylstdevlist)) 
                subhublevelvalues = substationvalues[0]+elecassyvalues[0]+devfrvalues[intsubhub]
                frvalues.append([subhublevelvalues])
                subsyslendict['Elec sub-system'] = len(elecassylst)
                stringfrvalues = devfrvalues
                
            else: stringfrvalues = [x for sublist in devfrvalues for x in sublist] 

        substationlst = []  
        substationdevlist = []
        substationvalues = []
        exportcableedevlist = []
        exportcabledevlist = []
        exportcablevalues = []
        
        for comps in self.arrayhierdict['array']['Substation']:
            if comps  == 'n/a': 
                self.arrayhierdict['array']['Substation'].remove('n/a')  
            substationlst.append('Substation')    
            substationdevlist.append('array')
            
        subsyslendict['Substation'] = len(substationlst)
        substationvalues.append(zip(self.arrayhierdict['array']['Substation'],substationlst,substationdevlist))                 
        
        for comps in self.arrayhierdict['array']['Export cable']:
            if comps  == 'n/a': 
                self.arrayhierdict['array']['Export cable'].remove('n/a')  
            exportcableedevlist.append('Export Cable')
            exportcabledevlist.append('array')
        
        subsyslendict['Export Cable'] = len(exportcableedevlist)
        exportcablevalues.append(zip(self.arrayhierdict['array']['Export cable'],exportcableedevlist,exportcabledevlist))
        arraylevelvalues = substationvalues[0] + exportcablevalues[0]
        
        if self._variables.eleclayout == 'multiplehubs':
            frvalues2 = arraylevelvalues + frvalues
        else:
            frvalues2 = arraylevelvalues + devfrvalues[0]
        
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
            frvalues2 = check2(frvalues2, comps)
            #self.frvalues3 = check2(frvalues2,comps) 
            # logmsg = [""]
            # logmsg.append('self.frvalues3  {}'.format(self.frvalues3))
            # module_logger.info("\n".join(logmsg))
        
        
        ### Generation of reliability function equations
        ### Access individual lists to determine reliability at mission time
        
        # logmsg.append('devfrvalues {}'.format(devfrvalues))
        # module_logger.info("\n".join(logmsg)) 
        
        rcompvalues = rcompmt(frvalues2,
                              self._variables.eleclayout,
                              self._variables.mtime)
        self.rcompvalues2 = copy.deepcopy(rcompvalues)
        
        import pprint
        pprint.pprint(rcompvalues)
        import sys
        sys.exit()
        
        
        #self.rcompvalues3 = copy.deepcopy(self.rcompvalues)
        # fil = open('RAM_outputs.txt','w');
        # fil.write('%%%%%%%%%%%%%%%%%%Reliability Values%%%%%%%%%%%%%%%%%%\r\n\r\nself.rcompvalues2\r\n')
        # for i in range(0,len(self.rcompvalues2)):
        # np.savetxt(fil,np.array(self.rcompvalues2),fmt='%s',delimiter='\t')
        # logmsg = [""]
        # logmsg.append('self.rcompvalues2 {}'.format(self.rcompvalues2))
        # module_logger.info("\n".join(logmsg))   

        rsubsysvalues = rsubsysmt(rcompvalues,
                                  self._variables.eleclayout,
                                  self._variables.systype,
                                  subsyslendict)
        
        self.rsubsysvalues2 = copy.deepcopy(rsubsysvalues)
        #self.rsubsysvalues3 = copy.deepcopy(self.rsubsysvalues)
        # fil.write('self.rsubsysvalues3\r\n')
        # np.savetxt(fil,self.rsubsysvalues3,fmt='%s',delimiter='\t')
        # logmsg = [""]
        # logmsg.append('self.rsubsysvalues3 {}'.format(self.rsubsysvalues2))
        # module_logger.info("\n".join(logmsg))
        
        rdevvalues = rdevmt(rsubsysvalues,
                            self._variables.eleclayout)
        self.rdevvalues2 = copy.deepcopy(rdevvalues)
        # fil.write('\r\n\r\nself.rdevvalues2\r\n')
        # np.savetxt(fil,self.rdevvalues2,fmt='%s',delimiter='\t')
        # logmsg = [""]
        # logmsg.append('self.rdevvalues2 {}'.format(self.rdevvalues2))
        # module_logger.info("\n".join(logmsg))
        
        if self._variables.eleclayout:
            # Call stringdev, string and subhub methods only if an electrical
            # network has been specified 
            
            rstringdevvalues = rstringdevmt(rdevvalues,
                                            self._variables.eleclayout)
            self.rstringdevvalues2 = copy.deepcopy(rstringdevvalues)
            # fil.write('\r\n\r\nself.rstringdevvalues\r\n')
            # np.savetxt(fil,self.rstringdevvalues,fmt='%s',delimiter='\t')
            # logmsg = [""]
            # logmsg.append('self.rstringdevvalues {}'.format(self.rstringdevvalues))
            # module_logger.info("\n".join(logmsg))
            
            rstringvalues = rstringmt(rstringdevvalues,
                                      self._variables.eleclayout,
                                      stringlist,
                                      subhubdevlist)
            self.rstringvalues2 = copy.deepcopy(rstringvalues)
            # fil.write('\r\n\r\nself.rstringvalues2\r\n')
            # np.savetxt(fil,self.rstringvalues2,fmt='%s',delimiter='\t')
            # logmsg = [""]
            # logmsg.append('self.rstringvalues2 {}'.format(self.rstringvalues2))
            # module_logger.info("\n".join(logmsg))
            
            
                    # fil.write('\r\n\r\nself.rsubhubvalues2\r\n')
                    # np.savetxt(fil,self.rsubhubvalues2,fmt='%s',delimiter='\t')
            rsubhubvalues = rsubhubmt(rstringvalues,
                                      self._variables.eleclayout)
            self.rsubhubvalues2 = copy.deepcopy(rsubhubvalues)
            # logmsg = [""]
            # logmsg.append('self.rsubhubvalues2  {}'.format(self.rsubhubvalues2))
            # module_logger.info("\n".join(logmsg))
            
            if self._variables.eleclayout in ('radial',
                                              'singlesidedstring',
                                              'doublesidedstring'):
                rarrayvalue = rarraymt(rstringvalues,
                                       self._variables.eleclayout)
                
            elif self._variables.eleclayout == 'multiplehubs':
                
                rarrayvalue = rarraymt(rsubhubvalues,
                                       self._variables.eleclayout)
        
        else:
            
            rarrayvalue = copy.deepcopy(rdevvalues)
        
        self.rarrayvalue2 = copy.deepcopy(rarrayvalue)
        # fil.write('\r\n\r\nself.rarrayvalue2\r\n')
        # np.savetxt(fil,self.rarrayvalue2,fmt='%s',delimiter='\t')
        # fil.close()
        # logmsg = [""]
        # logmsg.append('self.rarrayvalue2  {}'.format(self.rarrayvalue2))
        # module_logger.info("\n".join(logmsg))
    
    def ttf(self):
        """ Calculation of component TTFs and system MTTF """
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
        
        self.rsubsysvalues2 = subsysmttf(self.rsubsysvalues2,
                                         self._variables.eleclayout)
        
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
        
        def arraymttf():
            """ Top level MTTF calculation """
            mttfarray = []
            if self._variables.eleclayout:
                mttfarray = ('array', self.rarrayvalue2[2] ** -1)
            else:
                mttfarray = ('array', 'n/a')
            return mttfarray
        
        """ System MTTF in hours """
        print self.rarrayvalue2
        self.mttfarray = arraymttf()
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
            
            print "**"
            print self._variables.mttfreq
            print self.mttfarray[1]
            
            self.mttfpass = self._variables.mttfreq < self.mttfarray[1]
            
            if self.mttfpass:
                logmsg.append(passMsg)
            else:
                logmsg.append(failMsg)
                
            module_logger.info("\n".join(logmsg))

    def rpn(self, severitylevel):
        """ RPN calculation. Frequency definitions can be found in
        Deliverable 7.2
        """
        
        complist = [(comp, fr) for comp, fr in self.arrayfrdict.items()]
        
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
            
            if severitylevel == 'critical':
                rpn[compind] = 2.0 * freq[compind]
            elif severitylevel == 'non-critical':
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
        complist = [x for x in complist if x != 'dummy']
        rpnvalues = [x for x, y in zip(rpnvalues, complist) if y != 'dummy']
        
        self.rpncomptab = pd.DataFrame(rpnvalues,
                                       index=complist,
                                       columns=['Probability of failure %',
                                                'Risk Priority Number'])
        
        return

def get_arrayfrdict (dbdict,
                     complist,
                     severitylevel,
                     calcscenario):
    
    # For components with an id number look up respective failure rates 
    # otherwise for designed components (i.e. shallow/gravity foundations, 
    # direct embedment anchors and suction caissons) in addition to 
    # grouted jointed use generic failure rate of 1.0x10^-4 failures 
    # per annum (1.141x10^-14 failures per 10^6 hours)
    
    # Note:
    #  * If no data for a particular calculation scenario, failure rate 
    #    defaults to mean value
    #  * If no non-critical failure rate data is available use critical values
    
    arrayfrdict = {}
    designed_comps = ["dummy",
                      "n/a",
                      "ideal",
                      "gravity",
                      "shallowfoundation",
                      "suctioncaisson",
                      "directembedment",
                      "grout"]
    
    if calcscenario == 'lower':
        cs = 0
    elif calcscenario == 'mean':
        cs = 1
    elif calcscenario == 'upper':
        cs = 2
    else:
        err_str = "Argument 'calcscenario' may only take values 0, 1, or 2"
        raise ValueError(err_str)
    
    for comp in complist:
        
        if comp in designed_comps:
            arrayfrdict[comp] = 1.141 * 10.0 ** -14.0
            continue
        
        dbitem = dbdict[comp]['item10']
        
        if severitylevel == 'critical':
            
            if dbitem['failratecrit'][cs] == 0.0:
                arrayfrdict[comp] = dbitem['failratecrit'][1]
            else:
                arrayfrdict[comp] = dbitem['failratecrit'][cs]
        
        else:
            
            if dbitem['failratenoncrit'][1] == 0.0:
               dbitem['failratenoncrit'] = dbitem['failratecrit']
            
            if dbitem['failratenoncrit'][cs] == 0.0:
                 arrayfrdict[comp] = dbitem['failratenoncrit'][1]
            else:
                 arrayfrdict[comp] = dbitem['failratenoncrit'][cs]
    
    return arrayfrdict


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


def subsysmttf(failure_rate_network, eleclayout):
    """ Subsystem level MTTF calculation based on PAR/SER hierarchy """
    
    mttf_network = []
                
    for group in failure_rate_network:
                                        
        if isinstance(group, tuple) and group[0] == "SER":
            
            frs = group[4]
                                
            if eleclayout in ['singlesidedstring',
                              'doublesidedstring'] and isinstance(frs, list):
                
                frs = binomial(frs)
            
            new_tuple = (group[0],
                         group[1],
                         group[2],
                         frs ** -1.0)
            mttf_network.append(new_tuple)
                
        elif isinstance(group, tuple) and group[0] == "PAR":
            
            new_tuple = ("PAR", subsysmttf(group[1], eleclayout))
            mttf_network.append(new_tuple)
            
        else:
            
            # Should be a list
            new_list = subsysmttf(group, eleclayout)
            mttf_network.append(new_list)
        
    return mttf_network


def getfrvalues(arrayhierdict, devhierdict):
    
    frvalues = []
    
    owner = "array"
    array_dict = arrayhierdict[owner]
    
    frvalues.extend(get_array_frvalues(array_dict, owner))
    
    if "subhub" in array_dict["layout"][0][0]:
        
        subhubvalues = []
        
        for subhubgroup in array_dict["layout"]:
            
            # Assuming a single subhub per group
            owner = subhubgroup[0]
            subhub_dict = arrayhierdict[owner]
            subhub_comps = get_subhub_frvalues(subhub_dict, owner)
            
            if subhub_dict["layout"]:
                subhub_comps.append(get_dev_frvalues(subhub_dict["layout"][0],
                                                     devhierdict))
    
            subhubvalues.append(subhub_comps)
            
        frvalues.append(subhubvalues)
        
    elif array_dict["layout"]:
        
        frvalues.append(get_dev_frvalues(subhub_dict["layout"][0],
                                         devhierdict))
        
    return frvalues
        
    
def get_array_frvalues(arraydict, owner):
    
    array_list = []
    system_types = ["Export cable", "Substation"]
    
    for system in system_types:
        
        comps = strip_dummy(arraydict[system])
        if comps is None: continue
        complist = make_component_lists(comps, system, owner)
        array_list.extend(complist)
    
    return array_list


def get_subhub_frvalues(arraydict, owner):
    
    array_list = []
    system_types = ["Elec sub-system", "Substation"]
    
    for system in system_types:
        
        comps = strip_dummy(arraydict[system])
        if comps is None: continue
        complist = make_component_lists(comps, system, owner)
        array_list.extend(complist)
    
    return array_list


def get_dev_frvalues(dev_list, devhierdict):
    
    all_devices = []
    system_types = ['Array elec sub-system',
                    'M&F sub-system',
                    'User sub-systems']    
    
    for dev in dev_list:
        
        devdict = devhierdict[dev]
        
        devcomps = []
        
        for system in system_types:
            
            if system not in devdict: continue
            
            for subsystem, checkcomps in devdict[system].items():
                
                if system == 'User sub-systems':
                    owner = subsystem
                else:
                    owner = system
                
                checkcomps = strip_dummy(checkcomps)
                if checkcomps is None: continue
            
                syscomps = []
            
                for comps in checkcomps:
                
                    complist = make_component_lists(comps, owner, dev)
                    
                    if len(checkcomps) == 1:
                        devcomps.append(complist)
                    else:
                        syscomps.append(complist)
                    
                if syscomps:
                    devcomps.append(syscomps)
        
        if devcomps:
            all_devices.append(devcomps)
        
    if not all_devices: all_devices = None
    
    return all_devices


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
    

def make_component_lists(comps, subsys, owner):
    
    if isinstance(comps, basestring):
        return (comps, subsys, owner)
    
    complist = []
    
    for subcomps in comps:
        sublist = make_component_lists(subcomps, subsys, owner)
        if isinstance(sublist, tuple):
            complist.append(sublist)
        else:
            complist.append([sublist])
    
    return complist


def rcompmt(lst3, eleclayout, mtime):
    # Individual component reliabilities calculated """
    
    newlst3 = lst3[:]
    
    for index3, item3 in enumerate(lst3):
        
        rpara = []
        
        if type(item3) is list:
            
            if any(isinstance(x, list) for x in item3): 
                
                if (eleclayout == 'multiplehubs' and type(item3[0]) is tuple):
                    if item3[0][2][0:6] == 'subhub':
                        lst3[index3] = ('PAR', rcompmt(lst3[index3],
                                                       eleclayout,
                                                       mtime) )
                    else:
                        lst3[index3] = rcompmt(lst3[index3],
                                               eleclayout,
                                               mtime)
                else:
                    lst3[index3] = rcompmt(lst3[index3],
                                           eleclayout,
                                           mtime)
            
            else:
                
                for comps in item3:
                    
                    comp = comps[0]
                    subsys = comps[1]
                    devs = comps[2]
                    frs = comps[3]
                    rpara.append(('SER',
                                  comp,
                                  subsys,
                                  devs,
                                  math.exp(-frs * mtime),
                                  frs))
                    
                # 'PAR' used to define parallel relationship. Top level is
                # always treated as series (main hub and export cable)
                if item3[0][2] == 'array':
                    
                    lst3[index3] = ('SER', rpara)
                    
                else:
                    
                    samesubsys = [i for i, v in enumerate(rpara)
                                                    if v[2] == rpara[0][2]]
                    
                    if len(rpara) == len(samesubsys):
                        if len(rpara) == 1:
                            lst3[index3] = ('PAR', rpara)
                        else:
                            lst3[index3] = ('PAR', rpara)
                    else:
                        lst3[index3] = rpara
        else:
            
            # 'SER' used to define series relationship
            lst3[index3] = ('SER',
                            item3[0],
                            item3[1],
                            item3[2],
                            math.exp(-item3[3] * mtime),
                            item3[3])
        
        newlst3[index3] = lst3[index3]
    
    return newlst3

def rsubsysmt(lst3, eleclayout, systype, subsyslendict):
    # Sub-system level grouping """
    
    newlst3 = lst3[:]
    newlst4 = []
    sersubass = []
    sersubass2 = [] 
    
    for index3, item3 in enumerate(lst3):
        
        if type(item3) is list:
            
            if any(isinstance(x, list) for x in item3):
                
                newlst3[index3] = rsubsysmt(lst3[index3],
                                            eleclayout,
                                            systype,
                                            subsyslendict)
                continue
            
            elif (eleclayout == 'multiplehubs' and
                  item3[0][0] == 'PAR' and
                  item3[0][1][0][3][0:6] == 'subhub'):
                
                newlst3[index3] = ('PAR', rsubsysmt(item3[0][1],
                                                    eleclayout,
                                                    systype,
                                                    subsyslendict))
                continue
            
            rgroup = []
            rgroupser = defaultdict(list)
            rgrouppara = defaultdict(list)
            rgroupsing = defaultdict(list)
            frgroupser = defaultdict(list)
            frgrouppara = defaultdict(list)
            frgroupsing = defaultdict(list)
            sersubass = []
            rsingdict = defaultdict(list)

            # Find parallel assemblies first
            paraind = [i for i, z in enumerate(item3[0:len(item3)])
                                                            if z[0] == 'PAR']
            
            for subass in paraind:
                
                rserdict = defaultdict(list)
                rparadict = defaultdict(list)
                rsingdict = defaultdict(list)
                frserdict = defaultdict(list)
                frparadict = defaultdict(list)
                frsingdict = defaultdict(list)
                
                # Find components within the same subsystem 
                for x, y in Counter([x[2] for x in item3[subass][1]]).items():
                    
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
                    
                    if (x == 'M&F sub-system' and systype in ('wavefloat',
                                                              'tidefloat')):
                        # k of n system
                        if rserdict[x]:
                            rgroupser[x].append(np.prod(rserdict[x]))
                        if rparadict[x]:
                            rgrouppara[x].append(np.prod(rparadict[x])) 
                    elif (x == 'M&F sub-system' and systype in ('wavefixed',
                                                                'tidefixed')):
                        if rserdict[x]:
                            rgroupser[x].append(np.prod(rserdict[x]))
                        if rparadict[x]:
                            rgrouppara[x].append(1 - np.prod(rparadict[x]))
                    elif x != 'M&F sub-system':
                        if rserdict[x]:
                            rgroupser[x].append(np.prod(rserdict[x]))
                        if rparadict[x]:
                            rgrouppara[x].append(1 - np.prod(rparadict[x]))
                    
                    if rsingdict[x]:
                        rgroupsing[x].append(rsingdict[x]) 
                    if frserdict[x]:
                        frgroupser[x].append(sum(frserdict[x]))
                    if frparadict[x]:
                        frgrouppara[x].append(binomial(frparadict[x].values()))
                    if frsingdict[x]:
                        frgroupsing[x].append(frsingdict[x])
            
            if any(rgrouppara):
                
                for subsys in rgrouppara:
                    rgroup.append(('SER',
                                   subsys,
                                   comps[3],
                                   1 - np.prod(rgrouppara[subsys]),
                                   binomial(frgrouppara[subsys])))
            
            if any(rgroupser): 
                
                for subsys in rgroupser:
                    
                    if (eleclayout in ('singlesidedstring',
                                       'doublesidedstring') and
                        subsys == 'Array elec sub-system'):
                        # Prevent grouping of parallel link
                        rgroup.append(('SER',
                                       subsys,
                                       comps[3],
                                       rgroupser[subsys],
                                       frgroupser[subsys]))
                        
                    if (subsys == 'M&F sub-system' and
                        systype in ('wavefloat', 'tidefloat')):
                        
                        # Treat mooring systems as k of n system, i.e. one 
                        # line failure is permitted for Accident Limit State.
                        # All lines treated as having reliability equal to the
                        # line with the lowest reliability value
                        
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
                            rgroupval = rgroupsort[i-1]
                            fact = (math.factorial(n) /
                                   (math.factorial(n-i) * math.factorial(i)))
                            rmnval =  fact * rgroupval ** i * \
                                               (1 - rgroupval) ** (n - i)
                            rmngroup.append(rmnval)
                            frmngroup.append((i * rgroupval) ** -1.0)
                        
                        rgroup.append(('SER',
                                       subsys,
                                       comps[3],
                                       sum(rmngroup),
                                       sum(frmngroup) ** -1.0))
                    
                    elif (subsys == 'M&F sub-system' and
                          systype in ('wavefixed', 'tidefixed')):
                        
                        # Foundation is k of n system where functionality of
                        # all foundations is required
                        rmngroup = [] 
                        frmngroup = [] 
                        n = len(rgroupser[subsys])
                        k = n
                        frmngroup = sum(frgroupser[subsys])
                        rmngroup = np.prod(rgroupser[subsys])
                        rgroup.append(('SER',
                                       subsys,
                                       comps[3],
                                       rmngroup,frmngroup))
                    
                    elif subsys in ('Pto',
                                    'Hydrodynamic',
                                    'Control',
                                    'Support structure'):
                        
                        # Parallel components within user-defined sub-systems
                        rgroupserpara = []
                        
                        for rparavals in rgroupser[subsys]:
                            rgroupserpara.append(1 - rparavals)
                            
                        rgroup.append(('SER',
                                       subsys,
                                       comps[3], 1.0 - np.prod(rgroupserpara),
                                       binomial(frgroupser[subsys])))
                        
            # Single subsystem in parallel configuration """
            if any(rsingdict):
                
                for subsys in rgroupsing:
                    rgroup.append((comps[0],
                                   subsys,
                                   comps[3],
                                   rsingdict[subsys],
                                   frsingdict[subsys]))
            
            lst3[index3]  = rgroup 
            
            # Find series assemblies
            serind = [i for i, z in enumerate(item3[0:len(item3)])
                                                        if z[0] == 'SER']
            
            for subass in serind: 
                sersubass.append(item3[subass])
            
            # Find components within the same subsystem
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
                if frparadict[x]:
                    frgrouppara[x].append(binomial(frparadict[x].values()))
                
                if rgroupser[x]:
                    rgroup.append(('SER',
                                   x,
                                   comps[3],
                                   rgroupser[x],
                                   frgroupser[x])) 
                if rgrouppara[x]:
                    rgroup.append(('SER',
                                   x,
                                   comps[3],
                                   rgrouppara[x],
                                   frgrouppara[x]))
                if rsingdict[x]:
                    rgroup.append((comps[0],
                                   x,
                                   comps[3],
                                   rsingdict[x],
                                   frsingdict[x]))
            
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
            
            # Find components within the same subsystem
            
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
                if rparadict[x]:
                    rgrouppara[x]  = 1 - np.prod(rparadict[x]) 
                if frserdict[x]: frgroupser[x] = sum(frserdict[x])
                if frparadict[x]:
                    frgrouppara[x].append(binomial(frparadict[x].values()))
            
            if any(rserdict):
                for subsys in rserdict:
                    if (rgroupser[subsys] and
                        len(rserdict[subsys]) == subsyslendict[subsys]): 
                        rgroup.append(('SER',
                                       subsys,
                                       comps[3],
                                       rgroupser[subsys],
                                       frgroupser[subsys]))
            
            if any(rparadict):
                for subsys in rparadict:
                    if (rgrouppara[subsys] and
                        len(rparadict[subsys]) == subsyslendict[subsys]): 
                        rgroup.append(('SER',
                                       subsys,
                                       comps[3],
                                       rgrouppara[subsys],
                                       binomial(frgrouppara[subsys])))
                        
            if any(rsingdict):
                for subsys in rsingdict: 
                    if (subsys == lst3[index3][2] and
                        subsyslendict[subsys] == 1):
                        rgroup.append((comps[0],
                                       subsys,
                                       comps[3],
                                       rsingdict[subsys],
                                       frsingdict[subsys]))
            
            lst3[index3]  = rgroup
        
        newlst3[index3] = lst3[index3]
    
    newlst4 = filter(None, newlst3)
    
    return newlst4

def rdevmt(lst3, eleclayout):
    # Device level grouping. Only mooring and user-defined subsystems are
    # grouped
    newlst3 = lst3[:]
    relec = []
    
    for index3, item3 in enumerate(lst3):
        
        rpara = []
        rser = [] 
        frser = []
        frpara = []
        rgroup = []
        
        if type(item3) is list:
            
            if any(isinstance(x, list) for x in item3):
                lst3[index3] = rdevmt(lst3[index3], eleclayout)
                continue
            
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
                    relec = (subsys[0],
                             subsys[1],
                             subsys[2],
                             subsys[3],
                             subsys[4])
            
            if rpara:
                rgroup.append(('PAR',
                               subsys[2],
                               1 - np.prod(rpara),
                               binomial(frpara),
                               relec))
            
            if rser:
                rgroup.append(('SER',
                               subsys[2],
                               np.prod(rser),
                               sum(frser),
                               relec))
            
            if item3[0][1] in ('Substation', 'Export Cable'):
                lst3[index3] = item3[0]                      
            elif (eleclayout == 'multiplehubs' and
                  item3[0][1] == 'Elec sub-system'):
                lst3[index3] = item3[0] 
            else:
                lst3[index3] = rgroup[0]
        
        elif (eleclayout == 'multiplehubs' and item3[0] == 'PAR'):
            lst3[index3] = ('PAR', rdevmt(item3[1], eleclayout))
        
        newlst3[index3] = lst3[index3]
    
    return newlst3

def rstringdevmt(lst3, eleclayout):
    # String-device level grouping
    
    newlst3 = lst3[:]
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
        
        if eleclayout in ('radial',
                          'singlesidedstring',
                          'doublesidedstring'): 
            
            if type(item3) is not list: continue
        
            print item3
            import sys
            sys.exit()
                
            if any(isinstance(x, list) for x in item3):
                lst3[index3] = rstringdevmt(lst3[index3], eleclayout)
                continue
            
            for subsys in item3:
                if (subsys[4] and  
                    subsys[4][1] == 'Array elec sub-system'):
                    print subsys
                    import sys
                    sys.exit()
                    relec.append(subsys[4][3]) 
                    frelec.append(subsys[4][4])
                    
            if eleclayout in ('singlesidedstring', 'doublesidedstring'): 
                # Flatten lists
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
                
                if eleclayout  == 'radial':
                    relecgroup = np.prod(relec[index4-len(relec):])
                    frelecgroup = sum(frelec[index4-len(frelec):])
                elif eleclayout in ('singlesidedstring', 'doublesidedstring'):
                    relecgrouplhs = np.prod(relecmerged[0:index4+1])
                    frelecgrouplhs = sum(frelecmerged[0:index4+1])
                    relecgrouprhs = relecmerged[index4+1:]
                    relecgrouprhs = np.prod(relecgrouprhs) 
                    frelecgrouprhs = frelecmerged[index4+1:]
                    frelecgrouprhs = sum(frelecgrouprhs)

                    # Compare reliabilities on left hand side and right hand
                    # side of network
                    relecgroup = max(np.prod(relecgrouplhs),
                                     np.prod(relecgrouprhs))
                    frelecgroup = min(frelecgrouplhs, frelecgrouprhs)
                    
                rgroup.append(('SER',
                               rdev[1],
                               np.prod([rdev[2],relecgroup]),
                               sum([frdev,frelecgroup])))
            
            lst3[index3] = ('PAR',rgroup)
                 
        elif eleclayout == 'multiplehubs': 
            
            if item3[0] != 'PAR': continue
            if type(item3[1]) is not list: continue
            
            relec = [] 
            frelec = []
            
            for string in item3[1]:
                
                if type(string) is not list: continue
            
                for subsys in string:
                    
                    if (subsys[4] and
                        subsys[4][1] == 'Array elec sub-system'):
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
                        rgroup.append(('SER',
                                       rdev[1],
                                       np.prod([rdev[2],relecgroup]),
                                       sum([frdev,frelecgroup])))
                    
                    rstringgroup.append(('PAR', rgroup))
                
                else:
                    
                    rstringgroup.append(('SER',
                                         string[1],
                                         string[2],
                                         string[3],
                                         string[4]))
            
            if rstringgroup:
                lst3[index3] = [('PAR',rstringgroup)]
        
        newlst3[index3] = lst3[index3]
    
    return newlst3

def rstringmt(lst3, eleclayout, stringlist, subhubdevlist):
    # String level grouping
    
    newlst3 = lst3[:]
    
    for index3, item3 in enumerate(lst3):
        
        rgroup = []
        rpara = []   
        rgrouppara = []
        frgrouppara = []
        rstringgroup = []
        frpara = []
        
        if eleclayout in ('radial',
                          'singlesidedstring',
                          'doublesidedstring'):
            
            if type(item3) is list: 
                if any(isinstance(x, list) for x in item3):
                    rgroup = rstringmt(lst3[index3],
                                       eleclayout,
                                       stringlist,
                                       subhubdevlist)
                lst3[index3] = ('SER', rgroup)
                continue
            
            if item3[0] == 'PAR':
                
                for devs in item3[1]:
                    
                    if devs[0] == 'SER':
                        stringind = [x for x in stringlist if devs[1] in x]
                        rpara.append(devs[2])
                        frpara.append(devs[3])
                
                if stringind:
                
                    rstringgroup = ('PAR',
                                    'String ' + str(stringind[0][0]),
                                    np.prod(rpara),
                                    sum(frpara)) 
                    rgroup.append(rstringgroup)
                    lst3[index3] = ('PAR', rgroup)
            
            else:
                
                rgroup.append(('SER',
                               item3[1],
                               item3[2],
                               item3[3],
                               item3[4]))
                lst3[index3] = rgroup[0]
        
        elif eleclayout == 'multiplehubs':
            
            if item3[0][0] != 'PAR': continue
        
            if type(item3[0][1]) is list:
                
                for subhub in item3[0][1]:
                    
                    if subhub[0] != 'PAR':
                        
                        rgroup.append(subhub)
                        continue
                        
                    rpara = []
                    frpara = []
                    
                    for devs in subhub[1]:
                        
                        print devs
                        
                        rgrouppara = []
                        
                        if devs[0] == 'SER':
                            
                            stringind = [x for x in stringlist
                                                         if devs[1] in x]
                            subhubind = [x for x in subhubdevlist
                                                         if devs[1] in x]
                            
                            rpara.append(devs[2])
                            frpara.append(devs[3])
                            
                        rgrouppara = np.prod(rpara)
                        frgrouppara = sum(frpara)
                    
                    if stringind:
                    
                        rstringgroup.append([
                                'String ' + str(stringind[0][0]),
                                'subhub'+ '{0:03}'.format(subhubind[0][0]+1),
                                rgrouppara,
                                frgrouppara])
                
                rgroup.append(('PAR', rstringgroup))
                lst3[index3] = ('PAR', rgroup)
            
            else:
                
                lst3[index3] = item3
        
        newlst3[index3] = lst3[index3]
    
    return newlst3

def rsubhubmt(lst3, eleclayout):
    
    # Subhub level grouping (only used when multiple hubs exist) 
    if eleclayout in ('radial',
                      'singlesidedstring',
                      'doublesidedstring'):
        return
    
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
                
            # Subhubs are assumed to be connected in parallel with 
            # the main hub
            rgroup.append(('PAR',rsubhub))
            
        elif item3[0] == 'SER':
            rgroup.append(item3)
    
    return rgroup

def rarraymt(lst3, eleclayout):
    # Array level grouping
    # Strings and subhubs assumed to be parallel
    
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
        
        if eleclayout in ('radial', 'singlesidedstring', 'doublesidedstring'):
            
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
            
        elif eleclayout == 'multiplehubs':
            
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
        # rgroup.append((1 - np.prod(rstringcomb),
        #               np.reciprocal(binomial(frstringcomb))))
        rgroup.append((1 - np.prod(rstringcomb), binomial(frstringcomb)))

    if eleclayout in ('radial', 'singlesidedstring', 'doublesidedstring'):
        
        rarraycomb = []
        frarraycomb = []
        
        for arrayelem in rgroup:
            rarraycomb.append(arrayelem[0])
            frarraycomb.append(arrayelem[1])
        
        rarray = (np.prod(rarraycomb), sum(frarraycomb))
    
    elif eleclayout == 'multiplehubs':
        # Subhubs are assumed to be connected in parallel with 
        # the main hub
        rarrayser = (1-np.prod(rsubhubser)) * np.prod(rarrayser)
        frarrayser = binomial(frsubhubser) + sum(frarrayser)
        rarray = [rarrayser, frarrayser] 
    
    return ('array', rarray[0], rarray[1])
