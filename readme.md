Checkmate
=========

Status
------
Attempt at cheap hack in this branch is not working.

Intro
-----
Check the behaviour of a collection of chess engines against the expectations of
the python-chess library.

Some engines don't play nicely with python-chess. Checkmate attempts to 
detect these engines, so that we can blame someone... The program does not 
check that any executables that it finds are actually chess engines before
spawning them. It is strongly recommended to run this program in a sandbox 
or virtual machine. On windows, scan all executables for bad stuff prior to
executing.

XBoard v1 Engine Notes
-----------------------
Faile 
* does not work appear to work correctly in fixed time mode, i.e. 'st'. Tested in xboard
  gui.
* engine match with sf11 works fine. Tested using cutechess-cli at 40/1:0.

Phalanx
* works at st=1 in xboard gui
* engine match using cutechess-cli working at 40/1:0
