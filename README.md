# sensordata-assigment
The assignment is to read input from a number of sensors and output log files.
## Solution
My aproach to this is to make a wrapper for the generator binary and send data to a 'server' for parsing and logging of data.

## HowTo

1. Start server
2. Start sensor-generator wrapper
3. Inspect result in file/files

### Start server
```
$ python server.py
[INFO] [server] Started UDP server @ 127.0.0.1:10514
```
```
usage: server.py [-h] [-b XX] [-v] [-q] [-p XX]

   Fetch incoming packets from sensors on port 10514, parse them to human readable text
   and finally log the data as json to a file named as the sensor sending the data

   Author:     Jon Svendsen
   License:    Free as in beer

optional arguments:
  -h, --help          show this help message and exit
  -b XX, --bind XX    adress to bind to (Default: 127.0.0.1)
  -v, --verbose       increase log level
  -q, --quiet         decrease log level
  -p XX, --prefix XX  set logfile prefix

Example)
   python server.py -p j0nix -v
________________________________________________________
/j0nixRulez
```
### Start generator
```
$ python generator-wrapper.py -s 1
INFO    [generator-wrapper] Spawning 1 generator processes
INFO    [generator-wrapper] starting sensor vuxexekctlrkcbpd
INFO    [generator-wrapper] all processes started
```
```
usage: generator-wrapper.py [-h] [-d XX] [-v] [-q] -s N

 Generator wrapper. Send sensor data output with UDP over port 10514

optional arguments:
  -h, --help        show this help message and exit
  -d XX, --dest XX  adress to send to (Default: 127.0.0.1)
  -v, --verbose     increase log level
  -q, --quiet       decrease log level

required arguments:
  -s N, --spawn N   how many generators processes to spawn

Example)
   python generator-wrapper.py -s 3
________________________________________________________
/j0nixRulez
```
