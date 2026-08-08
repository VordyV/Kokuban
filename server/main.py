# Kokuban server developed by VordyV aka Vladislav Netievsky
# The program acts as a server for Kokuban Speaker

import sys
import argparse
import kokuban_server
from kokuban_server import KokubanServer
from loguru import logger
from prompt_toolkit.patch_stdout import StdoutProxy


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='kokuban.exe', description=f'Kokuban server v{kokuban_server.__version__} for the Kokuban Speaker client', epilog=f'Developed by VordyV aka Vladislav Netievsky')
    parser.add_argument('--tcpservaddr', help="TCP server address", default="127.0.0.1")
    parser.add_argument('--tcpservport', help="TCP server port", type=int, default=8080)
    parser.add_argument('--httpservaddr', help="HTTP server address", default="127.0.0.1")
    parser.add_argument('--httpservport', help="HTTP server port", type=int, default=80)
    parser.add_argument('--loglevel', help="Logging level. The level from which information will be output to the console", default="INFO")

    args = parser.parse_args()

    logger.remove()
    logger.add(StdoutProxy(raw=True), format="[{time:HH:mm:ss}] {level}: {message}", level=args.loglevel, colorize=True, enqueue=True)
    logger.add("{time:YYYY-MM-DD}.log", enqueue=True, rotation="03:00")

    ks = KokubanServer(address_tcp=args.tcpservaddr, port_tcp=args.tcpservport, address_http=args.httpservaddr, port_http=args.httpservport)
    ks.start()