# STELLA Programming Language

This document describes STELLA 3.6 or later.

STELLA is a strongly typed, object-oriented, Lisp-like language,
designed to facilitate symbolic programming tasks in artificial
intelligence applications. STELLA preserves those features of Common
Lisp deemed essential for symbolic programming such as built-in
support for dynamic data structures, heterogeneous collections,
first-class symbols, powerful iteration constructs, name spaces, an
object-oriented type system with a meta-object protocol, exception
handling, and language extensibility through macros, but without
compromising execution speed, interoperability with non-STELLA
programs, and platform independence. STELLA programs are translated
into a target language such as C++, Common Lisp, or Java, and then
compiled with the native target language compiler to generate
executable code. The language constructs of STELLA are restricted to
those that can be translated directly into native constructs of the
intended target languages, thus enabling the generation of highly
efficient as well as readable code.

For more documentation on STELLA please see the STELLA manual
available from the [STELLA web site](http://www.isi.edu/isd/LOOM/Stella/)
and also included with the release, in the directory `sources/stella/doc/`.


## Installation

### System Requirements

To install and use STELLA you'll approximately need the following
amounts of disk space:

   * 8 MB for the tar-red or zip-ped archive file

   * 35 MB for the untarred sources, tanslations, compiled Java files
     and documentation

   * 8 MB to compile a Lisp version

   * 11 MB to compile the C++ version (without -g)

   * 3 MB to compile the Java version (already included)

This means that you will need approximately 55 MB to work with one
Lisp, one C++ and one Java version of STELLA in parallel.  If you also
want to experiment with the Lisp translation variant that uses
structures instead of CLOS instances to implement STELLA objects, then
you will need an extra 8 MB to compile that.

The full STELLA development tree is quite large, since for every
STELLA source file there are three to four translated versions and as
many compiled versions thereof.  The actual STELLA libraries that you
have to ship with an application, however, are quite small.  For
example, the Java jar file `stella.jar` is only about 1.3 MB in size.
The dynamic C++ library `libstella.so` compiled on a Linux platform is
about 4 MB.  Additionally, if you don't need all the different
translations of STELLA, you can delete some of the versions to keep your
development tree smaller (See Removing Unneeded Files).

To run the Lisp version of STELLA you need an ANSI Common-Lisp (or at
least one that supports CLOS and logical pathnames).  We have
successfully tested STELLA with Allegro-CL 4.2, 4.3, 5.0, 6.0 and 7.0,
Macintosh MCL 3.0, 4.0 and 5.1, OpenMCL 1.0, SBCL 0.9.4, CMUCL 19c,
LispWorks 4.4.6, CLisp 2.37, Lucid CL 4.1 (plus the necessary ANSI
extensions and Mark Kantrowitz's logical pathnames implementation) and
various others.  Our main development platform is Allegro CL running
under Sun Solaris and Linux, so, the closer your environment is to ours,
the higher are the chances that everything will work right out of the
box.  Lisp development under Windows should also be no problem.

To run the C++ version of STELLA you need a C++ compiler such as g++
that supports templates and exception handling.  We have successfully
compiled and run STELLA with g++ 3.2 and later under Linux Redhat 8.0 &
9.0, SunOS and MacOS X, and with CygWin 5.0 and MinGW 5.0 under Windows
2000 and XP.  Both CygWin and MinGW provide a GNU Unix environment, but
MinGW can generate Windows executables that are fully standalone.  We've
also managed to compile STELLA under MS Visual C++, however, we never
got the Boehm garbage collector to work.  The GC claims to be very
portable, so this should be solvable for somebody with good knowledge of
MS Visual C++.

For the Java version you will need Java JDK 1.6 or later. We've run the
Java version of STELLA on a variety of platforms without any problems.

Any one of the Lisp, C++ or Java implementations of STELLA can be
used to develop your own STELLA code and translate it into all three
languages, but the most convenient development environment is the one
based on Lisp.  If you use the C++ or Java version, translating and
using your own STELLA macros is possible but not yet very well
supported.


### Unpacking the Sources

Uncompress and untar the file `stella-X.Y.Z.tar.gz` (or unzip the file
`stella-X.Y.Z.zip`) in the parent directory of where you want to
install STELLA (`X.Y.Z` are place holders for the actual version
numbers).  This will create the STELLA tree in the directory
`stella-X.Y.Z/`.  All pathnames mentioned below will be relative to that
directory which we will usually refer to as the "STELLA directory".


### Lisp Installation

To install the Lisp version startup Lisp and load the file
`load-stella.lisp` with:

        (CL:load "load-stella.lisp")

The first time around this will compile all Lisp-translated STELLA
files before they are loaded.  During subsequent sessions the compiled
files will be loaded right away.

If you want to use the version that uses Lisp structs instead of CLOS
objects to implement STELLA objects do the following:

        (CL:setq cl-user::*load-cl-struct-stella?* CL:t)
        (CL:load "load-stella.lisp")

Alternatively, you can edit the initial value of the variable
`*load-cl-struct-stella?*` in the file `load-stella.lisp`.  Using
structs instead of CLOS objects greatly improves slot access speed,
however, it may cause problems with incremental re-definition of STELLA
classes.  It is therefore recommended to only use this for systems that
are in or near the production stage.

Once all the files are loaded, you should see a message like this:

        Initializing STELLA...
        STELLA 3.6.0 loaded.
        Type `(in-package "STELLA")` to execute STELLA commands.
        CL-USER(2):

To reduce startup time, you might want to create a Lisp image that
has all of STELLA preloaded.

Now type
   
        (in-package "STELLA")

to enter the `STELLA` Lisp package where all the STELLA code resides.

**IMPORTANT**: All unqualified Lisp symbols in this document are
assumed to be in the `STELLA` Lisp package.  Moreover, the `STELLA`
package does **NOT** inherit anything from the `COMMON-LISP` package (see
the file `sources/stella/cl-lib/cl-setup.lisp` for the few exceptions),
hence, you have to explicitly qualify every Lisp symbol you want to use
with `CL:`.  For example, to get the result of the previous evaluation
you have to type `CL:*` instead of `*`.


### C++ Installation

To compile the C++ version of STELLA change to the native C++ directory
and run `make`:

        % cd native/cpp/stella
        % make

This will compile all STELLA files, the garbage collector and
generate a static or dynamic `libstella` library file in the directory
`native/cpp/lib` which can later be linked with your own C++-translated
STELLA (or other) code.  To test whether the compilation was successful
you can run STELLA from the top-level STELLA directory using the
`stella` script (or `stella.bat` under a Windows command prompt):

        % stella c++
        Running C++ version of STELLA...
        Running kernel startup code...
        Initializing symbol tables...
        Initializing quoted constants...
        Initializing global variables...
        Creating class objects...
        Finalizing classes...
        Creating method objects...
        Finalizing methods...
        Running non-phased startup code...
        Starting up translators...
        Welcome to STELLA 3.6.0
        Bye!

This will simply run various STELLA startup code and exit.  See the
`stella` script to see how you can use the STELLA C++ executable
to translate STELLA code.  The `c++` argument tells the script to run
the C++ version of STELLA.  If the argument is omitted and the C++
version is installed, it will be run automatically.  Otherwise, the Java
version will be run.


### Java Installation

Nothing needs to be done to install the Java version.  Since Java class
files are platform independent, they are already shipped with the STELLA
distribution and can be found in the directory `native/java` and its
subdirectories.  Additionally, they have been collected into the file
`native/java/lib/stella.jar`.  To try out the Java version of STELLA
run the `stella` script in the STELLA directory:

        % stella java
        Running Java version of STELLA...
        Running kernel startup code...
        Initializing symbol tables...
        Initializing quoted constants...
        Initializing global variables...
        Creating class objects...
        Finalizing classes...
        Creating method objects...
        Finalizing methods...
        Running non-phased startup code...
        Starting up translators...
        Welcome to STELLA 3.6.0
        Bye!

Similar to the C++ executable, this will simply run various STELLA
startup code and exit.  See the `stella` script to see how you can
use the STELLA Java executable to translate STELLA code.


### Emacs Setup

STELLA development is very similar to Lisp development, and it is best
done in an X/Emacs-based Lisp development environment such as the
Allegro-CL Emacs interface plus Allegro Composer, or ILISP.  If you do
use X/Emacs with the Allegro CL interface, add the following to your
`.emacs` or `.xemacs/init.el` file:

        (setq auto-mode-alist
              (cons '("\\.ste$" . fi:common-lisp-mode) auto-mode-alist))

If you are using the Allegro CL interface, you might want to install
the file `tools/fi-stella.el`, since it sets up proper indentation for
STELLA code and makes looking up STELLA definitions via the `C-c .` or
`M-.` commands work better.  Look at the file `tools/fi-stella.el` for
specific installation instructions.


### Removing Unneeded Files

To save disk space you can remove files that you don't need.  For
example, if you are not interested in the C++ version of STELLA, you can
delete the directory `native/cpp`.  Similarly, you can remove
`native/java` to eliminate all Java-related files.  You could do the
same thing for the Lisp directory `native/lisp`, but (in our opinion)
that would make it less convenient for you to develop new STELLA code.
Finally, if you don't need any of the STELLA sources, you can delete
the directory `sources/stella`.  If you don't need local copies of the
STELLA documentation, you can delete parts or all of the
`sources/stella/doc` directory.


## Questions and Comments

Please send mail to Hans Chalupsky (hans AT isi.edu).
