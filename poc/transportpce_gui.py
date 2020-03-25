import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State
from transportpce import Controller
import transportpce_graph as tg

tpce = Controller()
topology = tpce.get_topology()
xpdr_nodes = []
srg_nodes = []
for n in topology["node"]:
    if n["org-openroadm-common-network:node-type"] == "XPONDER":
        xpdr_nodes.append(n["node-id"])
    elif n["org-openroadm-common-network:node-type"] == "SRG":
        srg_nodes.append(n["node-id"])
xpdr_nodes.sort()
srg_nodes.sort()
port_mapping = tpce.get_portmapping()
G = tg.graph_from_topology(topology)

app = dash.Dash(__name__)

app.layout = html.Div([
    #html.H1("OpenROADM controller"),
    
    html.Div([

        html.Div([
            dcc.Dropdown(
                id='xpdr-1',
                options=[{'label': n, 'value': n} for n in xpdr_nodes],
                placeholder="Select transponder 1"
            ),
            dcc.Dropdown(
                id='xpdr-pp-1',
                placeholder="Select transponder 1 port"
            ),
            dcc.Dropdown(
                id='srg-1',
                options=[{'label': n, 'value': n} for n in srg_nodes],
                placeholder="Select SRG 1"
            ),
            dcc.Dropdown(
                id='srg-pp-1',
                placeholder="Select SRG 1 port"
            )
        ],
        style={'width': '30%', 'display': 'inline-block'}),

        html.Div([
            dcc.Dropdown(
                id='xpdr-2',
                placeholder="Select transponder 2"
            ),
            dcc.Dropdown(
                id='xpdr-pp-2',
                placeholder="Select transponder 2 port"
            ),
            dcc.Dropdown(
                id='srg-2',
                placeholder="Select SRG 2"
            ),
            dcc.Dropdown(
                id='srg-pp-2',
                placeholder="Select SRG 2 port"
            )
        ],
        style={'width': '30%', 'display': 'inline-block'}),
        
        html.Div(
            dcc.Dropdown(
                id='wl',
                options = [{'label': "auto", 'value': 0}] + [{'label': f"Ch: {n}", 'value': n} for n in range(1,41)],
                placeholder="Select wavelength channel"
            ),
        style={'width': '30%'}),
    ]),
    
    html.Div([
        html.Div([
            html.Div(
                html.Button('Request', id='request-button'),
            style={'display': 'inline-block'}),
            
            html.Div(dcc.RadioItems(
                        id='path-computation-only',
                        options=[
                            {'label': 'Service Creation', 'value': False},
                            {'label': 'Path Computation', 'value': True}
                        ],
                        value=False),
            style={'display': 'inline-block'})],
        style={'width': '30%', 'display': 'inline-block'}),

        html.Div(id='create-response',
        style={'display': 'inline-block'}),    
            
        html.Div(id='clear-response',
        style={'display': 'inline-block'})
    ]),

    html.Div(
        dcc.Dropdown(
            id='service-path-name',
            placeholder="Show service path"
        ),
    style={'width': '80%', 'display': 'inline-block'}),
    
    html.Div([
        html.Button('Update topology and services', id='update-button')
    ]),
    
    html.Div([
        dcc.Graph(
            style={'height': 1000},
            id='topology'
        )
    ])
])

@app.callback(
    [Output('topology', 'figure'),
    Output('service-path-name', 'options'),
    Output('xpdr-1', 'value'), Output('xpdr-pp-1', 'value'),
    Output('xpdr-2', 'value'), Output('xpdr-pp-2', 'value'),
    Output('srg-1', 'value'), Output('srg-pp-1', 'value'),
    Output('srg-2', 'value'), Output('srg-pp-2', 'value'),
    Output('wl', 'value'), Output('create-response', 'children')],
    [Input('update-button', 'n_clicks'),
    Input('service-path-name', 'value')])
def update_graph_services(n_clicks, service_path_name):
    topology = tpce.get_topology()
    G = tg.graph_from_topology(topology)
    fig = tg.figure_from_graph(G, port_mapping)
    service_path_list = tpce.get_service_path_list()
    values = tuple([None] * 9)
    if service_path_list is None:
        return (fig, [], *values,  html.Div(""))
    options = [{'label': sp["service-path-name"], 'value': sp["service-path-name"]} for sp in service_path_list["service-paths"]]
    if service_path_name is not None:
        sp = tpce.get_service_path(service_path_name)
        path_trace = tg.trace_from_service_path(sp, G)
        fig.add_trace(path_trace)
    
    return (fig, options, *values, html.Div(""))

@app.callback(
    Output('xpdr-2', 'options'),
    [Input('xpdr-1', 'value')])
def set_xpdr_2_options(xpdr_1):
    if xpdr_1 is None:
        return []
    return [{'label': n, 'value': n} for n in xpdr_nodes if n != xpdr_1]

@app.callback(
    Output('srg-2', 'options'),
    [Input('srg-1', 'value')])
def set_srg_2_options(srg_1):
    if srg_1 is None:
        return []
    return [{'label': n, 'value': n} for n in srg_nodes if
            G.nodes[n]["node_info"]["supporting-node"][0]["node-ref"] !=
            G.nodes[srg_1]["node_info"]["supporting-node"][0]["node-ref"]]  
    
@app.callback(
    Output('xpdr-pp-1', 'options'),
    [Input('xpdr-1', 'value')])
def set_xpdr_pp_1_options(xpdr_1):
    if xpdr_1 is None:
        return []
    tps = G.nodes[xpdr_1]["node_info"]["ietf-network-topology:termination-point"]
    pps = [tp["tp-id"] for tp in tps if tp["org-openroadm-common-network:tp-type"] == "XPONDER-NETWORK"]
    pps.sort()
    return [{'label': pp, 'value': pp} for pp in pps]   
    
@app.callback(
    Output('xpdr-pp-2', 'options'),
    [Input('xpdr-2', 'value')])
def set_xpdr_pp_2_options(xpdr_2):
    if xpdr_2 is None:
        return []
    tps = G.nodes[xpdr_2]["node_info"]["ietf-network-topology:termination-point"]
    pps = [tp["tp-id"] for tp in tps if tp["org-openroadm-common-network:tp-type"] == "XPONDER-NETWORK"]
    pps.sort()
    return [{'label': pp, 'value': pp} for pp in pps]
    
@app.callback(
    Output('srg-pp-1', 'options'),
    [Input('srg-1', 'value')])
def set_srg_pp_1_options(srg_1):
    if srg_1 is None:
        return []
    tps = G.nodes[srg_1]["node_info"]["ietf-network-topology:termination-point"]
    pps = [tp["tp-id"] for tp in tps if tp["org-openroadm-common-network:tp-type"] == "SRG-TXRX-PP"]
    pps.sort()
    return [{'label': pp, 'value': pp} for pp in pps]
    
@app.callback(
    Output('srg-pp-2', 'options'),
    [Input('srg-2', 'value')])
def set_srg_pp_2_options(srg_2):
    if srg_2 is None:
        return []
    tps = G.nodes[srg_2]["node_info"]["ietf-network-topology:termination-point"]
    pps = [tp["tp-id"] for tp in tps if tp["org-openroadm-common-network:tp-type"] == "SRG-TXRX-PP"]
    pps.sort()
    return [{'label': pp, 'value': pp} for pp in pps]

@app.callback(
    Output('clear-response', 'children'),
    [Input('request-button', 'n_clicks')],
    [State('xpdr-1', 'value'), State('xpdr-pp-1', 'value'), State('srg-1', 'value'), State('srg-pp-1', 'value'),
     State('xpdr-2', 'value'), State('xpdr-pp-2', 'value'), State('srg-2', 'value'), State('srg-pp-2', 'value'),
     State('wl', 'value'), State('path-computation-only', 'value')])
def create_service(n_clicks, xpdr_1, xpdr_pp_1, srg_1, srg_pp_1, xpdr_2, xpdr_pp_2, srg_2, srg_pp_2, wl, path_computation_only):
    if n_clicks is None:
        raise PreventUpdate
    else:
        if not all([srg_1, srg_pp_1, srg_2, srg_pp_2]):
            return html.Div("You must select two SRGs with corresponding ports", id="create-response")
        if xpdr_1 is not None and not all([xpdr_pp_1, xpdr_2, xpdr_pp_2]):
            return html.Div("You must select two transponders with corresponding ports", id="create-response")
        roadm_1 = G.nodes[srg_1]["node_info"]["supporting-node"][0]["node-ref"]
        roadm_2 = G.nodes[srg_2]["node_info"]["supporting-node"][0]["node-ref"]
        if not wl: wl = None
        node_1 = {
        "roadm_node_id": roadm_1,
        "srg_logical_connection_point": srg_pp_1
        }
        node_2 = {
            "roadm_node_id": roadm_2,
            "srg_logical_connection_point": srg_pp_2
        }

        if xpdr_1 is None or path_computation_only:
            response = tpce.provision_roadm_service(node_1, node_2, wl, path_computation_only)
        else:
            xpdr_node_1 = G.nodes[xpdr_1]["node_info"]["supporting-node"][0]["node-ref"]
            xpdr_node_2 = G.nodes[xpdr_2]["node_info"]["supporting-node"][0]["node-ref"]
            node_1.update({"xpdr_node_id": xpdr_node_1, "xpdr_logical_connection_point": xpdr_pp_1})
            node_2.update({"xpdr_node_id": xpdr_node_2, "xpdr_logical_connection_point": xpdr_pp_2})
            response = tpce.provision_xpdr_service(node_1, node_2, wl)
        
        message = response["configuration-response-common"]["response-message"]
        if message == "Path is calculated":
            message = ("Path available, Use wavelength ch: " +
                        str(response["response-parameters"]["path-description"]["aToZ-direction"]["aToZ-wavelength-number"]))
        elif message == "PCE calculation in progress":
            message = "Service creation requested ..."
        
        return html.Div(message, id="create-response")
            
if __name__ == '__main__':
    app.run_server()
