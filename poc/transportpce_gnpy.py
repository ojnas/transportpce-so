#!/usr/bin/env python

from gnpy.core.elements import Transceiver, Fiber, Edfa
from gnpy.core.info import create_input_spectral_information
from collections import namedtuple
from math import log10

def calculate_gsnr(path, topology):

    links = {l["link-id"]: l for l in topology["ietf-network-topology:link"]}
    
    path.sort(key = lambda x: int(x["id"]))
    
    spans = [links[p["resource"]["link-id"]]["org-openroadm-network-topology:OMS-attributes"]["span"]
                    for p in path if "link-id" in p["resource"] and
                    links[p["resource"]["link-id"]]["org-openroadm-common-network:link-type"] == "ROADM-TO-ROADM"]
    
    f_min = 192e12
    f_max = 196e12
    spacing = 100e9
    roll_off = 0.15
    baud_rate = 32e9
    tx_osnr = 33
    power_in = -16.25
    power = 10**(power_in / 10) / 1000
    
    si = create_input_spectral_information(f_min, f_max, roll_off, baud_rate, power, spacing)
    
    fiber_types = {
                    "smf": {"dispersion": 16.7e-06, "gamma": 1.27e-3},
                    "nz-dsf": {"dispersion": 5e-06, "gamma": 1.46e-3},
                    "eleaf": {"dispersion": 4e-06, "gamma": 1.41e-3},
                    "oleaf": {"dispersion": 4e-06, "gamma": 1.41e-3},
                    "truewave": {"dispersion": 4.3e-06, "gamma": 1.95e-3},
                    "truewavec": {"dispersion": 7.2e-06, "gamma": 1.84e-3},
                    "ull": {"dispersion": 18e-06, "gamma": 0.81e-3}
                    }
        
    fiber_params = {
                    "length_units": "km",
                    "att_in": 0,
                    "con_in": 0.5,
                    "con_out": 0.5
                    }
    
    edfa_params = {
                    "type_variety": "std_fixed_gain",
                    "type_def": "fixed_gain",
                    "gain_flatmax": 32,
                    "gain_min": 0,
                    "p_max": 21.82,
                    "nf_fit_coeff": None,
                    "allowed_for_design": False,
                    "f_min": 191.35e12,
                    "f_max": 196.1e12,
                    "nf_ripple": [0] * 96,
                    "gain_ripple": [0] * 96,
                    "dgt": [1] * 96
                    }
                    
    edfa_operational = {
                        "tilt_target": 0,
                        "out_voa": 0
                        }
    
    Model_fg = namedtuple('Model_fg', 'nf0')
    c58 = -10 * log10(6.62607015e-34 * 12.5e9 * 194e12 * 1000)
    
    for i, span in enumerate(spans):
        loss = span["spanloss-current"]
        length = span["link-concatenation"][0]["SRLG-length"] / 1000
        fiber_type = span["link-concatenation"][0]["fiber-type"]
        
        fiber_params.update(fiber_types.get(fiber_type, fiber_types["smf"]))
        fiber_params["type_variety"] = fiber_type
        fiber_params["length"] = length
        fiber_params["loss_coef"] = (loss - 1) / length
        
        edfa_params["nf_model"] = Model_fg(c58 + power_in - min((4 * power_in + 275) / 7, 33))
        
        power_out = min(loss - 12.5, 3)
        edfa_operational["gain_target"] = power_out - power_in
        
        amp = Edfa(uid = "node_" + str(i), params = edfa_params, operational = edfa_operational)
        fiber = Fiber(uid = "fiber_" + str(i), params = fiber_params)
        
        si = fiber(amp(si))
        power_in = power_out - loss
    
    edfa_params["nf_model"] = Model_fg(c58 + power_in - min((4 * power_in + 275) / 7, 33))
    edfa_operational["gain_target"] = -power_in
    
    amp = Edfa(uid = "node_" + str(i+1), params = edfa_params, operational = edfa_operational)
    
    si = amp(si)
    
    trx = Transceiver(uid = "trx")
    trx(si)
    trx.update_snr(tx_osnr)
    
    return round(min(trx.osnr_ase_01nm), 1), round(min(trx.snr_01nm), 1)
    
    

