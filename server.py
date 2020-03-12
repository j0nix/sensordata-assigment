import sys, socket, time, pytz, json
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
'''

"""

def decodeSensorData(message, msg_size, timestamp, name_length):

    # Set start and stop position for name in packet
    # we then use n_stop as start position for parsing temperature and humidity
    n_start, n_stop = (13, 13 + name_length)

    # Get name from packet
    name = unpack(">{}s".format(name_length), message[n_start:n_stop])

    # Parse epoch timestamp and set timestamp to ISO8601 with time zone
    ISO_timestamp = "{}{}:00".format(
        datetime.fromtimestamp(timestamp / 1000).isoformat()[:-3],
        datetime.now(pytz.timezone("Europe/Stockholm")).strftime("%z")[0:3],
    )

    # Prepare dictonary we will return for read sensor data
    # if below condition evaluates as false we return dict as is
    json_dict = {
        "timestamp": ISO_timestamp,
        "name": name[0].decode("utf-8"),
        "temperature": None,
        "humidity": None,
    }

    """
    We have 4 usecases to consider
    1. n_stop == msg_size. That means there is nothing left to parse and we can skip further actions
    3. msg_size - n_stop = 2. We have humidity data to parse, but no temerature data
    2. msg_size - n_stop = 3. We have temparature data to parse, but no humidity data
    4. msg_size - n_stop = 5. We have both temparature and humidity data to parse
    """

    # Usecase 1, Check if we need to parse sensor data
    if msg_size > n_stop:

        # Usecase 2, only humidity?
        if msg_size - n_stop == 2:
            json_dict["humidity"] = unpack(">H", message[n_stop:msg_size])[0]

        # Usecase 3, only temperature?
        if msg_size - n_stop == 3:
            json_dict["temperature"] = int.from_bytes(message[n_stop:msg_size], "big")
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


def logData(data):
    try:
        jsonData = json.dumps(data, indent=4)
        print(jsonData)
    except Exception as e:
        print(e)
        raise


if __name__ == "__main__":

    """
    Create UDP listener for incoming packets from generator-wrapper.py
    generatior-wrapper simulates incoming UDP traffic to this packet parser & log script.
    """

    try:
        # Server options
        local_ip, local_port, buffer_size = "127.0.0.1", 10514, 1024
        # Create a datagram socket
        UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        # Bind to address and ip & port
        UDPServerSocket.bind((local_ip, local_port))
    except Exception as e:
        print("Failed starting UDP server, {}".format(e))
        sys.exit(1)
    else:
        print(
            "Server up and listening for incoming UDP on {}:{}".format(
                local_ip, local_port
            )
        )

    # Init variables to make them global
    # These represent header data for incoming UDP packets
    p_size, p_timestamp, p_nlength = (None, None, None)
    # Listen for incoming datagrams
    while True:
        try:
            # Fetch incoming message
            # Have not read up on buffer size and how I should think to make this optimal.
            # Now only picked a value that works...
            incoming_msg = UDPServerSocket.recvfrom(buffer_size)
        except Exception as e:
            print("Failed to fetch data from UDP socket")
        else:
            # set message data and adress to dedicated variables, to clearify things
            message = incoming_msg[0]
            address = incoming_msg[1]

            try:
                # Parse header data. size & nlength (name length) will be used to eveluate and parse the rest of the message
                p_size, p_timestamp, p_nlength = unpack(">IQB", message[:13])
            except error as e:
                print("failed to parse packet(): {}".format(message, e))
            else:
                # Decode rest of message and log as json to a logfile
                parsed_dict = decodeSensorData(message, p_size, p_timestamp, p_nlength)
                try:
                    logData(parsed_dict)
                except Exception as e:
                    print("failed to send data to log outout")
