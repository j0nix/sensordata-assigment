import sys, socket, time, pytz, json, socket, threading
from struct import *
from datetime import datetime

"""
Assigment: Read input from a number of sensors and output log files.
Author: Jon Svendsen
License: Free as in beer

-- PACKET SPEC -----------------------------------------------------------------------------------
--------------------------------------------------------------------------------------------------
Offset      Field name      Type            Size        Description
--------------------------------------------------------------------------------------------------
0           plength         uint            4 bytes     The length of package,including this field
4           timestamp       uint            8 bytes     Unix timestamp, in milliseconds
12          nlen            uint            1 byte      The length of the name
13          name            string          nlen bytes  The length of the name
13 + nlen   temperature     uint            3 bytes     In hundredths of K
16 + nlen   humidity        uint            2 bytes     Relative humidity in ‰
--------------------------------------------------------------------------------------------------
- Both temperature and humidity are optional.
- This means that the offset for humidity can also be 13 + nlen
"""


def incoming_message(data, address):

    """ Handle the client """
    # handle request


""" A simple UDP Server """


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
        except Exception as e:
            print("Failed to fetch incoming message from socket ({})".format(e))

        print(data.decode('utf-8'))

    def shutdown(self):
        self.sock.close()


""" A simple UDP Server for handling multiple clients """


class UDPSensorPacketParser(UDPServer):
    def __init__(self, host, port):
        super().__init__(host, port)
        self.socket_lock = threading.Lock()

    def incoming_message(self, data, address):
        # UDP Packet Headers
        p_size, p_timestamp, p_nlength = (None, None, None)
        try:
            # Parse header data. size & nlength (name length) will be used to eveluate and parse the rest of the message
            p_size, p_timestamp, p_nlength = unpack(">IQB", data[:13])

            # make sure that the numbers adds up
            if len(data) == p_size:
                # Decode rest of message and log as json to a logfile
                parsed_dict = self.decode_sensor_data(
                    data, p_size, p_timestamp, p_nlength
                )
                try:
                    self.log_data(parsed_dict)
                except Exception as e:
                    print("failed to send data to log outout ({})".format(e))
            else:
                print("Exception: data:{}, len(data):{}, packet_size_in_header:{})".format(data,len(data),p_size))
                raise error
        except error as e:
            print("failed to parse packet({}) from {} ({})".format(data, address, e))

    def recv_message(self):
        """ Wait for clients and handle their requests """
        try:
            while True:  # keep alive

                try:  # receive request from client
                    data, address = self.sock.recvfrom(1024)

                    c_thread = threading.Thread(
                        target=self.incoming_message, args=(data, address)
                    )
                    c_thread.daemon = True
                    c_thread.start()

                except OSError as e:
                    print(e)

        except KeyboardInterrupt:
            self.shutdown()

    def log_data(self, data):
        try:
            jsonData = json.dumps(data, indent=4)
            print(jsonData)
        except Exception as e:
            print(e)
            raise

    def decode_sensor_data(self, message, msg_size, timestamp, name_length):

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

        # Get name from packet
        try:
            name = unpack(">{}s".format(name_length), message[n_start:n_stop])
        except error as e:
            print(
                "failed to unpack name ({}), start pos: {}, stop_pos: {}, message: {}, ignoring packet".format(
                    e, n_start, n_stop, message
                )
            )
            return json_dict

        # Parse epoch timestamp and set timestamp to ISO8601 with time zone
        try:
            ISO_timestamp = "{}{}:00".format(
                datetime.fromtimestamp(timestamp / 1000).isoformat()[:-3],
                datetime.now(pytz.timezone("Europe/Stockholm")).strftime("%z")[0:3],
            )
        except ValueError as e:
            print("failed to parse date data ({}), ignore packet".format(e))
            return json_dict

        # Add data to dictonary we will return from read sensor data
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

        # Usecase 1, Check if we need to parse sensor data
        if msg_size > n_stop:

            # Usecase 2, only humidity?
            if msg_size - n_stop == 2:
                json_dict["humidity"] = unpack(">H", message[n_stop:msg_size])[0]

            # Usecase 3, only temperature?
            if msg_size - n_stop == 3:
                json_dict["temperature"] = int.from_bytes(
                    message[n_stop:msg_size], "big"
                )
                """ Alternative solution for parsing 3 bytes with struct => Make it 4 bytes!
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
        I assume the following when proceed
        - Temperature are in hundreds of K that I translate that the three first digits is in Kelvin
          meaning than no measure values are lower than 100 K. All digits after the three first is decimals
        - Humidity is measured between 1 to 100. Numbers greater than 100, third digit is a decimal
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
                print("Error when modeling temperature with decimals")

        # Do we have humidity value?
        # Do we need to add decimal to value?
        if json_dict["humidity"] and json_dict["humidity"] > 100:
            try:
                # Take two first digits and make rest decimals, round to one decimal
                json_dict["humidity"] = round(
                    float(str(json_dict["humidity"])[:2])
                    + float("0." + str(json_dict["humidity"])[3:]),
                    1,
                )
            except Exception as e:
                print("Error when modeling humidity with decimals")

        return json_dict


def main():
    # Create UDP server and listen for incoming packets from generator-wrapper.py
    server = UDPSensorPacketParser("127.0.0.1", 10514)
    server.recv_message()

if __name__ == "__main__":
    main()
