#!/usr/bin/env python3

import argparse 
import os
import logging
import chess
import chess.engine
import asyncio
import sys
import prober

__version__ = "0.0.6"

MAX_PLIES = 160
MAX_TIME = 0.1 #seconds
MAX_THREADS = 4

logging.basicConfig(filename='checkmate.log', level=logging.DEBUG)

def get_exec(folder):
    """
    Return a set of all the executables in the folder and a list of the names of all  
    subfolders.
    """
    exes = set() 
    try:
        basepath, subnames, filenames = next(os.walk(folder))
        candidates = [os.path.join(basepath, f) for f in filenames]
        exes.update([f for f in candidates if is_executable(f)])
    except StopIteration:
        pass
    if subnames:
        return exes, subnames 
    else:
        return exes, None

def get_enginepaths(targets, include_subdir):
    """Return a set of full engine paths that will be used to spawn engines."""

    engine_paths = set() 
    for target in targets:
        target = os.path.expanduser(target)
        target = os.path.expandvars(target)
        target = os.path.abspath(target)
        if not os.path.exists(target):
            print(f'{target} does not exist.')
            return
        if os.path.isfile(target):
            if is_executable(target):
                engine_paths.add(target)
        else:
            exefiles, subfolders = get_exec(target)
            engine_paths.update(exefiles)
            if include_subdir and subfolders:
                for subfolder in subfolders:
                    subpath = os.path.join(target, subfolder)
                    sub_exes, _ = get_exec(subpath)
                    engine_paths.update(sub_exes)
    return engine_paths

def is_executable(filepath):
    """
    Determine if a file at filepath is executable. If the OS is posix then
    it will use the os.access method. For windows, it assumes that executables
    used by engines are files that end with the extension '.exe' or '.bat'.
    """
    if os.name == "posix":
        return os.access(filepath, os.X_OK)
    elif sys.platform == "win32":
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.exe' or ext == '.bat':
            return True
        else:
            return False
    else:
        sys.exit("Fatal error: I have no idea what OS this is. trigger grammar nazi")

def detect_protocol(command):
    """Attempt to detect the protocol used by an engine."""
    detector = prober.popen_probe(command)
    return asyncio.run(detector) 
    
def set_threads(engine, numthreads: int):
    """
    Configure the number of threads or 'cores' for the engine based on protocol.
    """
    if numthreads <= 0 or numthreads > MAX_THREADS:
        logging.warn(f'Invalid demand for {numthreads} threads. Ignoring.')
        return
    if engine.protocol == chess.engine.UciProtocol:
        if "Threads" in engine.options:
            engine.configure({'Threads': numthreads})
        else:
            logging.warn(f'Engine {engine.id["name"]} has no Threads option')
    elif engine.protocol == chess.engine.XBoardProtocol:
        if "cores" in engine.options:
            engine.configure({'cores': numthreads})
        else:
            logging.warn(f'Engine {engine.id["name"]} has no cores option')

def getpaths_fromfile(filename):
    """
    Retrieve the engine path names from a file. It also checks that the path
    exists. If any path specified in the file cannot be found, it skips that path 
    and prints a warning message to stdout.  A line must be an absolute path
    to an executable file, otherwise it is skipped.
    """
    paths = set()
    try:
        enginefile = open(filename, 'r')
    except FileNotFoundError:
        print(f'The file "{filename}" was not found.')
    except IOError:
        print('I/O exception')
    else:
        with enginefile:
            for line in enginefile:
                line = line.splitlines()[0]
                if os.path.isabs(line):
                    if os.path.exists(line):
                        if is_executable(line):
                            paths.add(line)
                        else:
                            print(f'{line} is not executable. Skipping')
                    else:
                        print(f'{line} not found. Skipping')
                else:
                    print(f'{line} is not an absolute path. Skipping')
    return paths

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='checkmate', description=
            """Check engine `compliance` against python-chess.
            Some engines don't play nicely with python-chess. %(prog)s attempts to 
            detect these engines, so that we can blame someone... The program does not 
            check that any executables that it finds are actually chess engines before
            spawning them. It is strongly recommended to run this program in a sandbox 
            or virtual machine. On Windows, scan all executables for bad stuff prior to
            executing %(prog)s.""")
    parser.add_argument('targets', nargs='*', help=
            'engine(s) to test or base directory where they live')
    parser.add_argument('-b', dest='blacklist', action='store_true',
            help="don't run any engine listed in a file called blacklist")
    parser.add_argument('-c', dest='collate', action='store_true', 
            help='collate engine logs into a single log file; clobber old log')
    parser.add_argument('--cpu', metavar='maxcpu', type=int, default=0, 
            help="cpu usage (%%) maximum allowed; assumes majority cpu cycles consumed by " + 
            "itself and subprocesses spawned")
    parser.add_argument('-d', dest='dump', action='store_true',
            help="dump the list of executatbles found to stdout and quit immediately")
    parser.add_argument('-f', dest='enginelist', metavar='enginelist',
            help='file containing list of absolute paths to engine programs; ' + 
            'ignores targets argument')
    parser.add_argument('-g', dest='gen_blacklist', action='store_true',
            help="generate or appends to the blacklist file, engines that refuse to die")
    parser.add_argument('-i', dest='numiter', type=int, default=1, metavar='numiter',
            help='how many iterations to run for each engine; default is one')
    parser.add_argument('--lib', metavar='libfolder', 
            help="folder containing the python-chess library")
    parser.add_argument('--mem', metavar='maxmem', help="memory usage (GB) maximum allowed" +
            "; assumes no other programs running in parallel will consume memory",
            type=int, default=0)
    parser.add_argument('-p', dest='protocol', choices=['uci', 'xboard', 'both'],
            default='both',
            help='protocol to test; default is both; xboard covers both versions')
    parser.add_argument('-s', dest='subfolder', action='store_true', 
            help='include subfolders, one level deep, in engine search')
    parser.add_argument('-v', '--version', action='version', version=
            f'%(prog)s {__version__}')
    parser.add_argument('-x', metavar="exclude_file", help=
            "exclude the programs and subfolders listed in an exclude file.")
    parser.add_argument('-y', dest='askuser', action='store_false', 
            help="yes to continue prompt, i.e. don't ask user just run")

    args = parser.parse_args()
    if not args.targets and not args.enginelist:
        print("Neither targets nor enginelist file (-f) specified.")
        exit()

    if args.enginelist:
        paths = getpaths_fromfile(args.enginelist)
    else:
        paths = get_enginepaths(args.targets, args.subfolder)

    if not paths:
        print("No engines found")
        exit()

    paths = sorted(paths, key=str.casefold)
    if args.dump:
        for p in paths:
            print(p)
        exit()

    runtime = MAX_TIME*MAX_PLIES*args.numiter*len(paths)/60
    print(f'Estimated worst-case run time = {runtime:.1f} minutes')
    print(f'Found {len(paths)} potential chess engines:')
    for p in paths:
        print(p)

    if args.askuser:
        answer = None
        valid_responses = ['yes', 'y', 'no', 'n',  '']
        while answer not in valid_responses:
            answer = input('Continue? [Y]/n ').lower()
        if answer not in ['yes', 'y', '']:
            exit()

    for engine_path in paths:
        protocol = detect_protocol(engine_path)
        if protocol == chess.engine.UciProtocol:
            print(f'Testing uci engine at: {engine_path}')
            engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        elif protocol == chess.engine.XBoardProtocol:
            print(f'Testing xboard engine at: {engine_path}')
            engine = chess.engine.SimpleEngine.popen_xboard(engine_path)
        else:
            print(f'Unknown protocol used by {engine_path} -- skipping')
            continue
        
        set_threads(engine, 1)
        ply_count = 0
        board = chess.Board()
        engine_name = engine.id["name"]
        while not board.is_game_over() and ply_count < MAX_PLIES:
            try:
                result = engine.play(board, chess.engine.Limit(time=MAX_TIME))
            except chess.engine.EngineTerminatedError:
                logging.error(f'Engine {engine_name} died during play.')
                break
            board.push(result.move)
            ply_count += 1
        if engine:
            engine.quit()
