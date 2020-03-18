#!/usr/bin/env python

import json
import requests

class Controller():
    
    headers = {"content-type": "application/json", "accept": "application/json"}
    
    def __init__(self, host = "localhost", port = "8181", auth=("admin", "admin")):
        self.baseurl = f"http://{host}:{port}/restconf"
        self.auth = auth

    def connect_device(self, node_id, ip_addr, port = "2022"):
        url = f"{self.baseurl}/config/network-topology:network-topology/topology/topology-netconf/node/{node_id}"
        data = {"node": [{
                    "node-id": node_id,
                    "netconf-node-topology:username": "admin",
                    "netconf-node-topology:password": "admin",
                    "netconf-node-topology:host": ip_addr,
                    "netconf-node-topology:port": port,
                    "netconf-node-topology:tcp-only": "false",
                    "netconf-node-topology:pass-through": {}}]}
        requests.put(url, data=json.dumps(data), headers=self.headers, auth=self.auth)
        
    # some useful getters:    
    def get_config(self, node_id):
        url = (f"{self.baseurl}/config/network-topology:network-topology/topology/topology-netconf/node/{node_id}/"
                "yang-ext:mount/org-openroadm-device:org-openroadm-device")
        response = requests.get(url, headers=self.headers, auth=self.auth)
        return response.json()["org-openroadm-device"]
        
    def get_operational(self, node_id):
        url = (f"{self.baseurl}/operational/network-topology:network-topology/topology/topology-netconf/node/{node_id}/"
                "yang-ext:mount/org-openroadm-device:org-openroadm-device")
        response = requests.get(url, headers=self.headers, auth=self.auth)
        return response.json()["org-openroadm-device"]
    
    def get_portmapping(self):
        url = f"{self.baseurl}/config/transportpce-portmapping:network"
        response = requests.get(url, headers=self.headers, auth=self.auth)
        return response.json()["network"]["nodes"]
    
    def get_portmapping_node(self, node_id):
        url = f"{self.baseurl}/config/transportpce-portmapping:network/nodes/{node_id}"
        response = requests.get(url, headers=self.headers, auth=self.auth)
        return response.json()["nodes"][0]
        
    def get_topology(self):
        url = f"{self.baseurl}/config/ietf-network:networks/network/openroadm-topology"
        response = requests.get(url, headers=self.headers, auth=self.auth)
        return response.json()["network"][0]
        
    def get_topology_node(self, node_id):
        url = f"{self.baseurl}/config/ietf-network:networks/network/openroadm-topology/node/{node_id}/"
        response = requests.get(url, headers=self.headers, auth=self.auth)
        return response.json()["node"][0]
        
    def get_service_list(self):
        url = f"{self.baseurl}/operational/org-openroadm-service:service-list"
        response = requests.get(url, headers=self.headers, auth=self.auth)
        return response.json()["service-list"]
        
    def get_service_path_list(self):
        url = f"{self.baseurl}/operational/transportpce-servicepath:service-path-list"
        response = requests.get(url, headers=self.headers, auth=self.auth)
        return response.json()["service-path-list"]
        
    def get_service_path(self, service_path_name):
        url = f"{self.baseurl}/operational/transportpce-servicepath:service-path-list/service-paths/{service_path_name}"
        response = requests.get(url, headers=self.headers, auth=self.auth)
        return response.json()["service-paths"][0]
    
    def get_logical_connection_point(self, node_id, circuit_pack_name, port_name):
        mapping = self.get_portmapping_node(node_id)["mapping"]
        return next(m["logical-connection-point"] for m in mapping
                    if m["supporting-circuit-pack-name"] == circuit_pack_name and m["supporting-port"] == port_name)
                    
    def get_srg_wavelengths(self, srg_id):
        url = (f"{self.baseurl}/config/ietf-network:networks/network/openroadm-topology/node/{srg_id}/"
                "org-openroadm-network-topology:srg-attributes")
        srg_attrs = requests.get(url, headers=self.headers, auth=self.auth).json()
        return [a["index"] for a in srg_attrs["org-openroadm-network-topology:srg-attributes"]["available-wavelengths"]]
        
    def get_srg_pps(self, srg_id):
        url = f"{self.baseurl}/config/ietf-network:networks/network/openroadm-topology/node/{srg_id}/"
        response = requests.get(url, headers=self.headers, auth=self.auth)
        pps = [tp for tp in response.json()["node"][0]["ietf-network-topology:termination-point"] if
                tp["org-openroadm-common-network:tp-type"] == "SRG-TXRX-PP"]
        return pps
    
    # limit available wavelengths for an srg (useful e.g. for AWGs):
    def set_srg_wavelengths(self, srg_id, wavelengths):
        url = (f"{self.baseurl}/config/ietf-network:networks/network/openroadm-topology/node/{srg_id}/"
                "org-openroadm-network-topology:srg-attributes")
        available_wavelengths = [{"index": wl} for wl in wavelengths]
        data = {"org-openroadm-network-topology:srg-attributes": {
                    "available-wavelengths": available_wavelengths}}
        requests.put(url, data=json.dumps(data), headers=self.headers, auth=self.auth)
    
    # "block" an srg pp by setting used wavelength
    def set_srg_pp_used(self, srg_id, tp_id):
        url = (f"{self.baseurl}/config/ietf-network:networks/network/openroadm-topology/node/{srg_id}/"
                f"ietf-network-topology:termination-point/{tp_id}/org-openroadm-network-topology:pp-attributes/used-wavelength/1")
        data = {"used-wavelength": [{
                                "index": 1,
                                "frequency": 196.0,
                                "width": 92}]}
        requests.put(url, data=json.dumps(data), headers=self.headers, auth=self.auth)
        
    # undo a "block on an srg pp by removing used wavelength
    def set_srg_pp_free(self, srg_id, tp_id):
        url = (f"{self.baseurl}/config/ietf-network:networks/network/openroadm-topology/node/{srg_id}/"
                f"ietf-network-topology:termination-point/{tp_id}/org-openroadm-network-topology:pp-attributes")
        requests.delete(url, headers=self.headers, auth=self.auth)
                
    # add OMS information to a link in the topology:
    def add_oms_attributes(self, link, spanloss, fiber_type="smf", length="10000"):
        url = (f"{self.baseurl}/config/ietf-network:networks/network/openroadm-topology/ietf-network-topology:link/{link}/"
               "org-openroadm-network-topology:OMS-attributes/span")
        data = {"span": {
                    "spanloss-current": spanloss,
                    "link-concatenation": [{
                        "SRLG-Id": 0,
                        "fiber-type": fiber_type,
                        "SRLG-length": length}]}}
        requests.put(url, data=json.dumps(data), headers=self.headers, auth=self.auth)
        
    # delete link from topology to limit connectivity (useful for non-direction-less ROADMs):
    def delete_link(self, node_id_1, node_id_2):
        sub_1 = node_id_1.split("-")[-1]
        sub_2 = node_id_2.split("-")[-1]
        tp_1 = "CP" if "SRG" in sub_1 else "CTP"
        tp_2 = "CP" if "SRG" in sub_2 else "CTP"
        end_1 = "-".join([node_id_1, sub_1, tp_1, "TXRX"])
        end_2 = "-".join([node_id_2, sub_2, tp_2, "TXRX"])
        link_id_1 = end_1 + "to" + end_2
        link_id_2 = end_2 + "to" + end_1
        
        url = f"{self.baseurl}/config/ietf-network:networks/network/openroadm-topology/ietf-network-topology:link/{link_id_1}"
        requests.delete(url, headers=self.headers, auth=self.auth)
        url = f"{self.baseurl}/config/ietf-network:networks/network/openroadm-topology/ietf-network-topology:link/{link_id_2}"
        requests.delete(url, headers=self.headers, auth=self.auth)
    
    # some functions based on RPCs defined by TransportPCE API:
    def link_xpdr_roadm(self, xpdr_node_id, xpdr_logical_connection_point, roadm_node_id, srg_logical_connection_point):
        x = xpdr_logical_connection_point.split("-")
        xpdr_num = x[0].lstrip("XPDR")
        network_num = x[1].lstrip("NETWORK")
        srg_num = srg_logical_connection_point.split("-")[0].lstrip("SRG")
        data = {"networkutils:input": {
                    "networkutils:links-input": {
                        "networkutils:xpdr-node": xpdr_node_id,
                        "networkutils:xpdr-num": xpdr_num,
                        "networkutils:network-num": network_num,
                        "networkutils:rdm-node": roadm_node_id,
                        "networkutils:srg-num": srg_num,
                        "networkutils:termination-point-num": srg_logical_connection_point}}}
        url = f"{self.baseurl}/operations/transportpce-networkutils:init-xpdr-rdm-links"
        requests.post(url, data=json.dumps(data), headers=self.headers, auth=self.auth)
        url = f"{self.baseurl}/operations/transportpce-networkutils:init-rdm-xpdr-links"
        requests.post(url, data=json.dumps(data), headers=self.headers, auth=self.auth)
        
    def create_ots_oms(self, node_id, logical_connection_point):
        url = f"{self.baseurl}/operations/transportpce-device-renderer:create-ots-oms"
        data = {
            "input" : {
                "node-id" : node_id,
                "logical-connection-point" : logical_connection_point}}
        requests.post(url, data=json.dumps(data), headers=self.headers, auth=self.auth)
    
    def get_optical_power(self, node_id, logical_connection_point):
        url = f"{self.baseurl}/operations/transportpce-olm:get-pm"
        data = {"input": {
                    "node-id": node_id,
                    "resource-type": "interface",
                    "granularity": "15min",
                    "resource-identifier": {
                        "resource-name" : f"OTS-{logical_connection_point}"}}}
        response = requests.post(url, data=json.dumps(data), headers=self.headers, auth=self.auth)
        return response.json()["output"]
    
    def measure_spanloss(self):
        url = f"{self.baseurl}/operations/transportpce-olm:calculate-spanloss-base"
        data = {"input": {
                    "src-type": "all"}}
        response = requests.post(url, data=json.dumps(data), headers=self.headers, auth=self.auth)
        return response.json()["output"]["spans"]
        
    # measure spanloss for all ROADM-to-ROADM links and update OMS information in topology based on results:
    def measure_and_add_oms_spanloss(self):
        spans = self.measure_spanloss()
        for span in spans:
            self.add_oms_attributes(span["link-id"], float(span["spanloss"]))
        return spans
    
    # OpenROADM service model service-create RPC:
    def create_service(self, node_id_1, node_id_2, request_id = "default_rid", service_name = "default_name", common_id = "default_cid"):
        url = f"{self.baseurl}/operations/org-openroadm-service:service-create"
        port = {"port-device-name": "n/a", "port-type": "n/a", "port-name": "n/a", "port-rack": "n/a", "port-shelf": "n/a"}
        lgx = {"lgx-device-name": "n/a", "lgx-port-name": "n/a", "lgx-port-rack": "n/a", "lgx-port-shelf": "n/a"}
        direction = {"port": port, "lgx": lgx}
        data = {"input": {
                    "sdnc-request-header": {
                        "request-id": request_id,
                        "rpc-action": "service-create"
                    },
                    "service-name": service_name,
                    "common-id": common_id,
                    "connection-type": "service",
                    "service-a-end": {
                        "service-rate": "100",
                        "node-id": node_id_1,
                        "service-format": "Ethernet",
                        "clli": "clli_1",
                        "tx-direction": direction,
                        "rx-direction": direction,
                        "optic-type": "dwdm"
                    },
                    "service-z-end": {
                        "service-rate": "100",
                        "node-id": node_id_2,
                        "service-format": "Ethernet",
                        "clli": "clli_2",
                        "tx-direction": direction,
                        "rx-direction": direction,
                        "optic-type": "dwdm"
                    }
                }
        }
        requests.post(url, data=json.dumps(data), headers=self.headers, auth=self.auth)
        
    # Create service between two XPDRs after linking XPDR ports with ROADM SRG ports and optionally specifying wavelength:
    def provision_xpdr_service(self, node_1, node_2, wl_index = None):
        xpdr_node_id_1 = node_1["xpdr_node_id"]
        xpdr_node_id_2 = node_2["xpdr_node_id"]
        xpdr_lcp_1 = node_1["xpdr_logical_connection_point"]
        xpdr_lcp_2 = node_2["xpdr_logical_connection_point"]
        roadm_node_id_1 = node_1["roadm_node_id"]
        roadm_node_id_2 = node_2["roadm_node_id"]
        srg_lcp_1 = node_1["srg_logical_connection_point"]
        srg_lcp_2 = node_2["srg_logical_connection_point"]
        
        self.link_xpdr_roadm(xpdr_node_id_1, xpdr_lcp_1, roadm_node_id_1, srg_lcp_1)
        self.link_xpdr_roadm(xpdr_node_id_2, xpdr_lcp_2, roadm_node_id_2, srg_lcp_2)
        
        service_name = (f"{xpdr_node_id_1}_{xpdr_lcp_1}_{roadm_node_id_1}_{srg_lcp_1}_to_"
                        f"{xpdr_node_id_2}_{xpdr_lcp_2}_{roadm_node_id_2}_{srg_lcp_2}")
        
        if wl_index is not None:
            srg_id_1 = roadm_node_id_1 + "-" + srg_lcp_1.split("-")[0]
            srg_id_2 = roadm_node_id_2 + "-" + srg_lcp_2.split("-")[0]
            available_wavelengths_1 = self.get_srg_wavelengths(srg_id_1)
            available_wavelengths_2 = self.get_srg_wavelengths(srg_id_2)
            self.set_srg_wavelengths(srg_id_1, [wl_index])
            self.set_srg_wavelengths(srg_id_2, [wl_index])
            service_name += f"_ch{wl_index}"

        self.create_service(xpdr_node_id_1, xpdr_node_id_2, service_name = service_name)
        
        if wl_index is not None:
            self.set_srg_wavelengths(srg_id_1, available_wavelengths_1)
            self.set_srg_wavelengths(srg_id_2, available_wavelengths_2)       
    
    # Create service between two ROADM SRG ports and optionally specify wavelength:
    def provision_roadm_service(self, node_1, node_2, wl_index = None):
        roadm_node_id_1 = node_1["roadm_node_id"]
        roadm_node_id_2 = node_2["roadm_node_id"]
        srg_lcp_1 = node_1["srg_logical_connection_point"]
        srg_lcp_2 = node_2["srg_logical_connection_point"]
        srg_id_1 = roadm_node_id_1 + "-" + srg_lcp_1.split("-")[0]
        srg_id_2 = roadm_node_id_2 + "-" + srg_lcp_2.split("-")[0]
        
        exclude_srgs = [n["node-id"] for n in self.get_topology()["node"] if
                            n["org-openroadm-common-network:node-type"] == "SRG" and
                            n["supporting-node"][0]["node-ref"] in (roadm_node_id_1, roadm_node_id_2) and
                            n["node-id"] not in (srg_id_1, srg_id_2)]

        exclude_srgs_wavelengths = []
        for srg_id in exclude_srgs:
            exclude_srgs_wavelengths.append(self.get_srg_wavelengths(srg_id))
            self.set_srg_wavelengths(srg_id, [])
            
        pps_1 = self.get_srg_pps(srg_id_1)
        pps_2 = self.get_srg_pps(srg_id_2)
                           
        exclude_pps_1 = [pp["tp-id"] for pp in pps_1 if pp["tp-id"] != srg_lcp_1 and
                            (pp.get("org-openroadm-network-topology:pp-attributes") == None or
                            pp.get("org-openroadm-network-topology:pp-attributes").get("used-wavelength") == None)]
                            
        exclude_pps_2 = [pp["tp-id"] for pp in pps_2 if pp["tp-id"] != srg_lcp_2 and
                            (pp.get("org-openroadm-network-topology:pp-attributes") == None or
                            pp.get("org-openroadm-network-topology:pp-attributes").get("used-wavelength") == None)]
        
        for pp in exclude_pps_1:
            self.set_srg_pp_used(srg_id_1, pp)
        
        for pp in exclude_pps_2:
            self.set_srg_pp_used(srg_id_2, pp)
        
        service_name = f"{roadm_node_id_1}_{srg_lcp_1}_to_{roadm_node_id_2}_{srg_lcp_2}"
        
        if wl_index is not None:
            available_wavelengths_1 = self.get_srg_wavelengths(srg_id_1)
            available_wavelengths_2 = self.get_srg_wavelengths(srg_id_2)
            self.set_srg_wavelengths(srg_id_1, [wl_index])
            self.set_srg_wavelengths(srg_id_2, [wl_index])
            service_name += f"_ch{wl_index}"

        self.create_service(roadm_node_id_1, roadm_node_id_2, service_name = service_name)
        
        for srg_id, wavelengths in zip(exclude_srgs, exclude_srgs_wavelengths):
            self.set_srg_wavelengths(srg_id, wavelengths)
            
        for pp in exclude_pps_1:
            self.set_srg_pp_free(srg_id_1, pp)
            
        for pp in exclude_pps_2:
            self.set_srg_pp_free(srg_id_2, pp)
        
        if wl_index is not None:
            self.set_srg_wavelengths(srg_id_1, available_wavelengths_1)
            self.set_srg_wavelengths(srg_id_2, available_wavelengths_2)
    
    # Experimental, not really working:
    def provision_roadm_service_2_stage(self, node_id_1, node_id_2, request_id = "default_rid", service_name = "default_name"):
        url = f"{self.baseurl}/operations/transportpce-pce:path-computation-request"
        service_a_end = {"node-id": node_id_1,
                        "service-rate": "0",
                        "service-format": "OC",
                        "clli": "clli_1"}
        service_z_end = {"node-id": node_id_2,
                        "service-rate": "0",
                        "service-format": "OC",
                        "clli": "clli_2"}
        data = {"input": {
                    "service-name": service_name,
                    "resource-reserve": "true",
                    "pce-metric": "hop-count",
                    "service-handler-header": {
                        "request-id": request_id
                    },
                    "service-a-end": service_a_end,
                    "service-z-end": service_z_end}}
        response = requests.post(url, data=json.dumps(data), headers=self.headers, auth=self.auth)
        
        path_description = response.json()["output"]["response-parameters"]["path-description"]
        wavelength = path_description["aToZ-direction"]["aToZ-wavelength-number"]  
        atoz = path_description["aToZ-direction"]["aToZ"]
        tp_1 = next(r["resource"]["tp-id"] for r in atoz if r["id"] == "0")
        tp_2 = max(atoz, key = lambda r : int(r["id"]))["resource"]["tp-id"]     
        print(f"Wavelength: {wavelength}")
        print(f"Port on {node_id_1}: {tp_1}")
        print(f"Port on {node_id_2}: {tp_2}")
        
        url = f"{self.baseurl}/operations/transportpce-renderer:service-implementation-request"
        data = {"input": {
                    "service-name": service_name,
                    "service-handler-header": {
                        "request-id": request_id
                    },
                    "service-a-end": service_a_end,
                    "service-z-end": service_z_end,
                    "path-description": path_description}}
        requests.post(url, data=json.dumps(data), headers=self.headers, auth=self.auth)
