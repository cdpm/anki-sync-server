#!/usr/bin/env python

from __future__ import print_function

import os
import sys
import signal
import subprocess
import getpass

from AnkiServer.user_managers import SqliteUserManager

SERVERCONFIG = "production.ini"
AUTHDBPATH = "auth.db"
PIDPATH = "/tmp/ankiserver.pid"
COLLECTIONPATH = "collections/"

def usage():
    print("usage: "+sys.argv[0]+" <command> [<args>]")
    print()
    print("Commands:")
    print("  start [configfile] - start the server")
    print("  debug [configfile] - start the server in debug mode")
    print("  stop               - stop the server")
    print("  adduser <username> - add a new user")
    print("  deluser <username> - delete a user")
    print("  lsuser             - list users")
    print("  passwd <username>  - change password of a user")

def startsrv(configpath, debug):
    if not configpath:
        configpath = SERVERCONFIG

    # We change to the directory containing the config file
    # so that all the paths will be relative to it.
    configdir = os.path.dirname(configpath)
    if configdir != '':
        os.chdir(configdir)
    configpath = os.path.basename(configpath)

    if debug:
        # Start it in the foreground and wait for it to complete.
        subprocess.call( ["paster", "serve", configpath], shell=False)
        return

    devnull = open(os.devnull, "w")
    pid = subprocess.Popen( ["paster", "serve", configpath],
                            stdout=devnull,
                            stderr=devnull).pid

    with open(PIDPATH, "w") as pidfile:
        pidfile.write(str(pid))

def stopsrv():
    if os.path.isfile(PIDPATH):
        try:
            with open(PIDPATH) as pidfile:
                pid = int(pidfile.read())

                os.kill(pid, signal.SIGKILL)
                os.remove(PIDPATH)
        except Exception as error:
            print("{}: Failed to stop server: {}"
                  .format(sys.argv[0], error.message), file=sys.stderr)
    else:
        print("{}: The server is not running".format(sys.argv[0]),
              file=sys.stderr)

def adduser(username):
    if username:
        print("Enter password for {}".format(username))
        password = getpass.getpass()

        user_manager = SqliteUserManager(AUTHDBPATH, COLLECTIONPATH)
        user_manager.add_user(username, password)
    else:
        usage()

def deluser(username):
    if username and os.path.isfile(AUTHDBPATH):
        user_manager = SqliteUserManager(AUTHDBPATH, COLLECTIONPATH)

        try:
            user_manager.del_user(username)
        except ValueError as error:
            print("Could not delete user {}: {}"
                  .format(username, error.message), file=sys.stderr)
    elif not username:
        usage()
    else:
        print("{}: Database file does not exist".format(sys.argv[0]),
              file=sys.stderr)

def lsuser():
    user_manager = SqliteUserManager(AUTHDBPATH, COLLECTIONPATH)
    try:
        users = user_manager.user_list()
        for username in users:
            print(username)
    except ValueError as error:
        print("Could not list users: {}".format(AUTHDBPATH, error.message),
              file=sys.stderr)

def passwd(username):
    if os.path.isfile(AUTHDBPATH):
        print("Enter password for {}:".format(username))
        password = getpass.getpass()

        user_manager = SqliteUserManager(AUTHDBPATH, COLLECTIONPATH)
        try:
            user_manager.set_password_for_user(username, password)
        except ValueError as error:
            print("Could not set password for user {}: {}"
                  .format(username, error.message), file=sys.stderr)
    else:
        print("{}: Database file does not exist".format(sys.argv[0]),
              file=sys.stderr)

def main():
    argc = len(sys.argv)
    exitcode = 0

    if argc < 2:
        usage()
        exitcode = 1
    else:
        if argc < 3:
            sys.argv.append(None)

        if sys.argv[1] == "start":
            startsrv(sys.argv[2], False)
        elif sys.argv[1] == "debug":
            startsrv(sys.argv[2], True)
        elif sys.argv[1] == "stop":
            stopsrv()
        elif sys.argv[1] == "adduser":
            adduser(sys.argv[2])
        elif sys.argv[1] == "deluser":
            deluser(sys.argv[2])
        elif sys.argv[1] == "lsuser":
            lsuser()
        elif sys.argv[1] == "passwd":
            passwd(sys.argv[2])
        else:
            usage()
            exitcode = 1

    sys.exit(exitcode)

if __name__ == "__main__":
    main()
