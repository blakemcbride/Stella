;;; -*- Mode: Lisp; Package: CL-USER; Syntax: COMMON-LISP; Base: 10 -*-

;;;;;;;;;;;;;;;;;;;;;;;;;;;; BEGIN LICENSE BLOCK ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;                                                                            ;
; Version: MPL 1.1/GPL 2.0/LGPL 2.1                                          ;
;                                                                            ;
; The contents of this file are subject to the Mozilla Public License        ;
; Version 1.1 (the "License"); you may not use this file except in           ;
; compliance with the License. You may obtain a copy of the License at       ;
; http://www.mozilla.org/MPL/                                                ;
;                                                                            ;
; Software distributed under the License is distributed on an "AS IS" basis, ;
; WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License   ;
; for the specific language governing rights and limitations under the       ;
; License.                                                                   ;
;                                                                            ;
; The Original Code is the STELLA Programming Language.                      ;
;                                                                            ;
; The Initial Developer of the Original Code is                              ;
; UNIVERSITY OF SOUTHERN CALIFORNIA, INFORMATION SCIENCES INSTITUTE          ;
; 4676 Admiralty Way, Marina Del Rey, California 90292, U.S.A.               ;
;                                                                            ;
; Portions created by the Initial Developer are Copyright (C) 1996-2019      ;
; the Initial Developer. All Rights Reserved.                                ;
;                                                                            ;
; Contributor(s):                                                            ;
;                                                                            ;
; Alternatively, the contents of this file may be used under the terms of    ;
; either the GNU General Public License Version 2 or later (the "GPL"), or   ;
; the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),   ;
; in which case the provisions of the GPL or the LGPL are applicable instead ;
; of those above. If you wish to allow use of your version of this file only ;
; under the terms of either the GPL or the LGPL, and not to allow others to  ;
; use your version of this file under the terms of the MPL, indicate your    ;
; decision by deleting the provisions above and replace them with the notice ;
; and other provisions required by the GPL or the LGPL. If you do not delete ;
; the provisions above, a recipient may use your version of this file under  ;
; the terms of any one of the MPL, the GPL or the LGPL.                      ;
;                                                                            ;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;; END LICENSE BLOCK ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;


;;; Lisp pathname translations for STELLA and related systems.
;;; Now assumes STELLA has been loaded before this file gets loaded.
;;; OBSOLETE: not needed or used anymore, but kept for now just in case.

(in-package "CL-USER")


;;  Use the pathname functions to avoid having to deal with
;;  different directory separators and other idiosyncratic
;;  handling of filenames across platforms.

(defparameter *stella-root-directory*
  (butlast (pathname-directory *stella-source-directory*) 2))

(defparameter *stella-logical-host-name*
    (stella::get-logical-host-name stella::*rootSourceDirectory*))

(let* ((default-source *load-truename*)
       ;; check if this Lisp allows :wild as a version value (e.g., ACL 5.0 doesn't):
       (wild-version-value
	(if (ignore-errors (make-pathname :version :wild :defaults default-source))
	    :wild
	  nil)))
  (flet ((create-pathname-pattern (root &rest subs)
	   (make-pathname :directory (append root subs '(:wild-inferiors))
			  :name :wild :type :wild :version wild-version-value
			  :defaults default-source))
	 (create-directory-pattern (root &rest subs)
	   (make-pathname :directory (append root subs '(:wild-inferiors))
			  :name nil :type nil :version nil
			  :defaults default-source)))
    ;; try to figure out dynamically whether the current Lisp/OS
    ;;    combination needs a separate directory-only translation rule:
    (let* ((directory-test-temp
	    (ignore-errors
	      (progn (setf (logical-pathname-translations *stella-logical-host-name*)
			   `(("sources;**;*.*.*" 
			      ,(create-pathname-pattern
				*stella-root-directory* "sources"))))
		     (namestring
                      (translate-logical-pathname
                       (concatenate 'string *stella-logical-host-name* ":sources;"))))))
	   (needs-directory-rule?
	    (or (null directory-test-temp)
		(char= #\* (char directory-test-temp 
				 (1- (length directory-test-temp)))))))
      (setf (logical-pathname-translations *stella-logical-host-name*)
	    `(("sources;**;*.*.*" ,(create-pathname-pattern
				    *stella-root-directory* "sources"))
	      ("native;**;*.*.*" ,(create-pathname-pattern
				   *stella-root-directory* "native"))
	      ("bin;**;*.*.*" ,(create-pathname-pattern
				*stella-root-directory* "native" "lisp" "bin"
				*stella-binary-subdirectory*))
	      ("kbs;**;*.*.*" ,(create-pathname-pattern
				*stella-root-directory* "kbs"))
	      ("**;*.*.*" ,(create-pathname-pattern *stella-root-directory*))))
      (when needs-directory-rule?
	(setf (logical-pathname-translations *stella-logical-host-name*)
	      (append `(("sources;**;" ,(create-directory-pattern
					 *stella-root-directory* "sources"))
			("native;**;" ,(create-directory-pattern
					*stella-root-directory* "native"))
			("bin;**;" ,(create-directory-pattern
				     *stella-root-directory* "native" "lisp" "bin"
				     *stella-binary-subdirectory*))
			("kbs;**;" ,(create-directory-pattern
				     *stella-root-directory* "kbs"))
			("**;" ,(create-directory-pattern *stella-root-directory*)))
		      (logical-pathname-translations *stella-logical-host-name*)))) )))
