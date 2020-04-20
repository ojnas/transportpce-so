#!/usr/bin/env python

import yaml
from copy import deepcopy
import networkx as nx
import plotly.graph_objects as go

def graph_from_topology(topology, G_old = None):
    
    G = nx.DiGraph()
   
    for node in topology["node"]:
        G.add_node(node["node-id"], node_info = node)

    for link in topology["ietf-network-topology:link"]:
        if link["org-openroadm-common-network:link-type"] == "ROADM-TO-ROADM":          
            length = link.get("org-openroadm-network-topology:OMS-attributes", {}).get("span", {}).get("link-concatenation", [{}])[0].get("SRLG-length")
            weight = length / 5000 if length is not None else 10
        elif link["org-openroadm-common-network:link-type"] == "EXPRESS-LINK":
            weight = 1.5
        else:
            weight = 1
        G.add_edge(link["source"]["source-node"], link["destination"]["dest-node"], link_info = link, weight = weight)

    if G_old is None or not nx.faster_could_be_isomorphic(G, G_old):
        pos = nx.kamada_kawai_layout(G)
        pos = {n: list(p) for n, p in pos.items()}            
    else:
        pos = nx.get_node_attributes(G_old, "pos")
        
    nx.set_node_attributes(G, pos, "pos")
    return G

def figure_from_graph(G, port_mapping = None):

    edge_x = []
    edge_y = []
    edge_hover_x = []
    edge_hover_y = []
    edge_hovertext = []
    seen_edges = []
    for edge in G.edges():
        opposite_edge = (edge[1], edge[0])
        if opposite_edge in seen_edges:
            continue
        x0, y0 = G.nodes[edge[0]]["pos"]
        x1, y1 = G.nodes[edge[1]]["pos"]   
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_hover_x.append((x0 + x1) / 2)
        edge_hover_y.append((y0 + y1) / 2)   
        edge_hovertext.append("<br>".join([f"Direction {edge[0]} -> {edge[1]}:", yaml.dump(G.edges[edge]["link_info"]).replace("\n", "<br>"),
                                f"Direction {edge[1]} -> {edge[0]}:", yaml.dump(G.edges[opposite_edge]["link_info"]).replace("\n", "<br>")]))
        seen_edges.append(edge)

    edge_trace = go.Scatter(x=edge_x, y=edge_y,
                            line=dict(color="#fb9f3a"), mode="lines", hoverinfo="skip")
        
    edge_hover_trace = go.Scatter(x=edge_hover_x, y=edge_hover_y,
                                    marker=dict(color="#fb9f3a"), mode="markers", hovertext=edge_hovertext, hoverinfo="text")
    
    if port_mapping is not None:
        pm_dict = {}
        for pm in port_mapping:
            pm.pop("cp-to-degree", None)
            pm_dict[pm["node-id"]] = pm
    
    node_hover_x = []
    node_hover_y = []
    node_hovertext =[]
    node_annotations = []
    node_text = []
    for node in G.nodes():
        node_text.append(node)
        x, y = G.nodes[node]["pos"]
        node_hover_x.append(x)
        node_hover_y.append(y)
        node_annotations.append(dict(ax=x, ay=y, x=x, y=y, xref="x", yref="y", text=node,
                                    bgcolor="#0d0887", borderpad=3, font=dict(color="white")))
        
        node_info = deepcopy(G.nodes[node]["node_info"])
        tps = node_info["ietf-network-topology:termination-point"]     
        node_type = node_info["org-openroadm-common-network:node-type"]
        
        if node_type == "DEGREE":
            node_info["ietf-network-topology:termination-point"] = [tp for tp in tps if tp["org-openroadm-common-network:tp-type"] == "DEGREE-TXRX-TTP"]
            available_wavelengths = [wl["index"] for wl in node_info["org-openroadm-network-topology:degree-attributes"]["available-wavelengths"]]
            available_wavelengths.sort()  
            node_info["available-wavelengths"] = str(available_wavelengths)[1:-1]
            node_info.pop("org-openroadm-network-topology:degree-attributes")
        elif node_type == "SRG":
            node_info["ietf-network-topology:termination-point"] = [tp for tp in tps if tp["org-openroadm-common-network:tp-type"] == "SRG-TXRX-PP"]
            available_wavelengths = [wl["index"] for wl in node_info["org-openroadm-network-topology:srg-attributes"]["available-wavelengths"]]
            available_wavelengths.sort()       
            node_info["available-wavelengths"] = str(available_wavelengths)[1:-1]
            node_info.pop("org-openroadm-network-topology:srg-attributes")
        elif node_type == "XPONDER":
            node_info["ietf-network-topology:termination-point"] = [tp for tp in tps if tp["org-openroadm-common-network:tp-type"] == "XPONDER-NETWORK"]
        
        for tp in tps:
            tp.pop("org-openroadm-common-network:tp-type")
            
        node_info["ietf-network-topology:termination-point"].sort(key = lambda x: x["tp-id"])
        
        if port_mapping is not None:
            pm_info = deepcopy(pm_dict[node_info["supporting-node"][0]["node-ref"]])
            node_info.pop("supporting-node")
            mapping = pm_info.pop("mapping")
            if node_info["org-openroadm-common-network:node-type"] in ("SRG", "DEGREE"):
                mapping = [m for m in mapping if node.split("-")[-1] == m["logical-connection-point"].split("-")[0]]
            for m in mapping:
                m.pop("port-direction", None)
            node_hovertext.append("<br>".join(["Node:", yaml.dump(node_info).replace("\n", "<br>"),
                                    "Mapping:", yaml.dump(mapping).replace("\n", "<br>"),
                                    "Supporting node:", yaml.dump(pm_info).replace("\n", "<br>")]))
        else:
            node_hovertext.append("<br>".join(["Node:", yaml.dump(node_info).replace("\n", "<br>")]))
        
    node_hover_trace = go.Scatter(x=node_hover_x, y=node_hover_y,
                                    marker=dict(color="#0d0887"), text=node_text, hovertext=node_hovertext, hoverinfo="text", mode="markers")

    return go.Figure(data=[edge_trace, edge_hover_trace, node_hover_trace],
                    layout=go.Layout(showlegend=False, annotations = node_annotations, clickmode="event+select", 
                    margin=dict(l=25, r=25, t=25, b=25),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))

def trace_from_service_path(service_path_atoz, G):
    
    path_nodes = [n for n in service_path_atoz if "node-id" in n["resource"]]
    path_nodes.sort(key = lambda x: int(x["id"]))
    
    path_x = []
    path_y = []
    for node in path_nodes:
        node_id = node["resource"]["node-id"]
        x, y = G.nodes[node_id]["pos"]
        path_x.append(x)
        path_y.append(y)
        
    return go.Scatter(x=path_x, y=path_y,
                        line=dict(color="#bd3786", width=4), mode="lines", hoverinfo="skip")
                    
if __name__ == '__main__':
    from transportpce import Controller
    tpce = Controller()
    topology = tpce.get_topology()
    port_mapping = tpce.get_portmapping()
    G = graph_from_topology(topology)
    fig = figure_from_graph(G, port_mapping)
    fig.show()
