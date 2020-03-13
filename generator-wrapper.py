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
    metavar='N',
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

# Simple string generator
def randomString(stringLength=16):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

def processSpawner(name,command):

    # Define UDP sender
    host, port = "127.0.0.1", 10514
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # define 
    procs = []
    # start subprocesses
    #for sub in command:
    #    procs.append(subprocess.Popen(sub,stdout=subprocess.PIPE,bufsize=0,shell=True))
    #    time.sleep(1)
    procs = [ subprocess.Popen(i,stdout=subprocess.PIPE,bufsize=0,shell=True) for i in command ]
    logging.info("all processes started")

    # while generator running, send output over UDP
    while True:
        for p in procs:
            # get generator output
            data = None
            try:
                data = p.stdout.read(1024)
            except:
                pass

            # send generator output
            if data:
                start=0
                while start < len(data):
                    p_size = int.from_bytes(data[start:start+4], "big")
                    sock.sendto(data[start:start+p_size], (host, port))
                    logging.debug("'Sensor:{} with PID {}' sent {} to {}:{}".format(name[procs.index(p)],p.pid,data[start:start+p_size],host,port))
                    start+=p_size

                # check if process is finished
                return_code = p.poll()
                if return_code is not None:
                    ## untested code, the idea is to parse whatever way be left after process is finished
                    logging.debug('RETURN CODE', return_code)
                    # Process has finished, read rest of the output
                    for output in p.stdout.read(34):
                        sock.sendto(data.encode("utf-8"), (host, port))
                    break
            else:
                logging.debug("{} - {}".format(p.pid,error))
        #p.wait()

if __name__ == "__main__":

    logging.info("Spawning {} generator processes".format(args.spawn))
    sensor_name = []
    command= []

    for x in range(args.spawn):
        sensor_name.append(randomString())
        command.append(os.path.dirname(os.path.realpath(__file__)) + "/bin/sensor_data.x86_64-unknown-linux-gnu --name {}".format(sensor_name[x]))
        logging.info("starting sensor {}".format(sensor_name[x]))
    else:
        processSpawner(sensor_name,command)
