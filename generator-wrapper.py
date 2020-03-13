""" Generator wrapper. Send sensor data output with UDP over port 10514 """
import sys, subprocess, socket, os, time, string, random
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter
import logzero, logging
from logzero import logger

epilog = """

Example)
   python {} -s 3
________________________________________________________
/j0nixRulez

""".format(
    sys.argv[0]
)

## Argument parser setup
parser = ArgumentParser(
    formatter_class=RawTextHelpFormatter,
    description=__doc__,
    epilog=epilog,
    prog=os.path.basename(sys.argv[0]),
)
parser.add_argument(
    "-d",
    "--dest",
    dest="dest",
    metavar="XX",
    default="127.0.01",
    help="adress to send to (Default: 127.0.0.1)",
)
parser.add_argument(
    "-v", "--verbose", action="count", default=0, help="increase log level"
)
parser.add_argument(
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
    help="how many generators processes to spawn",
)
args = parser.parse_args()

# Set a custom formatter
log_adjust = max(min(args.quiet - args.verbose, 2), -2)
logzero.loglevel(logging.INFO + log_adjust * 10)

# Define UDP sender, to make it easy, make it global
SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
HOST, PORT = args.dest, 10514

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
        logger.debug("\t-> {}".format(data[start : start + p_size]))
        # set start position at the end of the package size
        start += p_size


def processSpawner(name, command):

    # Open the generator/generators
    try:
        # loop over commands array and start a subprocess and pipe stdout and don't buffer anything
        procs = [
            subprocess.Popen(x, stdout=subprocess.PIPE, bufsize=0, shell=True)
            for x in command
        ]

    except Exeption as e:
        logger.error("Failed to start generator ({})".format(e))
        sys.exit(1)
    else:
        logger.info("all processes started")

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
                        logger.debug(
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
                        logger.debug("{} - {}".format(p.pid, error))

                except KeyboardInterrupt:
                    print("\n\n\tCauth KeyboardInterrupt, Bye Bye!\n\n")
                    sys.exit(0)
                except Exception as e:
                    logger.error("OOOoopss, some error ({})".format(e))
                    sys.exit(1)

if __name__ == "__main__":

    logger.info("Spawning {} generator processes".format(args.spawn))
    # Array for storing sensor names, this so we can map which sensor is logging when debug
    sensor_name = []
    # Array for storing commands that spawns subprocesses
    command = []

    for x in range(args.spawn):
        # Generate a random name for sensor
        sensor_name.append(randomString())
        # Add a command we will execute, using that random name we just created
        command.append(
            os.path.dirname(os.path.realpath(__file__))
            + "/bin/sensor_data.x86_64-unknown-linux-gnu --name {}".format(
                sensor_name[x]
            )
        )
        logger.info("starting sensor {}".format(sensor_name[x]))
    else:
        # Let's get started and spawn some processes
        processSpawner(sensor_name, command)
