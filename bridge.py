import socket, json, threading, sys
try:
    import serial, serial.tools.list_ports
except ImportError:
    print("Dependency not found: please run 'pip3 install pyserial'")
    sys.exit(1)