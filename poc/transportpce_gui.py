import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State
from transportpce import Controller
import transportpce_graph as tg
from websocket import create_connection
from json import loads

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

service_path_list = tpce.get_service_path_list()
if service_path_list is None:
    sp_options = []
else:
    sp_options = [{'label': sp["service-path-name"], 'value': sp["service-path-name"]} for sp in service_path_list["service-paths"]]


G = tg.graph_from_topology(topology)

external_stylesheets = None
#external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
#external_stylesheets = ['https://adi.tilde.institute/default.css/default.css']
#external_stylesheets = ['https://andybrewer.github.io/mvp/mvp.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    #html.H1("OpenROADM controller"),
    
    html.Div([

        html.Div([
            dcc.Dropdown(
                id='xpdr-1',
                options=[{'label': n, 'value': n} for n in xpdr_nodes],
                placeholder="Select transponder 1 (or leave empty for SRG-to-SRG service)"
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
        style={'width': '50%', 'display': 'inline-block'}),

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
        style={'width': '50%', 'display': 'inline-block'}),
        
        html.Div(
            dcc.Dropdown(
                id='wl',
                options = [{'label': f"Ch: {n}", 'value': n} for n in range(1,41)],
                placeholder="Select wavelength channel (or leave empty for automatic assignment)"
            ),
        style={'width': '50%'}),
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
                        value=False,
                        labelStyle={'display': 'inline-block'}),
            style={'display': 'inline-block'})],
        style={'display': 'inline-block'}),
        
        html.Div(
            html.Button('Update topology', id='update-button'),
        style={'display': 'inline-block', 'float': 'right'}),
    ],
    style={'width': '50%', 'display': 'inline-block'}),
            
    html.Div(id='status-text',
    style={'width': '40%', 'display': 'inline-block', 'text-align': 'center'}),
    
    html.Div(dcc.Loading(children=[html.Div(id="subscribe-waiting")], type="default"),
    style={'display': 'inline-block'}),

    dcc.Dropdown(
        id='service-path-name',
        options=sp_options,
        placeholder="Show service path"
    ),

    dcc.Graph(
        style={'height': 1000},
        id='topology'
    ),
    
    html.Div(id='computed-path', hidden=True),
    html.Div(id='requested-service-name', hidden=True),
    html.Div(id='ws-trigger', hidden=True),
    html.Div(id='service-created-trigger', hidden=True),
    html.Div(id='clear-status-trigger', hidden=True)
])

@app.callback(
    [Output('topology', 'figure'),
    Output('ws-trigger', 'children')],
    [Input('update-button', 'n_clicks'),
    Input('service-path-name', 'value'),
    Input('status-text', 'children')],
    [State('computed-path', 'children')])
def update_graph(n_clicks, service_path_name, status_text, computed_path):
    trig = dash.callback_context.triggered[0]
    if trig["prop_id"] == "status-text.children" and status_text in ("Service Created", ""):
        raise PreventUpdate
    
    topology = tpce.get_topology()
    G = tg.graph_from_topology(topology)
    fig = tg.figure_from_graph(G, port_mapping)
    
    if trig["prop_id"] == "status-text.children" and computed_path is not None:
        path_trace = tg.trace_from_service_path(computed_path, G)
        fig.add_trace(path_trace)
        
        if status_text != "Service setup in progress":
            return fig, dash.no_update
        
        return fig, 1
    
    if trig["prop_id"] == "service-path-name.value" and service_path_name is not None:
        sp = tpce.get_service_path(service_path_name)
        path_trace = tg.trace_from_service_path(sp["path-description"]["aToZ-direction"]["aToZ"], G)
        fig.add_trace(path_trace)
    
    return fig, dash.no_update

@app.callback(
    [Output('xpdr-1', 'value'), Output('xpdr-pp-1', 'value'),
    Output('xpdr-2', 'value'), Output('xpdr-pp-2', 'value'),
    Output('srg-1', 'value'), Output('srg-pp-1', 'value'),
    Output('srg-2', 'value'), Output('srg-pp-2', 'value'),
    Output('wl', 'value'), Output('clear-status-trigger', 'children')],
    [Input('update-button', 'n_clicks')])
def clear_values(n_clicks):
    if n_clicks is None:
        raise PreventUpdate
    
    outputs = [None] * 9
    
    return (*outputs, 1)

@app.callback(
    [Output('xpdr-2', 'options'),
     Output('xpdr-pp-1', 'options')],
    [Input('xpdr-1', 'value')])
def set_xpdr_1_options(xpdr_1):
    if xpdr_1 is None:
        return [], []
    tps = G.nodes[xpdr_1]["node_info"]["ietf-network-topology:termination-point"]
    pps = [tp["tp-id"] for tp in tps if tp["org-openroadm-common-network:tp-type"] == "XPONDER-NETWORK"]
    pps.sort()
    
    return ([{'label': n, 'value': n} for n in xpdr_nodes if n != xpdr_1],
            [{'label': pp, 'value': pp} for pp in pps])

@app.callback(
    [Output('srg-2', 'options'),
     Output('srg-pp-1', 'options')],
    [Input('srg-1', 'value')])
def set_srg_1_options(srg_1):
    if srg_1 is None:
        return [], []
    tps = G.nodes[srg_1]["node_info"]["ietf-network-topology:termination-point"]
    pps = [tp["tp-id"] for tp in tps if tp["org-openroadm-common-network:tp-type"] == "SRG-TXRX-PP"]
    pps.sort()
    return ([{'label': n, 'value': n} for n in srg_nodes if
            G.nodes[n]["node_info"]["supporting-node"][0]["node-ref"] !=
            G.nodes[srg_1]["node_info"]["supporting-node"][0]["node-ref"]],
            [{'label': pp, 'value': pp} for pp in pps])
    
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
    [Output('status-text', 'children'),
     Output('computed-path', 'children'),
     Output('requested-service-name', 'children')],
    [Input('request-button', 'n_clicks'),
     Input('service-created-trigger', 'children'),
     Input('clear-status-trigger', 'children')],
    [State('xpdr-1', 'value'), State('xpdr-pp-1', 'value'), State('srg-1', 'value'), State('srg-pp-1', 'value'),
     State('xpdr-2', 'value'), State('xpdr-pp-2', 'value'), State('srg-2', 'value'), State('srg-pp-2', 'value'),
     State('wl', 'value'), State('path-computation-only', 'value')])
def create_service(n_clicks, sc_trigger, clear_trigger, xpdr_1, xpdr_pp_1,
                    srg_1, srg_pp_1, xpdr_2, xpdr_pp_2, srg_2, srg_pp_2, wl, path_computation_only):
    if n_clicks is None:
        raise PreventUpdate

    trig = dash.callback_context.triggered[0]
    if trig["prop_id"] == "service-created-trigger.children":
        return "Service Created", None, None
    elif trig["prop_id"] == "clear-status-trigger.children":
        return "", None, None
    
    if not all([srg_1, srg_pp_1, srg_2, srg_pp_2]):
        return "You must select two SRGs with corresponding ports", None, None
    if xpdr_1 is not None and not all([xpdr_pp_1, xpdr_2, xpdr_pp_2]):
        return "You must select two transponders with corresponding ports", None, None
    
    roadm_1 = G.nodes[srg_1]["node_info"]["supporting-node"][0]["node-ref"]
    roadm_2 = G.nodes[srg_2]["node_info"]["supporting-node"][0]["node-ref"]

    node_1 = {
    "roadm_node_id": roadm_1,
    "srg_logical_connection_point": srg_pp_1
    }
    node_2 = {
        "roadm_node_id": roadm_2,
        "srg_logical_connection_point": srg_pp_2
    }
        
    if xpdr_1 is None:
        service_name = f"{roadm_1}_{srg_pp_1}_to_{roadm_2}_{srg_pp_2}"
        response = tpce.provision_roadm_service(node_1, node_2, wl, True, service_name)
    else:
        xpdr_node_1 = G.nodes[xpdr_1]["node_info"]["supporting-node"][0]["node-ref"]
        xpdr_node_2 = G.nodes[xpdr_2]["node_info"]["supporting-node"][0]["node-ref"]
        service_name = (f"{xpdr_node_1}_{xpdr_pp_1}_{roadm_1}_{srg_pp_1}_to_"
                        f"{xpdr_node_2}_{xpdr_pp_2}_{roadm_2}_{srg_pp_2}")
        node_1.update({"xpdr_node_id": xpdr_node_1, "xpdr_logical_connection_point": xpdr_pp_1})
        node_2.update({"xpdr_node_id": xpdr_node_2, "xpdr_logical_connection_point": xpdr_pp_2})
        response = tpce.provision_xpdr_service(node_1, node_2, wl, True, service_name)
    
    if response["configuration-response-common"]["response-message"] != "Path is calculated":
        return "No Path Available", None, None
    
    computed_path = response["response-parameters"]["path-description"]["aToZ-direction"]["aToZ"]
    
    if path_computation_only:
        status = ("Path Available, Use Wavelength Ch: " +
                    str(response["response-parameters"]["path-description"]["aToZ-direction"]["aToZ-wavelength-number"]))
        return status, computed_path, None
    
    if xpdr_1 is None:
        response = tpce.provision_roadm_service(node_1, node_2, wl, False, service_name)
    else:
        response = tpce.provision_xpdr_service(node_1, node_2, wl, False, service_name)
    
    status = response["configuration-response-common"]["response-message"]       
    if status == "PCE calculation in progress":
        requested_service_name = service_name
        status = "Service setup in progress"
    else:
        requested_service_name = None
    
    return status, computed_path, requested_service_name
    
@app.callback(
    [Output('service-path-name', 'options'),
     Output('service-created-trigger', 'children'),
     Output('subscribe-waiting', 'children')],
    [Input('ws-trigger', 'children')],
    [State('requested-service-name', 'children')])
def subsribe_service_update(ws_trigger, service_name):
    if service_name is None:
        raise PreventUpdate
        
    ws_loc = tpce.subscribe_service_status(service_name)["location"] 
    ws = create_connection(ws_loc)
    
    while True:
        message = ws.recv()
        notification = loads(message)
        print(notification)
        if notification["notification"]["data-changed-notification"]["data-change-event"]["data"]["operational-state"]["content"] == "inService":
            break

    ws.close()
    
    service_path_list = tpce.get_service_path_list()
    if service_path_list is None:
        return [], dash.no_update, None
    
    return [{'label': sp["service-path-name"], 'value': sp["service-path-name"]} for sp in service_path_list["service-paths"]], 1, None

if __name__ == '__main__':
    app.run_server()
