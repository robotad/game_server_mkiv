# Game Server MK-IV ![logo](cal.gif)

## Description
The basic idea for this server is to accomplish these goals:
- Quickly communicate player information between multiple clients
- Persist game state information

## Structure
The following describes the file structure of this repository.
```bash
app/
    config.py - global application configurations
    state_manager.py - manages the state of the application. All information
                      regarding game information should be accessed here
    udp_server.py - the implementation of the udp server
build.sh - script to build docker container
Dockerfile - dockerfile for building the containerized server
run.sh - script to run the containerized server
entrypoint.sh - loaded into the docker container as the ENTRYPOINT for execution
```

## Testing
You may have to increase the mount of files your OS can have open at
a time. On MacOS:
```bash
ulimit -Sn 1024
```
Verify the amount of open files has been increased to 1024:
```bash
ulimit -a

core file size          (blocks, -c) 0
data seg size           (kbytes, -d) unlimited
file size               (blocks, -f) unlimited
max locked memory       (kbytes, -l) unlimited
max memory size         (kbytes, -m) unlimited
open files                      (-n) 1024
...
```

Use the test client `./test.sh` to run tests.
```bash
pip3 install virtualenv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./test.sh
```
