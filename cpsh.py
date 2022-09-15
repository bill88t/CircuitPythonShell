#!/usr/bin/python -u

"""
CircuitPythonShell, by bill88t.
Or as it should better be called, wanna-be ssh.
"""

major = __import__("sys").implementation.version.major
if major != 3:
    print("This utility requires python3")
    exit(1)
del major

try:
    from websocket import create_connection as __create_connection__
except ImportError:
    print(
        'Please install websocket-client first.\nCommand: "pip3 install websocket-client"'
    )
    exit(1)

from sys import argv as __argv__
from sys import stdin as __stdin__
from sys import stdout as __stdout__
from base64 import b64encode as __b64__
from select import select as __select__
from os import system as __system__
from tty import setcbreak as __setcbreak__
import termios as __termios__
from multiprocessing import Process as __Process__
from multiprocessing import Queue as __Queue__


def __isData__():
    return __select__([__stdin__], [], [], 0) == ([__stdin__], [], [])


version = "0.1"

__verbose__ = False
__ip__ = None
__passwd__ = None
__ws__ = None


def __wsget__(q):
    try:
        global __ws__
        q.put(__ws__.recv())
    except KeyboardInterrupt:
        q.put(0)


def cpsh(ip, passwd):
    sf = __b64__(bytes(":" + passwd, "utf-8"))
    if __verbose__:
        print("Connecting..")
    try:
        global __ws__
        __ws__ = __create_connection__(
            f"ws://{ip}/cp/serial/",
            header={"Authorization": "Basic " + str(sf, "utf-8")},
        )
    except OSError:
        print("Error: Could not connect to board.")
        exit(1)
    if __verbose__:
        print("Connected.")
    del sf, passwd, ip

    old_settings = __termios__.tcgetattr(__stdin__)
    __system__("stty -echo")
    __setcbreak__(__stdin__.fileno())
    try:
        while True:
            q = __Queue__()
            rec_thd = __Process__(target=__wsget__, name="ws_getter", args=(q,))
            try:
                rx = ""
                while __isData__():
                    rx += str(__stdin__.read(1))
                if rx != "":
                    # __ws__.send(rx)
                    pass
                del rx
                rec_thd.start()
                rec_thd.join(timeout=0.03)
                rec_thd.terminate()
                if not q.empty():
                    dat = q.get()
                    if isinstance(dat, str):
                        __stdout__.write(dat)
                    else:
                        break
                    del dat
            except KeyboardInterrupt:
                rec_thd.terminate()
                break
            del rec_thd
            __stdout__.flush()
    except Exception as err:
        print(str(err))
    __system__("stty echo")
    __termios__.tcsetattr(__stdin__, __termios__.TCSADRAIN, old_settings)
    del old_settings

    if __verbose__:
        print("Closing connection..")

    __ws__.close()

    if __verbose__:
        print("Closed connection. Bye.")


if __name__ == "__main__":
    args = __argv__[1:]
    helpstr = (
        f"CircuitPythonShell version {version}\n"
        + "Usage: cpsh.py [ARGS] [BOARD IP]\n\n"
        + "Arguments:\n\n"
        + "   -v, --verbose  : Be more verbose\n"
        + '   -p, --password : Specify the password (-p="amogus")\n'
    )
    if len(args) > 0:
        for i in args:
            if i in ["-v", "--verbose"]:
                __verbose__ = True
            elif i.startswith("-p=") or i.startswith("--password="):
                __passwd__ = i[i.find("=") + 1 :]
        if not args[-1].startswith("-"):
            __ip__ = args[-1]
            if __passwd__ is not None:
                cpsh(__ip__, __passwd__)
        else:
            print("Error, no board ip specified.\n")
            print(helpstr)
    else:
        print(helpstr)
    del helpstr, args
