//  -*- Mode: Java -*-
//
// CsValue.java

/*
+---------------------------- BEGIN LICENSE BLOCK ---------------------------+
|                                                                            |
| Version: MPL 1.1/GPL 2.0/LGPL 2.1                                          |
|                                                                            |
| The contents of this file are subject to the Mozilla Public License        |
| Version 1.1 (the "License"); you may not use this file except in           |
| compliance with the License. You may obtain a copy of the License at       |
| http://www.mozilla.org/MPL/                                                |
|                                                                            |
| Software distributed under the License is distributed on an "AS IS" basis, |
| WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License   |
| for the specific language governing rights and limitations under the       |
| License.                                                                   |
|                                                                            |
| The Original Code is the STELLA Programming Language.                      |
|                                                                            |
| The Initial Developer of the Original Code is                              |
| UNIVERSITY OF SOUTHERN CALIFORNIA, INFORMATION SCIENCES INSTITUTE          |
| 4676 Admiralty Way, Marina Del Rey, California 90292, U.S.A.               |
|                                                                            |
| Portions created by the Initial Developer are Copyright (C) 1996-2023      |
| the Initial Developer. All Rights Reserved.                                |
|                                                                            |
| Contributor(s):                                                            |
|                                                                            |
| Alternatively, the contents of this file may be used under the terms of    |
| either the GNU General Public License Version 2 or later (the "GPL"), or   |
| the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),   |
| in which case the provisions of the GPL or the LGPL are applicable instead |
| of those above. If you wish to allow use of your version of this file only |
| under the terms of either the GPL or the LGPL, and not to allow others to  |
| use your version of this file under the terms of the MPL, indicate your    |
| decision by deleting the provisions above and replace them with the notice |
| and other provisions required by the GPL or the LGPL. If you do not delete |
| the provisions above, a recipient may use your version of this file under  |
| the terms of any one of the MPL, the GPL or the LGPL.                      |
|                                                                            |
+---------------------------- END LICENSE BLOCK -----------------------------+
*/

package edu.isi.stella;

import edu.isi.stella.javalib.*;

/** Contextualized value.  Contains a sorted kv-cons list indexed
 * by context. The kv-cons list is never null.  Newer (higher numbered) contexts
 * appear first.
 * @author Stella Java Translator
 */
public class CsValue extends KeyValueList {
  public static CsValue newCsValue() {
    { CsValue self = null;

      self = new CsValue();
      self.theKvList = null;
      return (self);
    }
  }

  public static void copyCurrentValueToChildren(CsValue csvalue, Context homecontext, Stella_Object parentvalue) {
    { Context childcxt = null;
      Cons iter000 = ((Context)(Stella.$CONTEXT$.get())).childContexts.theConsList;

      for (;!(iter000 == Stella.NIL); iter000 = iter000.rest) {
        childcxt = ((Context)(iter000.value));
        { Object old$Context$000 = Stella.$CONTEXT$.get();

          try {
            Native.setSpecial(Stella.$CONTEXT$, childcxt);
            { Stella_Object currentvalue = Stella_Object.accessInContext(csvalue, homecontext, false);

              if (!Stella_Object.eqlP(currentvalue, parentvalue)) {
                KvCons.helpInsertACsValue(csvalue.theKvList, currentvalue, childcxt, false);
              }
            }

          } finally {
            Stella.$CONTEXT$.set(old$Context$000);
          }
        }
      }
    }
  }

  public void insertAt(Context context, Stella_Object newvalue) {
    { CsValue self = this;

      if (self.theKvList == null) {
        { KvCons kvcons = KvCons.newKvCons();

          kvcons.key = context;
          kvcons.value = newvalue;
          self.theKvList = kvcons;
          return;
        }
      }
      KvCons.helpInsertACsValue(self.theKvList, newvalue, context, true);
    }
  }

  public Surrogate primaryType() {
    { CsValue self = this;

      return (Stella.SGT_STELLA_CS_VALUE);
    }
  }

}

