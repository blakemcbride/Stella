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
Common global and configuration variables.
"""

from __future__ import print_function, division, absolute_import

import sys
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] >= 3

import os
import os.path

import cffi


### Configuration

stellapiModule = sys.modules['stellapi']
stellapiHome   = os.path.dirname(stellapiModule.__file__)

# try to impute the STELLA directory where all the relevant include files reside to compile the call wrappers file;
# this is either the location of an existing STELLA source directory, or otherwise the stellapi installation directory:
STELLA_HOME = os.path.join(stellapiHome, os.pardir, os.pardir)
STELLA_HOME = os.path.exists(os.path.join(STELLA_HOME, 'native', 'cpp')) and os.path.realpath(STELLA_HOME) or stellapiHome

DEFAULT_ENCODING        = 'utf_8'
# the directory of this file defaults to site.getusersitepackages()/stellapi/:
CALL_WRAPPER_FILE       = '_libstella_dynamic_wrappers.cc'
PRESERVE_WRAPPER_SOURCE = True
VERBOSE_STARTUP         = False


### Globals

FFI = cffi.FFI()
LOADED_STELLA_LIBS = []

### Internal variables

_bootstrapCompleted = False
