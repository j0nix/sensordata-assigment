import sys, subprocess, socket, os, time, logging, string, random
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter

""" Generator wrapper. Send sensor data output with UDP over port 10514 """

__author__ = "Jon Svendsen"
__version__ = "1.0"
epilog = """

Example)
   python {} -s 3
______________________________________

"""

## Argument parser setup
parser = ArgumentParser(
    formatter_class=RawTextHelpFormatter,
    description=__doc__,
    epilog=epilog,
    prog=os.path.basename(sys.argv[0]),
)

parser._action_groups.pop()
optional = parser.add_argument_group(title="optional arguments")
optional.add_argument(
    "-v", "--verbose", action="count", default=0, help="increase log level"
)
optional.add_argument(
    "-q", "--quiet", action="count", default=0, help="decrease log level"
)
required = parser.add_argument_group(title="required arguments")
required.add_argument(
    "-s",
    "--spawn",
    dest="spawn",
    metavar="N",
    type=int,
    required=True,
    help="how many processes to spawn",
)
args = parser.parse_args()

"""Logging setup"""
log_adjust = max(min(args.quiet - args.verbose, 2), -2)
logging.basicConfig(
    level=logging.INFO + log_adjust * 10,
    format="%(levelname)-8s[%(module)10s] %(message)s",
)


# Define UDP sender, to make it easy, make it global
SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
HOST, PORT = "127.0.0.1", 10514

# Simple string generator
def randomString(stringLength=16):
    """Generate a random string"""
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(stringLength))


def UDPsender(data):

    # since read data can have more than one packet I below make sure we read all data
    # start at the beginning of data
    start = 0
    # if our start position is lower than the size of the package
    while start < len(data):
        # Read from header how big our package is
        p_size = int.from_bytes(data[start : start + 4], "big")
        # send data in the size defined in header
        SOCKET.sendto(data[start : start + p_size], (HOST, PORT))
        logging.debug("\t-> {}".format(data[start : start + p_size]))
        # set start position at the end of the package size
        start += p_size


def processSpawner(name, command):

    # define generators
    procs = []
    procs = [
        subprocess.Popen(i, stdout=subprocess.PIPE, bufsize=0, shell=True)
        for i in command
    ]

    logging.info("all processes started")

    # while generator running, send output over UDP
    while True:
        # loop over processes
        for p in procs:
            data = None
            # get generator output
            try:
                data = p.stdout.read(1024)
                # send generator output
                if data:
                    logging.debug(
                        "'Sensor:{} with PID {}' sending data to {}:{}".format(
                            name[procs.index(p)], p.pid, HOST, PORT
                        )
                    )
                    # Send data
                    UDPsender(data)
                    # check if process is finished and send anything not sent
                    return_code = p.poll()
                    if return_code is not None:
                        UDPsender(data, sock)
                else:
                    logging.debug("{} - {}".format(p.pid, error))

            except KeyboardInterrupt:
                print("\n\n\tCauth KeyboardInterrupt, Bye Bye!\n\n")
                sys.exit(0)
            except Exception as e:
                logging.error("OOOoopss, some error ({})".format(e))
                sys.exit(1)


if __name__ == "__main__":

    logging.info("Spawning {} generator processes".format(args.spawn))
    sensor_name = []
    command = []

    for x in range(args.spawn):
        sensor_name.append(randomString())
        command.append(
            os.path.dirname(os.path.realpath(__file__))
            + "/bin/sensor_data.x86_64-unknown-linux-gnu --name {}".format(
                sensor_name[x]
            )
        )
        logging.info("starting sensor {}".format(sensor_name[x]))
    else:
        processSpawner(sensor_name, command)
