#!/usr/bin/env python3

import socket, json, threading, sys
try:
    import serial, serial.tools.list_ports
except ImportError:
    print("Dependency not found: please run 'pip3 install pyserial'")
    sys.exit(1)

ce_id = (0x0451, 0xe008)
max_packet_size = 4096

def u24(*args):
	o=[]
	for arg in args:
		if int(arg)<0: arg = abs(int(arg))
		else: arg = int(arg)
		o.extend(list(int(arg).to_bytes(3,'little')))
	return o

def sock_recv(s, ser_out):
	global connected
	while connected:
		try:
			status = ser_out.write(s.recv(max_packet_size))

		except socket.error as e:
			sys.stderr.write('Error: {}\n'.format(e))
	s.close()
	print("Disconnected.")
	ser_out.write(b'\x01\x00\x00\x01')

def connect(server, custom_port):
	global s, connected
	try:
		port = tcp_port
		if custom_port:
			port = custom_port
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.settimeout(15)
		try:
			print(f"Connecting to {server} on port {port}...")
			if use_ssl:
				print(f"We should be using SSL")
			s.connect((server, port))
		except socket.timeout:
			print("Socket timeout")
			return

		print("Connected!")
		s.settimeout(None)
		connected = True
		sock_thread = threading.Thread(target=sock_recv, args=(s, ser_out), daemon=True)
		sock_thread.start()
	except Exception as e:
		sys.stderr.write('Error: {}\n'.format(e))

def ser_recv(ser_in, ser_out):
	global s, connected, use_ssl
	print("Serial listening.")
	try:
		while True:
			size = int.from_bytes(ser_in.read(3), 'little')
			if size > max_packet_size:
				sys.stderr.write('Error: Got {} bytes from client, but the max packet size is {}\n'.format(size, max_packet_size))
				# todo: we should stop something, as this will 100% cause a desync
			else:
				data = ser_in.read(size)
				if len(data) > 0:
					packet_type = data[0]
					if debug_mode: print("C->S: Type {:>3}, size {}".format(packet_type, size))
					if packet_type == 0:
						# Connect
						hostinfo = str(data[1:-1], 'utf-8').split(":", maxsplit=2)
						if debug_mode: print("Got connect packet")
						server=hostinfo[0]
						custom_port=tcp_port
						if len(hostinfo)>1:
							custom_port=int(hostinfo[1])
						connect(server, custom_port)
						if connected:
							ser_out.write(b'\x01\x00\x00\x00')
							if debug_mode: print("B->C: Type   0, size 1")
						else:
							ser_out.write(b'\x01\x00\x00\xF0')
							if debug_mode: print("B->C: Type 253, size 1")
					elif packet_type == 1:
						# Disconnect
						if debug_mode: print("Got disconnect packet")
						connected = False
						try:
							s.close()
						except: pass
						ser_out.write(b'\x01\x00\x00\x01')
						if debug_mode: print("B->C: Type   1, size 1")
						return
					else:
						# Not for us
						if connected:
							status = s.send(bytes(u24(size)) + data)
							if debug_mode: print("C->S completed: ", status)
						else:
							sys.stderr.write('Error: Tried to send a packet without being connected to a server\n')
	except (serial.SerialException, OSError, IOError): 
		sys.stderr.write('Serial device appears disabled. Disconnecting from remote host\n')
		connected = False
		try:
			s.close()
		except NameError: pass
		return

f = open("config.json","r")
config = json.load(f)
f.close()

tcp_port = config["port"]
use_ssl = False
prefer_ssl = False

pipe_mode = False
if "mode" in config:
	if config["mode"] == "pipe":
		pipe_mode = True
	elif config["mode"] == "CEmu":
		pipe_mode = True
	elif config["mode"] == "cemu":
		pipe_mode = True
	elif config["mode"] == "serial":
		pipe_mode = False
	else:
		print("Invalid mode: " + config["mode"])
		sys.exit(1)
serial_mode = not pipe_mode

debug_mode = False
if "debug" in config:
	debug_mode = config["debug"]

if debug_mode:
	print("Running in debug mode.")

if serial_mode:
	if "serial" in config:
		serial_name = config["serial"]
	else:
		ports = [x for x in serial.tools.list_ports.comports() if (x.vid, x.pid) == ce_id]
		if len(ports) == 0:
			ports_manual=serial.tools.list_ports.comports()
			ct=0
			for p in ports_manual:
				print(f"{ct} {p}")
				ct+=1
			print(f"{ct} device not listed")
			sel=input("Select Device: ")
			if int(sel)==len(ports_manual):
				sys.exit(1)
			else:
				serial_name=ports_manual[int(sel)].device
		else: serial_name = ports[0].device

		if len(ports) > 1:
			print("Multiple devices detected - using {}".format(serial_name))

	ser = serial.Serial(serial_name, timeout=None)
	ser_in = ser
	ser_out = ser

if pipe_mode:
	oname = config["pipe_out"]
	iname = config["pipe_in"]
	if debug_mode:
		print("Out pipe: " + oname)
		print("In pipe: " + iname)
	ser_out = open(oname, "wb", buffering=0)
	ser_in = open(iname, "rb")
	if debug_mode:
		print("Pipes opened")

print("^C to exit.")

connected = False

try:
	ser_recv(ser_in, ser_out)
except KeyboardInterrupt:
	pass

if serial_mode:
	ser.close()
if pipe_mode:
	ser_in.close()
	ser_out.close()
try: 
	s.close()
except: pass
	