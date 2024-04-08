############################ BEGIN LICENSE BLOCK #############################
#                                                                            #
# Version: MPL 1.1/GPL 2.0/LGPL 2.1                                          #
#                                                                            #
# The contents of this file are subject to the Mozilla Public License        #
# Version 1.1 (the "License"); you may not use this file except in           #
# compliance with the License. You may obtain a copy of the License at       #
# http://www.mozilla.org/MPL/                                                #
#                                                                            #
# Software distributed under the License is distributed on an "AS IS" basis, #
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License   #
# for the specific language governing rights and limitations under the       #
# License.                                                                   #
#                                                                            #
# The Original Code is the STELLA Programming Language.                      #
#                                                                            #
# The Initial Developer of the Original Code is                              #
# UNIVERSITY OF SOUTHERN CALIFORNIA, INFORMATION SCIENCES INSTITUTE          #
# 4676 Admiralty Way, Marina Del Rey, California 90292, U.S.A.               #
#                                                                            #
# Portions created by the Initial Developer are Copyright (C) 1996-2020      #
# the Initial Developer. All Rights Reserved.                                #
#                                                                            #
# Contributor(s):                                                            #
#                                                                            #
# Alternatively, the contents of this file may be used under the terms of    #
# either the GNU General Public License Version 2 or later (the "GPL"), or   #
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),   #
# in which case the provisions of the GPL or the LGPL are applicable instead #
# of those above. If you wish to allow use of your version of this file only #
# under the terms of either the GPL or the LGPL, and not to allow others to  #
# use your version of this file under the terms of the MPL, indicate your    #
# decision by deleting the provisions above and replace them with the notice #
# and other provisions required by the GPL or the LGPL. If you do not delete #
# the provisions above, a recipient may use your version of this file under  #
# the terms of any one of the MPL, the GPL or the LGPL.                      #
#                                                                            #
############################# END LICENSE BLOCK ##############################

"""
Mapping STELLA modules to Python namespaces.
"""

from __future__ import print_function, division, absolute_import

import sys
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] >= 3
if PY3:
    unicode = str
    long = int

from types import ModuleType

import stellapi.common as com
from   stellapi.utils import ApiException


### Module to Python namespace mapping

# ISSUE: we need to create this here, since this file is not the top-level stellapi anymore:
stellapi = com.stellapiModule

class Namespace(ModuleType):
    """Namespace class that creates instances that serve as modules to host Python and C definitions
    for STELLA functions of a particular namespace, and that also serve as decorator objects.
    """

    name = None
    singleton = None

    def __new__(cls, *args, **kwargs):
        if cls.singleton is None:
            cls.singleton = super(Namespace, cls).__new__(cls, *args, **kwargs)
        return cls.singleton

    def __init__(self, name=None):
        """`name' is the name of the singleton module instance we are creating.  If the
        module singleton already has a name, it will be changed to the new one.
        """
        self.__name__ = name or self.name
        if self.__name__ is not None:
            sys.modules[self.__name__] = self

    def getName(self, obj):
        objName = None
        if hasattr(obj, 'func_name'):
            objName = obj.func_name
        elif hasattr(obj, '__name__'):
            objName = obj.__name__
        if objName is None:
            raise ApiException('Unable to determine object name: ' + str(obj))
        return objName

    def __call__(self, obj):
        """Decorate function called on `obj' when `self' is used as a decorator.
        """
        #print '__call__:', self, obj
        ns = self
        objName = self.getName(obj)
        # strip off any internal prefixes before adding to the namespace:
        while objName.startswith('_'):
            if objName.find('_', 1) >= 1:
                objName = objName[objName.find('_', 1):]
            else:
                objName = objName[1:]
        # give `obj' its new name and module and link it from the new module; unfortunately, `obj' will
        # still be assigned to the current module after we exit here, for this reason, we usually want to
        # define with a private `_ns_xxx' name, so it won't conflict with anything even if it stays there:
        setattr(obj, '__name__', objName)
        setattr(obj, '__module__', ns)
        setattr(ns, objName, obj)
        return obj


_stellaModuleToNamespaceMap = {}

def qualifiedNameToNormalizedModuleName(qualName):
    """Parse and normalize `qualName' into an absolute module pathname.  `qualName'
    might be a module name or an (optionally) qualified STELLA symbol.
    """
    if com._bootstrapCompleted:
        if qualName.endswith('/'):
            qualName += '_'
        symName, modName, kind = stella.pdef.parseStellaName(qualName, True)
        if modName is None:
            if stella.pdef.getStellaModule(symName, False) is not None:
                return stella.pdef.getStellaModule(symName, False).moduleFullName
            else:
                modName = stella.pdef.oMODULEo.moduleFullName
        qualName = modName + '/' + symName
        if stella.pdef.getStellaModule(qualName, False) is not None:
            return stella.pdef.getStellaModule(qualName, False).moduleFullName
        else:
            return stella.pdef.getStellaModule(modName, True).moduleFullName
    else:
        return '/STELLA'

def defineStellaModuleNamespace(moduleSpec, nsName=None):
    """Define the Python classes and module instances necessary for the Python namespace
    `nsName' to hold objects of STELLA module `moduleSpec'.  If `nsName' is None, it will
    be based on the C++ namespace used for module `moduleSpec'.  This creates Python modules
    `stellapi.ns', `stellapi.ns.pdef' and `stellapi.ns.cdef'. In addition, a separate class
    is generated for each generated Python module to host properties.
    """
    modulePath = qualifiedNameToNormalizedModuleName(moduleSpec)
    if nsName is not None:
        pass
    elif com._bootstrapCompleted:
        nsName = stella.pdef.cppYieldNamespacePrefixFromModule(stella.pdef.getStellaModule(modulePath, True))
    else:
        nsName = 'stella'
    nsRootModule = com.stellapiModule
    nsFullName = nsRootModule.__name__ + '.' + nsName
    nsClassName = nsName.lower().capitalize() + 'Namespace'
    # check for accidental overrides but allow identical redefinitions so we can reload the module:
    if hasattr(nsRootModule, nsClassName) and getattr(getattr(nsRootModule, nsClassName), 'name', None) != nsFullName:
        raise ApiException('Namespace module class already exists: ' + nsClassName)
    if hasattr(nsRootModule, nsName) and getattr(getattr(nsRootModule, nsName), 'name', None) != nsFullName:
        raise ApiException('Namespace module already exists: ' + nsName)
    nsClass = type(nsClassName, (Namespace,), {})
    nsClass.name = nsFullName
    ns = nsClass()
    setattr(nsRootModule, nsClassName, nsClass)
    setattr(nsRootModule, nsName, ns)
    cdefClassName = nsName.lower().capitalize() + 'CDefNamespace'
    cdefClass = type(cdefClassName, (Namespace,), {})
    cdefClass.name = nsRootModule.__name__ + '.' + nsName + '.cdef'
    cdef = cdefClass()
    setattr(nsRootModule, cdefClassName, cdefClass)
    setattr(ns, 'cdef', cdef)
    pdefClassName = nsName.lower().capitalize() + 'PDefNamespace'
    pdefClass = type(pdefClassName, (Namespace,), {})
    pdefClass.name = nsRootModule.__name__ + '.' + nsName + '.pdef'
    pdef = pdefClass()
    setattr(nsRootModule, pdefClassName, pdefClass)
    setattr(ns, 'pdef', pdef)
    mapStellaModuleToNamespace(modulePath, ns)
    return ns

def lookupStellaModuleNamespace(qualName):
    modulePath = qualifiedNameToNormalizedModuleName(qualName)
    return _stellaModuleToNamespaceMap.get(modulePath)

def mapStellaModuleToNamespace(qualName, ns):
    modulePath = qualifiedNameToNormalizedModuleName(qualName)
    _stellaModuleToNamespaceMap[modulePath] = ns
    
def getStellaModuleNamespace(qualName):
    """Return the Python namespace object for the STELLA module indicated by `qualName'.
    If no such namespace exists yet, create on on the fly based on modules C++ translation.
    """
    modulePath = qualifiedNameToNormalizedModuleName(qualName)
    ns = lookupStellaModuleNamespace(modulePath)
    if ns is None:
        # define it on the fly:
        ns = defineStellaModuleNamespace(modulePath)
    return ns

def getStellaModuleCDefNamespace(qualName):
    return getStellaModuleNamespace(qualName).cdef

def getStellaModulePDefNamespace(qualName):
    return getStellaModuleNamespace(qualName).pdef

stella = defineStellaModuleNamespace('/STELLA')

class BootNamespace(Namespace):
    """Special namespace to hold definitions needed during bootstrap of the interface."""
    name = com.stellapiModule.__name__ + '.boot'
boot = BootNamespace()
