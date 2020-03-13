# sensordata-assigment
The assignment is to read input from a number of sensors and output log files.
## Solution
My aproach to this is to make a wrapper for the generator binary and send data to a 'server' for parsing and logging of data.

## Howto test solution

1. Start server
2. Start sensor-generator wrapper
3. Inspect result in file/files

### Start server
```
$ python server.py 
[INFO] [server] Started UDP server @ 127.0.0.1:10514
```
```
usage: server.py [-h] [-v] [-q] [-p XX]

Assigment: Read input from a number of sensors and output log files.
Author: Jon Svendsen
License: Free as in beer

-- PACKET SPEC for incoming messages -------------------------------------------------------------
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
--------------------------------------------------------------------------------------------------

optional arguments:
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
usage: generator-wrapper.py [-h] [-v] [-q] -s N

 Generator wrapper. Send sensor data output with UDP over port 10514

optional arguments:
  -v, --verbose    increase log level
  -q, --quiet      decrease log level

required arguments:
  -s N, --spawn N  how many generators processes to spawn

Example)
   python generator-wrapper.py -s 3
________________________________________________________
/j0nixRulez
```
