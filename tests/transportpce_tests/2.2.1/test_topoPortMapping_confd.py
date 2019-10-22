#!/usr/bin/env python

##############################################################################
#Copyright (c) 2017 Orange, Inc. and others.  All rights reserved.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import docker
import json
import os
import psutil
import requests
import signal
import shutil
import subprocess
import time
import unittest
import logging

class TransportPCEtesting(unittest.TestCase):

    confd_container1 = None
    confd_container2 = None
    client = docker.from_env()
    odl_process = None
    restconf_baseurl = "http://localhost:8181/restconf"

#START_IGNORE_XTESTING

    @classmethod
    def __start_confd1(cls):
        cls.confd_container1 = cls.client.containers.run("confd-openroadm", "roadma",
                                      init=True, detach=True, tty=True, remove=True)

    @classmethod
    def __start_confd2(cls):
        cls.confd_container2 = cls.client.containers.run("confd-openroadm", "xpdra",
                                      init=True, detach=True, tty=True, remove=True)

    @classmethod
    def __start_odl(cls):
        executable = "../karaf/target/assembly/bin/karaf"
        with open('odl.log', 'w') as outfile:
            cls.odl_process = subprocess.Popen(
                ["bash", executable, "server"], stdout=outfile,
                stdin=open(os.devnull))

    @classmethod
    def setUpClass(cls):
        cls.__start_confd1()
        time.sleep(20)
        cls.__start_confd2()
        time.sleep(20)
        cls.__start_odl()
        time.sleep(60)

    @classmethod
    def tearDownClass(cls):
        for child in psutil.Process(cls.odl_process.pid).children():
            child.send_signal(signal.SIGINT)
            child.wait()
        cls.odl_process.send_signal(signal.SIGINT)
        cls.odl_process.wait()
        cls.confd_container1.stop()
        cls.confd_container2.stop()

    def setUp(self):
        time.sleep(10)

#END_IGNORE_XTESTING

    #Connect the ROADMA
    def test_01_connect_rdm(self):
        #Config ROADMA
        url = ("{}/config/network-topology:"
                "network-topology/topology/topology-netconf/node/ROADM-A1"
               .format(self.restconf_baseurl))
        data = {"node": [{
             "node-id": "ROADM-A1",
             "netconf-node-topology:username": "admin",
             "netconf-node-topology:password": "admin",
             "netconf-node-topology:host": "172.17.0.2",
             "netconf-node-topology:port": "2022",
             "netconf-node-topology:tcp-only": "false",
             "netconf-node-topology:pass-through": {}}]}
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "PUT", url, data=json.dumps(data), headers=headers,
             auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.created)
        time.sleep(20)

    #Verify the termination points of the ROADMA
    def test_02_compareOpenroadmTopologyPortMapping_rdm(self):
        urlTopo = ("{}/config/ietf-network:networks/network/openroadm-topology"
            .format(self.restconf_baseurl))
        headers = {'content-type': 'application/json'}
        responseTopo = requests.request(
            "GET", urlTopo, headers=headers, auth=('admin', 'admin'))
        resTopo = responseTopo.json()
        nbNode = len(resTopo['network'][0]['node'])
        nbMapCumul = 0
        nbMappings = 0
        for i in range(0, nbNode):
            nodeId = resTopo['network'][0]['node'][i]['node-id']
            print("nodeId={}".format(nodeId))
            nodeMapId = nodeId.split("-")[0] + "-" + nodeId.split("-")[1]
            print("nodeMapId={}".format(nodeMapId))
            urlMapList = "{}/config/transportpce-portmapping:network/nodes/" + nodeMapId
            urlMapListFull = urlMapList.format(self.restconf_baseurl)
            responseMapList = requests.request(
                        "GET", urlMapListFull, headers=headers, auth=('admin', 'admin'))
            resMapList = responseMapList.json()

            nbMappings = len(resMapList['nodes'][0]['mapping']) - nbMapCumul
            nbTp = len(resTopo['network'][0]['node'][i]['ietf-network-topology:termination-point'])
            nbMapCurrent = 0
            for j in range(0, nbTp):
                tpId = resTopo['network'][0]['node'][i]['ietf-network-topology:termination-point'][j]['tp-id']
                if((not "CP" in tpId) and (not "CTP" in tpId)):
                     urlMap = "{}/config/transportpce-portmapping:network/nodes/" + nodeMapId + "/mapping/" + tpId
                     urlMapFull = urlMap.format(self.restconf_baseurl)
                     responseMap = requests.request(
                        "GET", urlMapFull, headers=headers, auth=('admin', 'admin'))
                     self.assertEqual(responseMap.status_code, requests.codes.ok)
                     if(responseMap.status_code == requests.codes.ok):
                        nbMapCurrent += 1
            nbMapCumul += nbMapCurrent
        nbMappings -= nbMapCurrent
        self.assertEqual(nbMappings, 0)

    #Disconnect the ROADMA
    def test_03_disconnect_rdm(self):
        url = ("{}/config/network-topology:"
                "network-topology/topology/topology-netconf/node/ROADM-A1"
               .format(self.restconf_baseurl))
        data = {}
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "DELETE", url, data=json.dumps(data), headers=headers,
             auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)

#     #Connect the XPDRA
    def test_04_connect_xpdr(self):
         #Config XPDRA
         url = ("{}/config/network-topology:"
                 "network-topology/topology/topology-netconf/node/XPDR-A1"
                .format(self.restconf_baseurl))
         data = {"node": [{
              "node-id": "XPDR-A1",
              "netconf-node-topology:username": "admin",
              "netconf-node-topology:password": "admin",
              "netconf-node-topology:host": "172.17.0.3",
              "netconf-node-topology:port": "2022",
              "netconf-node-topology:tcp-only": "false",
              "netconf-node-topology:pass-through": {}}]}
         headers = {'content-type': 'application/json'}
         response = requests.request(
              "PUT", url, data=json.dumps(data), headers=headers,
              auth=('admin', 'admin'))
         self.assertEqual(response.status_code, requests.codes.created)
         time.sleep(20)

#     #Verify the termination points related to XPDR
    def test_05_compareOpenroadmTopologyPortMapping_xpdr(self):
        self.test_02_compareOpenroadmTopologyPortMapping_rdm()

    #Disconnect the XPDRA
    def test_06_disconnect_device(self):
        url = ("{}/config/network-topology:"
               "network-topology/topology/topology-netconf/node/XPDR-A1"
              .format(self.restconf_baseurl))
        data = {}
        headers = {'content-type': 'application/json'}
        response = requests.request(
            "DELETE", url, data=json.dumps(data), headers=headers,
            auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)

if __name__ == "__main__":
    #logging.basicConfig(filename='./transportpce_tests/log/response.log',filemode='w',level=logging.DEBUG)
    #logging.debug('I am there')
    unittest.main(verbosity=2)
