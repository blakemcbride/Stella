"""Setup for Python API to the STELLA programming language.
"""

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

import io
import os.path
import setuptools
from  distutils.errors import DistutilsSetupError


# NOTES, TO DO:
# - see https://github.com/pypa/sampleproject for more info in setup
# - paths need to use Unix-style syntax (use distutils.util.convert_path to convert)
# - see .old versions on how to define specialized build commands, for now we
#   rely on cffi to build extension modules which seems to do the trick
#   (see See https://cffi.readthedocs.io/en/latest/cdef.html)
# - see python/stellapi/build_* script TO DOs


def get_stella_version():
    startupFile = os.path.join('sources', 'stella', 'startup.ste')
    try:
        with open(startupFile, 'r') as inp:
            for line in inp:
                if line.startswith('(defglobal *stella-version* '):
                    start = line.find('"')+1
                    end = line.rfind('"')
                    if start > 0 and end > start:
                        return line[start:end]
    except:
        pass
    raise DistutilsSetupError('Failed to determine STELLA version from: ' + startupFile)

setuptools.setup(
    name='stellapi',
    version=get_stella_version(),
    description='Python API to the STELLA programming language',
    long_description=io.open('README.md').read(),
    long_description_content_type='text/markdown',
    license='MPL 1.1 or GPLv2+ or LGPLv2.1+',
    url='https://www.isi.edu/isd/LOOM/Stella',
    author='Hans Chalupsky, USC Information Sciences Institute',
    author_email='hans@isi.edu',

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Software Development :: Compilers',
        'Topic :: Software Development :: Interpreters',
        'License :: OSI Approved :: Mozilla Public License 1.1 (MPL 1.1)',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        # TO DO: figure out if this is ok, this exact version 2.1 what not on PyPI:
        'License :: OSI Approved :: GNU Lesser General Public License v2.1 or later (LGPLv2.1+)',
        # TO DO: figure out if this is the right way to mark this as a programming language:
        'Programming Language :: Other :: STELLA',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='programming language for symbolic programming',

    python_requires='>=2.7',
    setup_requires=['cffi>=1.13'],
    install_requires=['cffi>=1.13'],

    packages=['stellapi'],
    package_dir={'stellapi': 'python/stellapi'},
    # requires build_libstella.py to copy relevant libs, etc. into package_dir/...:
    package_data={'stellapi': ['.libs/*', 'include/*', 'include/*/*', 'include/*/*/*', 'sources/*', 'sources/*/*']},

    cffi_modules=['python/stellapi/build_libstella.py:ffibuilder',
                  'python/stellapi/build_libstella_wrappers.py:ffibuilder',
    ],
    
    project_urls={
        'Source': 'https://www.isi.edu/isd/LOOM/Stella',
    },
)

"""
# testing installation with temporary environment:

> conda deactivate
> tcsh   # start a fresh shell
> conda create -n testenv python=3
> unsetenv PYTHONPATH
> unsetenv LD_LIBRARY_PATH
> conda activate testenv

### IMPORTANT: make sure that's the active environment, since we are installing into it ###
> python -c 'import sys; print(sys.path, sys.version)'

> cd .../stella
> pip install -v .

> python
>>> import stellapi as spi
>>> spi.__version__
'3.6.12'
>>> spi.stella.pdef.oSTELLA_VERSIONo
'3.6.12'
>>> spi.defun('stella/make-date-time')
(<function makeDateTime at 0x7f492a016cd0>, 'stellapi.stella.pdef.makeDateTime', <proxy.MethodSlot |F|MAKE-DATE-TIME>)
>>> spi.stella.pdef.makeDateTime(2000, 10, 30, 14, 59, 59, 200, 10.0)
<proxy.CalendarDate "2000-OCT-30 4:59:59.200 UTC">
>>>

# cleanup:
> conda deactivate
> conda env remove -n testenv

# alternatively to pip, use this for older easy_install process based on eggs:
> python setup.py install

# or with pipenv:
> cd $HOME/.local/share/virtualenvs-defs/testenv/
> conda activate testenv
> setenv VIRTUAL_ENV $CONDA_PREFIX
> pipenv install -skip-lock cffi
> pipenv install -v --skip-lock .../stella-systems/stella/

# creating a source distribution:
> python setup.py sdist -d /tmp/
"""
