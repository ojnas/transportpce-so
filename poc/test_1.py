#!/usr/bin/env python

from transportpce import Controller
from devices import DockerDevices
import json
import time

tpce = Controller()
dd = DockerDevices()

node_ids = ["XPDR-A1", "XPDR-C1", "ROADM-A1", "ROADM-C1"]
devices = [n[:-1].replace("-", "").lower() for n in node_ids]

dd.start(devices)
time.sleep(20)

for node_id, ip_addr in zip(node_ids, dd.get_ip_addrs()):
    tpce.connect_device(node_id, ip_addr)
time.sleep(20)

tpce.create_ots_oms("ROADM-A1", "DEG1-TTP-TXRX")
tpce.create_ots_oms("ROADM-A1", "DEG2-TTP-TXRX")
tpce.create_ots_oms("ROADM-C1", "DEG1-TTP-TXRX")
tpce.create_ots_oms("ROADM-C1", "DEG2-TTP-TXRX")

res = tpce.get_optical_power("ROADM-A1", "DEG2-TTP-TXRX")
print("Optical power on ROADM-A1:")
print(json.dumps(res, indent = 4))

res = tpce.get_optical_power("ROADM-C1", "DEG1-TTP-TXRX")
print("Optical power on ROADM-C1:")
print(json.dumps(res, indent = 4))

res = tpce.measure_and_add_oms_spanloss()
print("Spanloss:")
print(json.dumps(res, indent = 4))

xpdr_lcp_1 = tpce.get_logical_connection_point("XPDR-A1", "1/0/1-PLUG-NET", "1")
xpdr_lcp_2 = tpce.get_logical_connection_point("XPDR-C1", "1/0/1-PLUG-NET", "1")
srg_lcp_1 = tpce.get_logical_connection_point("ROADM-A1", "5/0", "C4")
srg_lcp_2 = tpce.get_logical_connection_point("ROADM-C1", "3/0", "C4")

node_1 = {
    "xpdr_node_id": "XPDR-A1",
    "xpdr_logical_connection_point": xpdr_lcp_1,
    "roadm_node_id": "ROADM-A1",
    "srg_logical_connection_point": srg_lcp_1
}

node_2 = {
    "xpdr_node_id": "XPDR-C1",
    "xpdr_logical_connection_point": xpdr_lcp_2,
    "roadm_node_id": "ROADM-C1",
    "srg_logical_connection_point": srg_lcp_2
}

tpce.provision_xpdr_service(node_1, node_2, wl_index = 4)
time.sleep(180)

srg_lcp_1 = tpce.get_logical_connection_point("ROADM-A1", "5/0", "C3")
srg_lcp_2 = tpce.get_logical_connection_point("ROADM-C1", "3/0", "C3")

node_1 = {
    "roadm_node_id": "ROADM-A1",
    "srg_logical_connection_point": srg_lcp_1
}

node_2 = {
    "roadm_node_id": "ROADM-C1",
    "srg_logical_connection_point": srg_lcp_2
}

tpce.provision_roadm_service(node_1, node_2, wl_index = 3)
time.sleep(180)

res = tpce.get_config("ROADM-A1")
res = res["roadm-connections"]
print("ROADM connections on ROADM-A1:")
print(json.dumps(res, indent = 4))

res = tpce.get_config("ROADM-C1")
res = res["roadm-connections"]
print("ROADM connections on ROADM-C1:")
print(json.dumps(res, indent = 4))

dd.stop()

