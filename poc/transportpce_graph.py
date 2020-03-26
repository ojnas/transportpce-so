#!/usr/bin/env python

import json
from copy import deepcopy
import networkx as nx
import plotly.graph_objects as go

def graph_from_topology(topology):
    
    G = nx.DiGraph()
   
    for node in topology["node"]:
        if node["org-openroadm-common-network:node-type"] == "SRG":
            available_wavelengths = [wl["index"] for wl in node["org-openroadm-network-topology:srg-attributes"]["available-wavelengths"]]
            available_wavelengths.sort()       
            node["available-wavelengths"] = str(available_wavelengths)[1:-1]
            node.pop("org-openroadm-network-topology:srg-attributes", None)
        elif node["org-openroadm-common-network:node-type"] == "DEGREE":
            available_wavelengths = [wl["index"] for wl in node["org-openroadm-network-topology:degree-attributes"]["available-wavelengths"]]
            available_wavelengths.sort()  
            node["available-wavelengths"] = str(available_wavelengths)[1:-1]
            node.pop("org-openroadm-network-topology:degree-attributes", None)   
        G.add_node(node["node-id"], node_info = node)

    for link in topology["ietf-network-topology:link"]:
        if link["org-openroadm-common-network:link-type"] == "ROADM-TO-ROADM":          
            length = link.get("org-openroadm-network-topology:OMS-attributes", {}).get("span", {}).get("link-concatenation", [{}])[0].get("SRLG-length")
            weight = length / 1000 if length is not None else 10
        elif link["org-openroadm-common-network:link-type"] == "EXPRESS-LINK":
            weight = 1.5
        else:
            weight = 1
        G.add_edge(link["source"]["source-node"], link["destination"]["dest-node"], link_info = link, weight = weight)

    pos = nx.kamada_kawai_layout(G)
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
        edge_hovertext.append("<br>".join([f"Direction {edge[0]} -> {edge[1]}:", json.dumps(G.edges[edge]["link_info"], indent=4).replace("\n", "<br>"),
                                f"Direction {edge[1]} -> {edge[0]}:", json.dumps(G.edges[opposite_edge]["link_info"], indent=4).replace("\n", "<br>")]))
        seen_edges.append(edge)

    edge_trace = go.Scatter(x=edge_x, y=edge_y,
                            line=dict(color="#fb9f3a"), mode="lines", hoverinfo="skip")
        
    edge_hover_trace = go.Scatter(x=edge_hover_x, y=edge_hover_y,
                                    marker=dict(color="#fb9f3a"), mode="markers", hovertext=edge_hovertext, hoverinfo="text")

    node_hover_x = []
    node_hover_y = []
    node_hovertext =[]
    node_annotations = []
    for node in G.nodes():
        x, y = G.nodes[node]["pos"]
        node_hover_x.append(x)
        node_hover_y.append(y)
        node_annotations.append(dict(ax=x, ay=y, x=x, y=y, xref="x", yref="y", text=node,
                                    bgcolor="#0d0887", borderpad=3, font=dict(color="white")))
        node_info = deepcopy(G.nodes[node]["node_info"])
        tps = node_info["ietf-network-topology:termination-point"]
        if node_info["org-openroadm-common-network:node-type"] == "DEGREE":
            node_info["ietf-network-topology:termination-point"] = [tp for tp in tps if tp["org-openroadm-common-network:tp-type"] == "DEGREE-TXRX-TTP"]
        elif node_info["org-openroadm-common-network:node-type"] == "SRG":
            node_info["ietf-network-topology:termination-point"] = [tp for tp in tps if tp["org-openroadm-common-network:tp-type"] == "SRG-TXRX-PP"]
        elif node_info["org-openroadm-common-network:node-type"] == "XPONDER":
            node_info["ietf-network-topology:termination-point"] = [tp for tp in tps if tp["org-openroadm-common-network:tp-type"] == "XPONDER-NETWORK"]
        for tp in node_info["ietf-network-topology:termination-point"]:
            tp.pop("org-openroadm-common-network:tp-type", None)
        if port_mapping is not None:
            pm_info = next(deepcopy(pm) for pm in port_mapping if pm["node-id"] == node_info["supporting-node"][0]["node-ref"])
            pm_info.pop("cp-to-degree", None)
            node_info.pop("supporting-node", None)
            mapping = pm_info.pop("mapping")
            if node_info["org-openroadm-common-network:node-type"] in ("SRG", "DEGREE"):
                mapping = [m for m in mapping if node.split("-")[-1] == m["logical-connection-point"].split("-")[0]]
            for m in mapping:
                m.pop("port-direction", None)
            node_hovertext.append("<br>".join(["Node:", json.dumps(node_info, indent=4).replace("\n", "<br>"),
                                    "Mapping:", json.dumps(mapping, indent=4).replace("\n", "<br>"),
                                    "Supporting node:", json.dumps(pm_info, indent=4).replace("\n", "<br>")]))
        else:
            node_hovertext.append("<br>".join(["Node:", json.dumps(node_info, indent=4).replace("\n", "<br>")]))
        
    node_hover_trace = go.Scatter(x=node_hover_x, y=node_hover_y,
                                    marker=dict(color="#0d0887"), hovertext=node_hovertext, hoverinfo="text", mode="markers")

    return go.Figure(data=[edge_trace, edge_hover_trace, node_hover_trace],
                    layout=go.Layout(showlegend=False, annotations = node_annotations, margin=dict(l=25, r=25, t=25, b=25),
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
    
