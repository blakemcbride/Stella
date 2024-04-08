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
STELLA exception handling support.
"""

from __future__ import print_function, division, absolute_import

import sys
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] >= 3
if PY3:
    unicode = str
    long = int

from stellapi.common import FFI as _ffi
from stellapi.utils import ffi_to_string
from stellapi.namespaces import boot


### Handling STELLA exceptions raised on the C++ side

# This is somewhat tricky, because:
# (1) we can't catch them in C-code, instead we have to catch them on the STELLA C++ side and unwrap to the top level there
#     returning a harmless value such as NULL and then check if an exception ocurred or not
# (2) the exception handler callback below can't create a non-local return to the Python environment that called the C function
#     so instead of raising the exception, it simply stores them on the Python side for later inspection
# (3) we have to wrap all STELLA function proxies that potentially throw exceptions to check right before they return whether an
#     exception was raised, and, if so, finally raise a Python exception at the right place

class StellaException(Exception):
    """Exception wrapper class for STELLA run-time errors."""
    pass

_lastException = None

def setLastException(exc):
    global _lastException
    _lastException = exc

def clearLastException():
    global _lastException
    _lastException = None

def getLastException():
    global _lastException
    return _lastException

@_ffi.callback("void(const char*, const char*)")
def exceptionCallbackHandler(msg, ctxt):
    # This only saves the information for the last exception caught on the C-side on the Python side.
    # Unfortunately, raising an exception here will simply print the stack trace and then return;
    # therefore, a special exception wrapper needs to be created that propagates the exception in Python.
    setLastException(StellaException(ffi_to_string(msg)))

boot.setGlobalExceptionHandler(exceptionCallbackHandler)
