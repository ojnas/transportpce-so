#!/usr/bin/env python

from transportpce import Controller

tpce = Controller()

tpce.add_oms_attributes("ROADM-A1-DEG2-DEG2-TTP-TXRXtoROADM-C1-DEG1-DEG1-TTP-TXRX", 17.0)
tpce.add_oms_attributes("ROADM-C1-DEG1-DEG1-TTP-TXRXtoROADM-A1-DEG2-DEG2-TTP-TXRX", 18.0)
tpce.add_oms_attributes("ROADM-A1-DEG1-DEG1-TTP-TXRXtoROADM-B1-DEG1-DEG1-TTP-TXRX", 19.0)
tpce.add_oms_attributes("ROADM-B1-DEG1-DEG1-TTP-TXRXtoROADM-A1-DEG1-DEG1-TTP-TXRX", 20.0)
tpce.add_oms_attributes("ROADM-B1-DEG2-DEG2-TTP-TXRXtoROADM-C1-DEG2-DEG2-TTP-TXRX", 21.0)
tpce.add_oms_attributes("ROADM-C1-DEG2-DEG2-TTP-TXRXtoROADM-B1-DEG2-DEG2-TTP-TXRX", 22.0)

#tpce.link_xpdr_roadm("XPDR-A1", "XPDR1-NETWORK1", "ROADM-A1", "SRG1-PP1-TXRX")
#tpce.link_xpdr_roadm("XPDR-C1", "XPDR1-NETWORK1", "ROADM-C1", "SRG1-PP1-TXRX")

#topology = tpce.get_topology()
#print(json.dumps(topology, indent = 4))

