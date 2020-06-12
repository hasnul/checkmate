#!/usr/bin/env python3

import argparse 
import os
import logging
import chess
import chess.engine
import asyncio

__version__ = "0.0.4"
MAX_PLIES = 160
MAX_TIME = 0.1 #seconds
BYTES_PER_LINE = 1024 #useless, depends on speed, egtb, threads, etc.
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
        exes.update([f for f in candidates if os.access(f, os.X_OK)])
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
            if os.access(target, os.X_OK):
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

def detect_protocol(command):
    """Attempt to detect the protocol used by an engine."""
    try:
        engine = chess.engine.SimpleEngine.popen_uci(command)
        engine.quit()
        protocol = chess.engine.UciProtocol 
    except asyncio.exceptions.TimeoutError:
        try:
            engine = chess.engine.SimpleEngine.popen_xboard(command)
            engine.quit()
            protocol = chess.engine.XBoardProtocol
        except:
            protocol = None
    return protocol
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='checkmate', description=
            """Check engine `compliance` against python-chess.
            Some engines don't play nicely with python-chess. %(prog)s attempts to 
            detect these engines, so that we can blame someone... The program does not 
            check that any executables that it finds are actually chess engines before
            spawning them. It is strongly recommended to run this program in a sandbox 
            or virtual machine. On windows, scan all executables for bad stuff prior to
            executing %(prog)s.""")
    parser.add_argument('-b', dest='blacklist', action='store_true',
            help="don't run any engine listed in a file called blacklist")
    parser.add_argument('-c', dest='collate', action='store_true', 
            help='collate engine logs into a single log file; clobber old log')
    parser.add_argument('--cpu', metavar='maxcpu', type=int, default=0, 
            help="cpu usage (%%) maximum allowed; assumes majority cpu cycles consumed by " + 
            "itself and subprocesses spawned")
    parser.add_argument('-f', dest='enginelist', metavar='enginelist',
            help='file containing list of relative paths to engine programs; ' + 
            'use in conjunction with base directory specified in main argument: targets')
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
    parser.add_argument('targets', nargs='+', help=
            'engine(s) to test or base directory where they live')
    parser.add_argument('-s', dest='subfolder', action='store_true', 
            help='include subfolders, one level deep, in engine search')
    parser.add_argument('-v', '--version', action='version', version=
            f'%(prog)s {__version__}')
    parser.add_argument('-x', metavar="exclude_file", help=
            "exclude the programs and subfolders listed in an exclude file.")
    parser.add_argument('-y', dest='askuser', action='store_false', 
            help="yes to continue prompt, i.e. don't ask user just run")

    args = parser.parse_args()
    paths = get_enginepaths(args.targets, args.subfolder)
    if not paths:
        print("No engines found")
        exit()

    runtime = MAX_TIME*MAX_PLIES*args.numiter*len(paths)/60
    print(f'Estimated worst-case run time = {runtime:.1f} minutes')
    #diskspace = MAX_PLIES*len(paths)*args.numiter*BYTES_PER_LINE/(1024*1024)
    #print(f'Estimated worst-case disk space = {diskspace:.2f} MB')
    print(f'Found {len(paths)} potential chess engines:')
    for p in paths:
        print(p)

    if args.askuser:
        answer = input('Continue? (Y/n) ').lower()
        if answer not in ['yes', 'y', '']:
            exit()

    for engine_path in paths:
        print(f'Testing executable: {engine_path}')
        protocol = detect_protocol(engine_path)
        if protocol == chess.engine.UciProtocol:
            engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        elif protocol == chess.engine.XBoardProtocol:
            engine = chess.engine.SimpleEngine.popen_xboard(engine_path)
        else:
            print(f'Unknown protocol used by {engine_path} -- skipping')
            continue

        try:
            engine.configure({'Threads': 1})
        except:
            logging.debug(f'Engine {engine.id["name"]} has no Threads option')
        ply_count = 0
        board = chess.Board()
        while not board.is_game_over() and ply_count < MAX_PLIES:
            result = engine.play(board, chess.engine.Limit(time=MAX_TIME))
            board.push(result.move)
            ply_count += 1
        engine.quit()
