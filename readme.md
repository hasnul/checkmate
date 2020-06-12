Checkmate
=========

Check the behaviour of a collection of chess engines against the expectations of
the python-chess library.

Some engines don't play nicely with python-chess. Checkmate attempts to 
detect these engines, so that we can blame someone... The program does not 
check that any executables that it finds are actually chess engines before
spawning them. It is strongly recommended to run this program in a sandbox 
or virtual machine. On windows, scan all executables for bad stuff prior to
executing.

Todo
----

- Detect protocol
- Get engine id
- Detect "standard" options
- Identify any extra options
- Adjudicate threefold repetition
- Record if engine erred

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


