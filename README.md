# sensordata-assigment
The assignment is to read input from a number of sensors and output log files.
## Solution
My aproach to this is to make a wrapper for the generator binary and send data to a 'server' for parsing and logging of data.

## Howto test solution

1. Start server
2. Start sensor-generator wrapper
3. Inspect result in file/files

### Start server
```bash
$ python server.py 
[INFO] [server] Started UDP server @ 127.0.0.1:10514
```
```bash
usage: server.py [-h] [-v] [-q] [-p XX]

optional arguments:
  -v, --verbose       increase log level
  -q, --quiet         decrease log level
  -p XX, --prefix XX  set logfile prefix

Example)
   python {} -p j0nix -v
________________________________________________________
/j0nixRulez
```
### Start generator
```bash
$ python generator-wrapper.py -s 1
INFO    [generator-wrapper] Spawning 1 generator processes
INFO    [generator-wrapper] starting sensor vuxexekctlrkcbpd
INFO    [generator-wrapper] all processes started
```
```
usage: generator-wrapper.py [-h] [-v] [-q] -s N

optional arguments:
  -v, --verbose    increase log level
  -q, --quiet      decrease log level

required arguments:
  -s N, --spawn N  how many generators processes to spawn

Example)
   python {} -s 3
________________________________________________________
/j0nixRulez
```
