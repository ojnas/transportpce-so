#!/usr/bin/env python

#############################################################################
# Copyright (c) 2017 Orange, Inc. and others.  All rights reserved.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
#############################################################################

import unittest
import requests
import time
import subprocess
import signal
import json
import os
import psutil
import shutil
from unittest.result import failfast


class TransportOlmTesting(unittest.TestCase):

    honeynode_process1 = None
    honeynode_process2 = None
    honeynode_process3 = None
    honeynode_process4 = None
    odl_process = None
    restconf_baseurl = "http://localhost:8181/restconf"

    @classmethod
    def __start_honeynode1(cls):
        executable = ("./honeynode/honeynode-distribution/target/honeynode-distribution-1.18.01-hc"
                      "/honeynode-distribution-1.18.01/honeycomb-tpce")
        if os.path.isfile(executable):
            with open('honeynode1.log', 'w') as outfile:
                cls.honeynode_process1 = subprocess.Popen(
                    [executable, "17830", "sample_configs/ord_2.1/oper-ROADMA-full.xml"],
                    stdout=outfile)

    @classmethod
    def __start_honeynode2(cls):
        executable = ("./honeynode/honeynode-distribution/target/honeynode-distribution-1.18.01-hc"
                      "/honeynode-distribution-1.18.01/honeycomb-tpce")
        if os.path.isfile(executable):
            with open('honeynode2.log', 'w') as outfile:
                cls.honeynode_process2 = subprocess.Popen(
                    [executable, "17831", "sample_configs/ord_2.1/oper-XPDRA.xml"],
                    stdout=outfile)

    @classmethod
    def __start_honeynode3(cls):
        executable = ("./honeynode/honeynode-distribution/target/honeynode-distribution-1.18.01-hc"
                      "/honeynode-distribution-1.18.01/honeycomb-tpce")
        if os.path.isfile(executable):
            with open('honeynode3.log', 'w') as outfile:
                cls.honeynode_process3 = subprocess.Popen(
                    [executable, "17833", "sample_configs/ord_2.1/oper-ROADMC-full.xml"],
                    stdout=outfile)
    @classmethod
    def __start_honeynode4(cls):
        executable = ("./honeynode/honeynode-distribution/target/honeynode-distribution-1.18.01-hc"
                      "/honeynode-distribution-1.18.01/honeycomb-tpce")
        if os.path.isfile(executable):
            with open('honeynode4.log', 'w') as outfile:
                cls.honeynode_process4 = subprocess.Popen(
                    [executable, "17834", "sample_configs/ord_2.1/oper-XPDRC.xml"],
                    stdout=outfile)

    @classmethod
    def __start_odl(cls):
        executable = "../karaf/target/assembly/bin/karaf"
        with open('odl.log', 'w') as outfile:
            cls.odl_process = subprocess.Popen(
                ["bash", executable, "server"], stdout=outfile,
                stdin=open(os.devnull))

    @classmethod
    def setUpClass(cls):
        cls.__start_honeynode1()
        time.sleep(30)
        cls.__start_honeynode2()
        time.sleep(30)
        cls.__start_honeynode3()
        time.sleep(30)
        cls.__start_honeynode4()
        time.sleep(30)
        cls.__start_odl()
        time.sleep(60)

    @classmethod
    def tearDownClass(cls):
        for child in psutil.Process(cls.odl_process.pid).children():
            child.send_signal(signal.SIGINT)
            child.wait()
        cls.odl_process.send_signal(signal.SIGINT)
        cls.odl_process.wait()
        for child in psutil.Process(cls.honeynode_process1.pid).children():
            child.send_signal(signal.SIGINT)
            child.wait()
        cls.honeynode_process1.send_signal(signal.SIGINT)
        cls.honeynode_process1.wait()
        for child in psutil.Process(cls.honeynode_process2.pid).children():
            child.send_signal(signal.SIGINT)
            child.wait()
        cls.honeynode_process2.send_signal(signal.SIGINT)
        cls.honeynode_process2.wait()
        for child in psutil.Process(cls.honeynode_process3.pid).children():
            child.send_signal(signal.SIGINT)
            child.wait()
        cls.honeynode_process3.send_signal(signal.SIGINT)
        cls.honeynode_process3.wait()
        for child in psutil.Process(cls.honeynode_process4.pid).children():
            child.send_signal(signal.SIGINT)
            child.wait()
        cls.honeynode_process4.send_signal(signal.SIGINT)
        cls.honeynode_process4.wait()

    def setUp(self):
        print ("execution of {}".format(self.id().split(".")[-1]))
        time.sleep(1)

    def test_01_xpdrA_device_connected(self):
        url = ("{}/config/network-topology:"
               "network-topology/topology/topology-netconf/node/XPDRA"
              .format(self.restconf_baseurl))
        data = {"node": [{
            "node-id": "XPDRA",
            "netconf-node-topology:username": "admin",
            "netconf-node-topology:password": "admin",
            "netconf-node-topology:host": "127.0.0.1",
            "netconf-node-topology:port": "17831",
            "netconf-node-topology:tcp-only": "false",
            "netconf-node-topology:pass-through": {}}]}
        headers = {'content-type': 'application/json'}
        response = requests.request(
            "PUT", url, data=json.dumps(data), headers=headers,
            auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.created)
        time.sleep(20)

    def test_02_xpdrC_device_connected(self):
        url = ("{}/config/network-topology:"
               "network-topology/topology/topology-netconf/node/XPDRC"
              .format(self.restconf_baseurl))
        data = {"node": [{
            "node-id": "XPDRC",
            "netconf-node-topology:username": "admin",
            "netconf-node-topology:password": "admin",
            "netconf-node-topology:host": "127.0.0.1",
            "netconf-node-topology:port": "17834",
            "netconf-node-topology:tcp-only": "false",
            "netconf-node-topology:pass-through": {}}]}
        headers = {'content-type': 'application/json'}
        response = requests.request(
            "PUT", url, data=json.dumps(data), headers=headers,
            auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.created)
        time.sleep(20)

    def test_03_rdmA_device_connected(self):
        url = ("{}/config/network-topology:"
               "network-topology/topology/topology-netconf/node/ROADMA"
               .format(self.restconf_baseurl))
        data = {"node": [{
             "node-id": "ROADMA",
             "netconf-node-topology:username": "admin",
             "netconf-node-topology:password": "admin",
             "netconf-node-topology:host": "127.0.0.1",
             "netconf-node-topology:port": "17830",
             "netconf-node-topology:tcp-only": "false",
             "netconf-node-topology:pass-through": {}}]}
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "PUT", url, data=json.dumps(data), headers=headers,
              auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.created)
        time.sleep(20)

    def test_04_rdmC_device_connected(self):
        url = ("{}/config/network-topology:"
               "network-topology/topology/topology-netconf/node/ROADMC"
               .format(self.restconf_baseurl))
        data = {"node": [{
             "node-id": "ROADMC",
             "netconf-node-topology:username": "admin",
             "netconf-node-topology:password": "admin",
             "netconf-node-topology:host": "127.0.0.1",
             "netconf-node-topology:port": "17833",
             "netconf-node-topology:tcp-only": "false",
             "netconf-node-topology:pass-through": {}}]}
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "PUT", url, data=json.dumps(data), headers=headers,
              auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.created)
        time.sleep(20)

    def test_05_connect_xprdA_to_roadmA(self):
        url = "{}/operations/networkutils:init-xpdr-rdm-links".format(self.restconf_baseurl)
        data = {
            "networkutils:input": {
                "networkutils:links-input": {
                    "networkutils:xpdr-node": "XPDRA",
                    "networkutils:xpdr-num": "1",
                    "networkutils:network-num": "1",
                    "networkutils:rdm-node": "ROADMA",
                    "networkutils:srg-num": "1",
                    "networkutils:termination-point-num": "SRG1-PP1-TXRX"
                }
            }
        }
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "POST", url, data=json.dumps(data),
             headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertIn('Xponder Roadm Link created successfully', res["output"]["result"])

    def test_06_connect_roadmA_to_xpdrA(self):
        url = "{}/operations/networkutils:init-rdm-xpdr-links".format(self.restconf_baseurl)
        data = {
            "networkutils:input": {
                "networkutils:links-input": {
                    "networkutils:xpdr-node": "XPDRA",
                    "networkutils:xpdr-num": "1",
                    "networkutils:network-num": "1",
                    "networkutils:rdm-node": "ROADMA",
                    "networkutils:srg-num": "1",
                    "networkutils:termination-point-num": "SRG1-PP1-TXRX"
                }
            }
        }
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "POST", url, data=json.dumps(data),
             headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertIn('Roadm Xponder links created successfully', res["output"]["result"])

    def test_07_connect_xprdC_to_roadmC(self):
        url = "{}/operations/networkutils:init-xpdr-rdm-links".format(self.restconf_baseurl)
        data = {
            "networkutils:input": {
                "networkutils:links-input": {
                    "networkutils:xpdr-node": "XPDRC",
                    "networkutils:xpdr-num": "1",
                    "networkutils:network-num": "1",
                    "networkutils:rdm-node": "ROADMC",
                    "networkutils:srg-num": "1",
                    "networkutils:termination-point-num": "SRG1-PP1-TXRX"
                }
            }
        }
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "POST", url, data=json.dumps(data),
             headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertIn('Xponder Roadm Link created successfully', res["output"]["result"])

    def test_08_connect_roadmC_to_xpdrC(self):
        url = "{}/operations/networkutils:init-rdm-xpdr-links".format(self.restconf_baseurl)
        data = {
            "networkutils:input": {
                "networkutils:links-input": {
                    "networkutils:xpdr-node": "XPDRC",
                    "networkutils:xpdr-num": "1",
                    "networkutils:network-num": "1",
                    "networkutils:rdm-node": "ROADMC",
                    "networkutils:srg-num": "1",
                    "networkutils:termination-point-num": "SRG1-PP1-TXRX"
                }
            }
        }
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "POST", url, data=json.dumps(data),
             headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertIn('Roadm Xponder links created successfully', res["output"]["result"])

    def test_09_create_OTS_ROADMA(self):
        url = "{}/operations/renderer:create-ots-oms".format(self.restconf_baseurl)
        data = {
            "input" : {
                "node-id" : "ROADMA",
                "logical-connection-point" : "DEG1-TTP-TXRX"
            }
        }
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "POST", url, data=json.dumps(data),
             headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertIn('Interfaces OTS-DEG1-TTP-TXRX - OMS-DEG1-TTP-TXRX successfully created on node ROADMA',
                      res["output"]["result"])

    def test_10_create_OTS_ROADMC(self):
        url = "{}/operations/renderer:create-ots-oms".format(self.restconf_baseurl)
        data = {
            "input" : {
                "node-id" : "ROADMC",
                "logical-connection-point" : "DEG2-TTP-TXRX"
            }
        }
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "POST", url, data=json.dumps(data),
             headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertIn('Interfaces OTS-DEG2-TTP-TXRX - OMS-DEG2-TTP-TXRX successfully created on node ROADMC',
                      res["output"]["result"])

    def test_11_get_PM_ROADMA(self):
        url = "{}/operations/olm:get-pm".format(self.restconf_baseurl)
        data = {
            "input": {
                "node-id": "ROADMA",
                "resource-type": "interface",
                "granularity": "15min",
                "resource-identifier": {
                    "resource-name" : "OTS-DEG1-TTP-TXRX"
                }
            }
        }
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "POST", url, data=json.dumps(data),
             headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertIn({
                "pmparameter-name": "OpticalPowerOutput",
                "pmparameter-value": "2.5"
            }, res["output"]["measurements"])
        self.assertIn({
                "pmparameter-name": "OpticalReturnLoss",
                "pmparameter-value": "49.9"
            }, res["output"]["measurements"])
        self.assertIn({
                "pmparameter-name": "OpticalPowerInput",
                "pmparameter-value": "3"
            }, res["output"]["measurements"])

    def test_12_get_PM_ROADMC(self):
        url = "{}/operations/olm:get-pm".format(self.restconf_baseurl)
        data = {
            "input": {
                "node-id": "ROADMC",
                "resource-type": "interface",
                "granularity": "15min",
                "resource-identifier": {
                    "resource-name" : "OTS-DEG2-TTP-TXRX"
                }
            }
        }
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "POST", url, data=json.dumps(data),
             headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertIn({
                "pmparameter-name": "OpticalPowerOutput",
                "pmparameter-value": "18.1"
            }, res["output"]["measurements"])
        self.assertIn({
                "pmparameter-name": "OpticalReturnLoss",
                "pmparameter-value": "48.8"
            }, res["output"]["measurements"])
        self.assertIn({
                "pmparameter-name": "OpticalPowerInput",
                "pmparameter-value": "-3.2"
            }, res["output"]["measurements"])

    def test_13_calculate_span_loss_base_ROADMA_ROADMC(self):
        url = "{}/operations/olm:calculate-spanloss-base".format(self.restconf_baseurl)
        data = {
            "input": {
                "src-type": "link",
                "link-id": "ROADMA-DEG1-DEG1-TTP-TXRXtoROADMC-DEG2-DEG2-TTP-TXRX"
            }
        }
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "POST", url, data=json.dumps(data),
             headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertIn('Success',
                      res["output"]["result"])
        time.sleep(5)

    def test_14_calculate_span_loss_base_ROADMC_ROADMA(self):
        url = "{}/operations/olm:calculate-spanloss-base".format(self.restconf_baseurl)
        data = {
            "input": {
                "src-type": "link",
                "link-id": "ROADMC-DEG2-DEG2-TTP-TXRXtoROADMA-DEG1-DEG1-TTP-TXRX"
            }
        }
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "POST", url, data=json.dumps(data),
             headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertIn('Success',
                      res["output"]["result"])
        time.sleep(5)

    def test_15_get_OTS_DEG1_TTP_TXRX_ROADMA(self):
        url = ("{}/config/network-topology:network-topology/topology/topology-netconf/"
               "node/ROADMA/yang-ext:mount/org-openroadm-device:org-openroadm-device/interface/OTS-DEG1-TTP-TXRX/"
               "org-openroadm-optical-transport-interfaces:ots".format(self.restconf_baseurl))
        headers = {'content-type': 'application/json'}
        response = requests.request(
            "GET", url, headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertEqual(6, res['org-openroadm-optical-transport-interfaces:ots']['span-loss-transmit'])
        self.assertEqual(15, res['org-openroadm-optical-transport-interfaces:ots']['span-loss-receive'])

    def test_16_get_OTS_DEG2_TTP_TXRX_ROADMC(self):
        url = ("{}/config/network-topology:network-topology/topology/topology-netconf/"
               "node/ROADMC/yang-ext:mount/org-openroadm-device:org-openroadm-device/interface/OTS-DEG2-TTP-TXRX/"
               "org-openroadm-optical-transport-interfaces:ots".format(self.restconf_baseurl))
        headers = {'content-type': 'application/json'}
        response = requests.request(
            "GET", url, headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertEqual(15, res['org-openroadm-optical-transport-interfaces:ots']['span-loss-transmit'])
        self.assertEqual(6, res['org-openroadm-optical-transport-interfaces:ots']['span-loss-receive'])

    def test_17_servicePath_create_AToZ(self):
        url = "{}/operations/renderer:service-path".format(self.restconf_baseurl)
        data = {
            "input": {
                "service-name": "test",
                "wave-number": "1",
                "modulation-format": "qpsk",
                "operation": "create",
                "nodes": [
                    {
                        "dest-tp": "XPDR1-NETWORK1",
                        "src-tp": "XPDR1-CLIENT1",
                        "node-id": "XPDRA"
                    },
                    {
                        "dest-tp": "DEG1-TTP-TXRX",
                        "src-tp": "SRG1-PP1-TXRX",
                        "node-id": "ROADMA"
                    },
                    {
                        "dest-tp": "SRG1-PP1-TXRX",
                        "src-tp": "DEG2-TTP-TXRX",
                        "node-id": "ROADMC"
                    },
                    {
                        "dest-tp": "XPDR1-CLIENT1",
                        "src-tp": "XPDR1-NETWORK1",
                        "node-id": "XPDRC"
                    }
                ]
            }
        }
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "POST", url, data=json.dumps(data),
             headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertIn('Roadm-connection successfully created for nodes', res["output"]["result"])
        time.sleep(40)

    def test_18_servicePath_create_ZToA(self):
        url = "{}/operations/renderer:service-path".format(self.restconf_baseurl)
        data = {
            "input": {
                "service-name": "test",
                "wave-number": "1",
                "modulation-format": "qpsk",
                "operation": "create",
                "nodes": [
                    {
                        "dest-tp": "XPDR1-NETWORK1",
                        "src-tp": "XPDR1-CLIENT1",
                        "node-id": "XPDRC"
                    },
                    {
                        "dest-tp": "DEG2-TTP-TXRX",
                        "src-tp": "SRG1-PP1-TXRX",
                        "node-id": "ROADMC"
                    },
                    {
                        "src-tp": "DEG1-TTP-TXRX",
                        "dest-tp": "SRG1-PP1-TXRX",
                        "node-id": "ROADMA"
                    },
                    {
                        "src-tp": "XPDR1-NETWORK1",
                        "dest-tp": "XPDR1-CLIENT1",
                        "node-id": "XPDRA"
                    }
                ]
            }
        }
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "POST", url, data=json.dumps(data),
             headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertIn('Roadm-connection successfully created for nodes', res["output"]["result"])
        time.sleep(40)

    def test_19_service_power_setup_XPDRA_XPDRC(self):
        url = "{}/operations/olm:service-power-setup".format(self.restconf_baseurl)
        data = {
            "input": {
                "service-name": "test",
                "wave-number": 1,
                "nodes": [
                    {
                        "dest-tp": "XPDR1-NETWORK1",
                        "src-tp": "XPDR1-CLIENT1",
                        "node-id": "XPDRA"
                    },
                    {
                        "dest-tp": "DEG1-TTP-TXRX",
                        "src-tp": "SRG1-PP1-TXRX",
                        "node-id": "ROADMA"
                    },
                    {
                        "dest-tp": "SRG1-PP1-TXRX",
                        "src-tp": "DEG2-TTP-TXRX",
                        "node-id": "ROADMC"
                    },
                    {
                        "dest-tp": "XPDR1-CLIENT1",
                        "src-tp": "XPDR1-NETWORK1",
                        "node-id": "XPDRC"
                    }
                ]
            }
        }
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "POST", url, data=json.dumps(data),
             headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertIn('Success', res["output"]["result"])

    def test_20_get_interface_XPDRA_XPDR1_NETWORK1(self):
        url = ("{}/config/network-topology:network-topology/topology/topology-netconf/node/XPDRA/yang-ext:mount/"
               "org-openroadm-device:org-openroadm-device/interface/XPDR1-NETWORK1-1/"
               "org-openroadm-optical-channel-interfaces:och".format(self.restconf_baseurl))
        headers = {'content-type': 'application/json'}
        response = requests.request(
            "GET", url, headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertEqual(0, res['org-openroadm-optical-channel-interfaces:och']['transmit-power'])
        self.assertEqual(1, res['org-openroadm-optical-channel-interfaces:och']['wavelength-number'])

    def test_21_get_roadmconnection_ROADMA(self):
        url = ("{}/config/network-topology:network-topology/topology/topology-netconf/node/ROADMA/yang-ext:mount/"
               "org-openroadm-device:org-openroadm-device/roadm-connections/"
               "SRG1-PP1-TXRX-DEG1-TTP-TXRX-1".format(self.restconf_baseurl))
        headers = {'content-type': 'application/json'}
        response = requests.request(
            "GET", url, headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertEqual("gainLoss", res['roadm-connections'][0]['opticalControlMode'])
        self.assertEqual(-3, res['roadm-connections'][0]['target-output-power'])

    def test_22_get_roadmconnection_ROADMC(self):
        url = ("{}/config/network-topology:network-topology/topology/topology-netconf/node/ROADMC/yang-ext:mount/"
               "org-openroadm-device:org-openroadm-device/roadm-connections/"
               "DEG2-TTP-TXRX-SRG1-PP1-TXRX-1".format(self.restconf_baseurl))
        headers = {'content-type': 'application/json'}
        response = requests.request(
            "GET", url, headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertEqual("power", res['roadm-connections'][0]['opticalControlMode'])

    def test_23_service_power_setup_XPDRC_XPDRA(self):
        url = "{}/operations/olm:service-power-setup".format(self.restconf_baseurl)
        data = {
            "input": {
                "service-name": "test",
                "wave-number": 1,
                "nodes": [
                    {
                        "dest-tp": "XPDR1-NETWORK1",
                        "src-tp": "XPDR1-CLIENT1",
                        "node-id": "XPDRC"
                    },
                    {
                        "dest-tp": "DEG2-TTP-TXRX",
                        "src-tp": "SRG1-PP1-TXRX",
                        "node-id": "ROADMC"
                    },
                    {
                        "src-tp": "DEG1-TTP-TXRX",
                        "dest-tp": "SRG1-PP1-TXRX",
                        "node-id": "ROADMA"
                    },
                    {
                        "src-tp": "XPDR1-NETWORK1",
                        "dest-tp": "XPDR1-CLIENT1",
                        "node-id": "XPDRA"
                    }
                ]
            }
        }
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "POST", url, data=json.dumps(data),
             headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertIn('Success', res["output"]["result"])

    def test_24_get_interface_XPDRC_XPDR1_NETWORK1(self):
        url = ("{}/config/network-topology:network-topology/topology/topology-netconf/node/XPDRC/yang-ext:mount/"
               "org-openroadm-device:org-openroadm-device/interface/XPDR1-NETWORK1-1/"
               "org-openroadm-optical-channel-interfaces:och".format(self.restconf_baseurl))
        headers = {'content-type': 'application/json'}
        response = requests.request(
            "GET", url, headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertEqual(-5, res['org-openroadm-optical-channel-interfaces:och']['transmit-power'])
        self.assertEqual(1, res['org-openroadm-optical-channel-interfaces:och']['wavelength-number'])

    def test_25_get_roadmconnection_ROADMC(self):
        url = ("{}/config/network-topology:network-topology/topology/topology-netconf/node/ROADMC/yang-ext:mount/"
               "org-openroadm-device:org-openroadm-device/roadm-connections/"
               "SRG1-PP1-TXRX-DEG2-TTP-TXRX-1".format(self.restconf_baseurl))
        headers = {'content-type': 'application/json'}
        response = requests.request(
            "GET", url, headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertEqual("gainLoss", res['roadm-connections'][0]['opticalControlMode'])
        self.assertEqual(2, res['roadm-connections'][0]['target-output-power'])

    def test_26_service_power_turndown_XPDRA_XPDRC(self):
        url = "{}/operations/olm:service-power-turndown".format(self.restconf_baseurl)
        data = {
            "input": {
                "service-name": "test",
                "wave-number": 1,
                "nodes": [
                    {
                        "dest-tp": "XPDR1-NETWORK1",
                        "src-tp": "XPDR1-CLIENT1",
                        "node-id": "XPDRA"
                    },
                    {
                        "dest-tp": "DEG1-TTP-TXRX",
                        "src-tp": "SRG1-PP1-TXRX",
                        "node-id": "ROADMA"
                    },
                    {
                        "dest-tp": "SRG1-PP1-TXRX",
                        "src-tp": "DEG2-TTP-TXRX",
                        "node-id": "ROADMC"
                    },
                    {
                        "dest-tp": "XPDR1-CLIENT1",
                        "src-tp": "XPDR1-NETWORK1",
                        "node-id": "XPDRC"
                    }
                ]
            }
        }
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "POST", url, data=json.dumps(data),
             headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertIn('Success', res["output"]["result"])

    def test_27_get_roadmconnection_ROADMA(self):
        url = ("{}/config/network-topology:network-topology/topology/topology-netconf/node/ROADMA/yang-ext:mount/"
               "org-openroadm-device:org-openroadm-device/roadm-connections/"
               "SRG1-PP1-TXRX-DEG1-TTP-TXRX-1".format(self.restconf_baseurl))
        headers = {'content-type': 'application/json'}
        response = requests.request(
            "GET", url, headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertEqual("off", res['roadm-connections'][0]['opticalControlMode'])
        self.assertEqual(-60, res['roadm-connections'][0]['target-output-power'])

    def test_28_get_roadmconnection_ROADMC(self):
        url = ("{}/config/network-topology:network-topology/topology/topology-netconf/node/ROADMC/yang-ext:mount/"
               "org-openroadm-device:org-openroadm-device/roadm-connections/"
               "DEG2-TTP-TXRX-SRG1-PP1-TXRX-1".format(self.restconf_baseurl))
        headers = {'content-type': 'application/json'}
        response = requests.request(
            "GET", url, headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertEqual("off", res['roadm-connections'][0]['opticalControlMode'])

    def test_29_servicePath_delete_AToZ(self):
        url = "{}/operations/renderer:service-path".format(self.restconf_baseurl)
        data = {
            "input": {
                "service-name": "test",
                "wave-number": "1",
                "modulation-format": "qpsk",
                "operation": "delete",
                "nodes": [
                    {
                        "dest-tp": "XPDR1-NETWORK1",
                        "src-tp": "XPDR1-CLIENT1",
                        "node-id": "XPDRA"
                    },
                    {
                        "dest-tp": "DEG1-TTP-TXRX",
                        "src-tp": "SRG1-PP1-TXRX",
                        "node-id": "ROADMA"
                    },
                    {
                        "dest-tp": "SRG1-PP1-TXRX",
                        "src-tp": "DEG2-TTP-TXRX",
                        "node-id": "ROADMC"
                    },
                    {
                        "dest-tp": "XPDR1-CLIENT1",
                        "src-tp": "XPDR1-NETWORK1",
                        "node-id": "XPDRC"
                    }
                ]
            }
        }
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "POST", url, data=json.dumps(data),
             headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertIn('Request processed', res["output"]["result"])
        time.sleep(10)

    def test_30_servicePath_delete_ZToA(self):
        url = "{}/operations/renderer:service-path".format(self.restconf_baseurl)
        data = {
            "input": {
                "service-name": "test",
                "wave-number": "1",
                "modulation-format": "qpsk",
                "operation": "delete",
                "nodes": [
                    {
                        "dest-tp": "XPDR1-NETWORK1",
                        "src-tp": "XPDR1-CLIENT1",
                        "node-id": "XPDRC"
                    },
                    {
                        "dest-tp": "DEG2-TTP-TXRX",
                        "src-tp": "SRG1-PP1-TXRX",
                        "node-id": "ROADMC"
                    },
                    {
                        "src-tp": "DEG1-TTP-TXRX",
                        "dest-tp": "SRG1-PP1-TXRX",
                        "node-id": "ROADMA"
                    },
                    {
                        "src-tp": "XPDR1-NETWORK1",
                        "dest-tp": "XPDR1-CLIENT1",
                        "node-id": "XPDRA"
                    }
                ]
            }
        }
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "POST", url, data=json.dumps(data),
             headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertIn('Request processed', res["output"]["result"])
        time.sleep(10)

    """to test case where SRG where the xpdr is connected to has no optical range data"""

    def test_31_connect_xprdA_to_roadmA(self):
        url = "{}/operations/networkutils:init-xpdr-rdm-links".format(self.restconf_baseurl)
        data = {
            "networkutils:input": {
                "networkutils:links-input": {
                    "networkutils:xpdr-node": "XPDRA",
                    "networkutils:xpdr-num": "1",
                    "networkutils:network-num": "2",
                    "networkutils:rdm-node": "ROADMA",
                    "networkutils:srg-num": "1",
                    "networkutils:termination-point-num": "SRG1-PP2-TXRX"
                }
            }
        }
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "POST", url, data=json.dumps(data),
             headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertIn('Xponder Roadm Link created successfully', res["output"]["result"])

    def test_32_connect_roadmA_to_xpdrA(self):
        url = "{}/operations/networkutils:init-rdm-xpdr-links".format(self.restconf_baseurl)
        data = {
            "networkutils:input": {
                "networkutils:links-input": {
                    "networkutils:xpdr-node": "XPDRA",
                    "networkutils:xpdr-num": "1",
                    "networkutils:network-num": "2",
                    "networkutils:rdm-node": "ROADMA",
                    "networkutils:srg-num": "1",
                    "networkutils:termination-point-num": "SRG1-PP2-TXRX"
                }
            }
        }
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "POST", url, data=json.dumps(data),
             headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertIn('Roadm Xponder links created successfully', res["output"]["result"])

    def test_33_servicePath_create_AToZ(self):
        url = "{}/operations/renderer:service-path".format(self.restconf_baseurl)
        data = {
            "input": {
                "service-name": "test2",
                "wave-number": "2",
                "modulation-format": "qpsk",
                "operation": "create",
                "nodes": [
                    {
                        "dest-tp": "XPDR1-NETWORK2",
                        "src-tp": "XPDR1-CLIENT2",
                        "node-id": "XPDRA"
                    },
                    {
                        "dest-tp": "DEG1-TTP-TXRX",
                        "src-tp": "SRG1-PP2-TXRX",
                        "node-id": "ROADMA"
                    }
                ]
            }
        }
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "POST", url, data=json.dumps(data),
             headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertIn('Roadm-connection successfully created for nodes', res["output"]["result"])
        time.sleep(40)

    def test_34_get_interface_XPDRA_XPDR1_NETWORK2(self):
        url = ("{}/config/network-topology:network-topology/topology/topology-netconf/node/XPDRA/yang-ext:mount/"
               "org-openroadm-device:org-openroadm-device/interface/XPDR1-NETWORK2-2/"
               "org-openroadm-optical-channel-interfaces:och".format(self.restconf_baseurl))
        headers = {'content-type': 'application/json'}
        response = requests.request(
            "GET", url, headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertEqual(-5, res['org-openroadm-optical-channel-interfaces:och']['transmit-power'])
        self.assertEqual(2, res['org-openroadm-optical-channel-interfaces:och']['wavelength-number'])

    def test_35_servicePath_delete_AToZ(self):
        url = "{}/operations/renderer:service-path".format(self.restconf_baseurl)
        data = {
            "input": {
                "service-name": "test",
                "wave-number": "1",
                "modulation-format": "qpsk",
                "operation": "delete",
                "nodes": [
                    {
                        "dest-tp": "XPDR1-NETWORK2",
                        "src-tp": "XPDR1-CLIENT2",
                        "node-id": "XPDRA"
                    },
                    {
                        "dest-tp": "DEG1-TTP-TXRX",
                        "src-tp": "SRG1-PP2-TXRX",
                        "node-id": "ROADMA"
                    }
                ]
            }
        }
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "POST", url, data=json.dumps(data),
             headers=headers, auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        res = response.json()
        self.assertIn('Request processed', res["output"]["result"])
        time.sleep(10)

    def test_36_xpdrA_device_disconnected(self):
        url = ("{}/config/network-topology:"
                "network-topology/topology/topology-netconf/node/XPDRA"
               .format(self.restconf_baseurl))
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "DELETE", url, headers=headers,
             auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        time.sleep(10)

    def test_37_xpdrC_device_disconnected(self):
        url = ("{}/config/network-topology:"
                "network-topology/topology/topology-netconf/node/XPDRC"
               .format(self.restconf_baseurl))
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "DELETE", url, headers=headers,
             auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        time.sleep(10)

    def test_38_rdmA_device_disconnected(self):
        url = ("{}/config/network-topology:"
                "network-topology/topology/topology-netconf/node/ROADMA"
               .format(self.restconf_baseurl))
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "DELETE", url, headers=headers,
             auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        time.sleep(10)

    def test_39_rdmC_device_disconnected(self):
        url = ("{}/config/network-topology:"
                "network-topology/topology/topology-netconf/node/ROADMC"
               .format(self.restconf_baseurl))
        headers = {'content-type': 'application/json'}
        response = requests.request(
             "DELETE", url, headers=headers,
             auth=('admin', 'admin'))
        self.assertEqual(response.status_code, requests.codes.ok)
        time.sleep(10)

if __name__ == "__main__":
    unittest.main(verbosity=2)
