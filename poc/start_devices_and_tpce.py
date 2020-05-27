#!/usr/bin/env python

from transportpce import Controller
from devices import DockerDevices
import subprocess
import os
import psutil
import signal
import time

tpce = Controller()

karaf = "../karaf/target/assembly/bin/karaf"
with open('odl.log', 'w') as outfile:
    odl_process = subprocess.Popen(["bash", karaf, "server"],
                                    stdout=outfile, stdin=open(os.devnull))

node_ids = ["XPDR-A1", "XPDR-C1", "ROADM-A1", "ROADM-B1", "ROADM-C1"]
#node_ids = ["ROADM-A1", "ROADM-C1"]
#node_ids = ["XPDR-A1", "XPDR-C1", "ROADM-D1"]
devices = [n[:-1].replace("-", "").lower() for n in node_ids]

dd = DockerDevices(devices)
dd.start()
time.sleep(40)

for node_id, ip_addr in zip(node_ids, dd.get_ip_addrs()):
    tpce.connect_device(node_id, ip_addr)
    time.sleep(10)

input("Press Enter to finish...")

dd.save_traces()

for child in psutil.Process(odl_process.pid).children():
    child.send_signal(signal.SIGINT)
    child.wait()
odl_process.send_signal(signal.SIGINT)
odl_process.wait()

dd.stop()

