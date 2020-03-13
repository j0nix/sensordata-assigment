# sensordata-assigment
The assignment is to read input from X number of sensors and output result to log file as json

## howto

1. Start server
2. Start sensor-generator
3. Tail those files

### Start server
```bash
$ python server.py
```
```bash
python server.py -h
usage: server.py [-h] [-v] [-q] [-p PREFIX]

optional arguments:
  -v, --verbose         increase log level
  -q, --quiet           decrease log level
  -p PREFIX, --prefix PREFIX
                        set logfile prefix

Example)
   python {} -p j0nix -v
________________________________________________________
/j0nixRulez
```
### Start generator 
