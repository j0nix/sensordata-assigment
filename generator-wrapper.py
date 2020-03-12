import subprocess, socket, os, time
'''
generator wrapper. Send sensor data output with UDP over port 10514
'''
# Define UDP sender
HOST, PORT = "127.0.0.1", 10514
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# open a subprocess with generator
file = os.path.dirname(os.path.realpath(__file__)) + "/bin/sensor_data.x86_64-unknown-linux-gnu"
process = subprocess.Popen([file,'-n j0nix'], stdout=subprocess.PIPE,bufsize=0,shell=True)
print("Running subprocess on PID {}".format(process.pid))
# while generator running, send output over UDP
while True:
    # get generator output
    data = process.stdout.read(100)
    # send generator output
    sock.sendto(data, (HOST, PORT))
    print("sent data")
    # check if process is finished
    return_code = process.poll()
    if return_code is not None:
        ## untested code, the idea is to parse whatever way be left after process is finished
        print('RETURN CODE', return_code)
        # Process has finished, read rest of the output
        for output in process.stdout.read(100):
    	    sock.sendto(data, (HOST, PORT))
        break
