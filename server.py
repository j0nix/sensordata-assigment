"""
   Fetch incoming packets from sensors on port 10514, parse them to human readable text
   and finally log the data as json to a file named as the sensor sending the data

   Author:     Jon Svendsen
   License:    Free as in beer
"""
import sys, socket, time, pytz, json, socket, threading, os
from struct import *
from datetime import datetime
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter
import logzero, logging
from logzero import logger

epilog = """
Example)
   python {} -p j0nix -v
________________________________________________________
/j0nixRulez
""".format(
    sys.argv[0]
)

## Argument parser setup
parser = ArgumentParser(
    formatter_class=RawTextHelpFormatter, description=__doc__, epilog=epilog,
)
parser.add_argument(
    "-b",
    "--bind",
    dest="addr",
    metavar="XX",
    default="127.0.01",
    help="adress to bind to (Default: 127.0.0.1)",
)
parser.add_argument(
    "-v", "--verbose", action="count", default=0, help="increase log level"
)
parser.add_argument(
    "-q", "--quiet", action="count", default=0, help="decrease log level"
)
parser.add_argument(
    "-p",
    "--prefix",
    dest="prefix",
    metavar="XX",
    default=None,
    help="set logfile prefix",
)
args = parser.parse_args()

# Set a custom formatter
log_adjust = max(min(args.quiet - args.verbose, 2), -2)
logzero.loglevel(logging.INFO + log_adjust * 10)

"""
Note: UDPSensorPacketParser inherits UDPServer class, just for showcasing
      OOP style programming. Overwrites 'recv_message' function and also
      add some more cool functions required for solving the assigment
"""
# A simple UDP Server
class UDPServer:
    def __init__(self, host, port):
        self.host = host  # Host address
        self.port = port  # Host port
        self.sock = None  # Socket
        # create socket and bind server to the address + port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))

    def recv_message(self):
        # Listen for incoming messages
        try:
            data, address = self.sock.recvfrom(1024)
            print(data.decode("utf-8"))
        except Exception as e:
            print("Failed to fetch incoming message from socket ({})".format(e))

    def shutdown(self):
        print("\nBye Bye!")
        self.sock.close()


# Starts a UDP server when initiated.
# Class for all required parsing of our sensor data
class UDPSensorPacketParser(UDPServer):
    def __init__(self, host, port, file_prefix=None):
        # Call init from inherited/parent class
        super().__init__(host, port)
        # Set the filename prefix, if any
        self.prefix = file_prefix

        logger.info("Started UDP server @ {}:{}".format(host, port))

    def recv_message(self):

        try:
            # Run until further notice
            while True:
                # Get incoming packet/message
                try:
                    data, address = self.sock.recvfrom(1024)
                    try:
                        # Threads to handle multiple "clients"
                        c_thread = threading.Thread(
                            # Thread out and run function __incoming_message to start parsing package/message
                            target=self.__incoming_message,
                            args=(data, address),
                        )
                        # run in background
                        c_thread.daemon = True
                        c_thread.start()
                    except Exception as e:
                        logging.error(
                            "Failed to start daemon for incoming message".format(e)
                        )
                        raise e

                except Exception as e:
                    logging.error("Failed get incoming message ({})".format(e))

        except KeyboardInterrupt:
            self.shutdown()

    def __incoming_message(self, data, address):

        try:
            # Parse header data. size & nlength (name length) will be used to eveluate and parse the rest of the message
            p_size, p_timestamp, p_nlength = unpack(">IQB", data[:13])

            # make sure that the numbers adds up
            if len(data) == p_size:
                # Decode rest of message and log as json to a logfile
                parsed_dict = self.__decode_sensor_data(
                    data, p_size, p_timestamp, p_nlength
                )
                try:
                    self.__log_data(parsed_dict)
                except Exception as e:
                    logger.warning("Failed to send data to log outout ({})".format(e))
            else:
                logger.warning(
                    "Actual packet size and header packet size missmatch. (Data size: {}, packet_size_in_header: {}) data: {}".format(
                        len(data), p_size, data
                    )
                )
                raise error
        except error as e:
            logger.error(
                "Failed to parse packet({}) from {} ({})".format(data, address, e)
            )

    def __log_data(self, data):
        logger.debug(json.dumps(data))
        # set filename
        try:
            data["name"]
            filename = "{}.json".format(data["name"])
        except IndexError:
            filename = "unknown.json"
        # should we prefix files ?
        if self.prefix:
            filename = "{}-{}".format(self.prefix, filename)

        try:
            # write data to log file
            with open(filename, "a") as writer:
                writer.write("{}\n".format(json.dumps(data)))

        except Exception as e:
            logger.error("Failed to send data to logfile ({})".format(e))

    def __decode_sensor_data(self, message, msg_size, timestamp, name_length):

        # Set start and stop position for name in packet
        # we then use n_stop as start position for parsing temperature and humidity
        n_start, n_stop = (13, 13 + name_length)

        # Dictonary to save parsed data into ... or not, depending on what comes our way
        json_dict = {
            "timestamp": None,
            "name": None,
            "temperature": None,
            "humidity": None,
        }

        # Get name from packet, return what we have in dics if we fail
        try:
            name = unpack(">{}s".format(name_length), message[n_start:n_stop])
        except error as e:
            logger.warning(
                "failed to unpack name ({}), message data: {}, ignoring packet".format(
                    e, message
                )
            )
            return json_dict

        # Parse epoch timestamp and set timestamp to ISO8601 with time zone, return what we have in dict if we fail
        try:
            ISO_timestamp = "{}{}:00".format(
                datetime.fromtimestamp(timestamp / 1000).isoformat()[:-3],
                datetime.now(pytz.timezone("Europe/Stockholm")).strftime("%z")[0:3],
            )
        except ValueError as e:
            logger.error("failed to parse date data ({}), ignore packet".format(e))
            return json_dict

        # Add data to our sensor data dictonary
        json_dict = {
            "timestamp": ISO_timestamp,
            "name": name[0].decode("utf-8"),
            "temperature": None,
            "humidity": None,
        }

        """
        We have 4 usecases to consider
        1. n_stop == msg_size. That means there is nothing left to parse and we can skip further actions
        2. msg_size - n_stop = 2. We have humidity data to parse, but no temerature data
        3. msg_size - n_stop = 3. We have temparature data to parse, but no humidity data
        4. msg_size - n_stop = 5. We have both temparature and humidity data to parse
        """

        # Usecase 1, Check if we need to parse sensor data, otherwise we return what we have
        if msg_size > n_stop:

            # Usecase 2, only humidity?
            if msg_size - n_stop == 2:
                json_dict["humidity"] = unpack(">H", message[n_stop:msg_size])[0]

            # Usecase 3, only temperature?
            if msg_size - n_stop == 3:
                json_dict["temperature"] = int.from_bytes(
                    message[n_stop:msg_size], "big"
                )
                """
                    - Alternative solution for parsing 3 bytes with struct
                      => Make it 4 bytes!

                    tmp = bytearray()
                    tmp.extend(b'\x00')
                    tmp.extend(message[n_stop:msg_size])
                    temperature = unpack(">I", tmp)
                """

            # Usecase 4, both temperature and humidity ?
            if msg_size - n_stop == 5:
                json_dict["temperature"] = int.from_bytes(
                    message[n_stop : msg_size - 2], "big"
                )
                json_dict["humidity"] = int.from_bytes(
                    message[n_stop + 3 : msg_size], "big"
                )
        else:
            return json_dict

        """
        I assume the following when proceed:
        - Temperature are in hundreds of K that I translate that the three first digits is in Kelvin, the rest is decimals
          I also assume that that all temp data always have more than three digits.
        - Humidity is measured between 1 to 100. Numbers greater than 100, then third digit is a decimal
        """
        # Do we have temp value?
        if json_dict["temperature"]:
            try:
                # Take first three digits and make rest decimal, round to one decimal
                json_dict["temperature"] = round(
                    float(str(json_dict["temperature"])[:3])
                    + float("0." + str(json_dict["temperature"])[4:]),
                    1,
                )
            except Exception as e:
                logger.error("Error when modeling temperature with decimals")

        # Do we have humidity value? if so, do we need to add decimal to value?
        if json_dict["humidity"] and json_dict["humidity"] > 100:
            try:
                # Take two first digits and make rest decimals, round to one decimal
                json_dict["humidity"] = round(
                    float(str(json_dict["humidity"])[:2])
                    + float("0." + str(json_dict["humidity"])[3:]),
                    1,
                )
            except Exception as e:
                logger.error("Error when modeling humidity with decimals")

        return json_dict


if __name__ == "__main__":
    # Create UDP server and listen for incoming packets from generator-wrapper.py
    server = UDPSensorPacketParser(args.addr, 10514, args.prefix)
    server.recv_message()
