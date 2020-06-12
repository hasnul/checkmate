Checkmate
=========

Check the behaviour of a collection of chess engines against the expectations of
the python-chess library.


Pseudocode
----------

1. Find all engine targets 
    1.1 Estimate run time
    1.2 Estimate disk space required for logs
    1.3 Estimate current cpu usage and available memory
2. For each engine
    2.1 Detect protocol
    2.2 Get engine id
    2.3 Detect "standard" options
    2.4 Identify any extra options
    2.5 Run gauntlet
        2.5.1 Adjudicate threefold repetition
        2.5.2 Record if engine erred
        2.5.3 Stop if max plies exceeded
        2.5.4 Detect engine successfully killed
            2.5.4.1 If engine still alive --> add to blacklist
    2.6 Check system health --> cpu usage and available memory
3. Produce a report output to stdout

UCI Engine Behaviour
--------------------
Typically a uci engine offers
- Threads
- Hash
- Tablebases

XBoard Engine Behaviour
-----------------------
An XBoard engine should
- respond correctly to "rejected usermove"

Usage
-----
Usage:
checkmate [options] targets

Optional command line arguments:

targets: A set of engine executables or the base directory of an engine collection.
If not provided use current dir.

-y Don't ask to continue
-l (log) error/debug/none?
-s (subfolder) search for engines in subfolders; goes one level deeper only
-c (collate) yes/no : separate log files or single collated log
-p (protocol) uci/xboard : choose engine type; if not provided do any type 
-b (blacklist) Don't run any engine in this blacklist file
-g (generate) generate blacklist of engines that refuse to die on command
-m (monitor) monitor system health so we don't run out of cpu and memory; cpu usage and
    memory usage is estimated at start; to function correctly don't run any other
    computationally intensive process in parallel.
-v (version)
--lib use a specially tailored version of the python-chess library

