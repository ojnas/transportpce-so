import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from transportpce import Controller
import transportpce_graph as tg
from transportpce_gnpy import calculate_gsnr
import websocket
from threading import Thread
import json
import networkx as nx

tpce = Controller()

spans = tpce.measure_and_add_oms_spanloss()
#print(json.dumps(spans, indent = 4))

port_mapping = tpce.get_portmapping()
topology = tpce.get_topology()

xpdr_nodes = []
srg_nodes = []
deg_nodes = []
supp_nodes = {}
term_points = {}
conn_map_delete = set()
for n in topology["node"]:
    supp_nodes[n["node-id"]] = n["supporting-node"][0]["node-ref"]
    if n["org-openroadm-common-network:node-type"] == "XPONDER":
        xpdr_nodes.append(n["node-id"])
        term_points[n["node-id"]] = n["ietf-network-topology:termination-point"]
    elif n["org-openroadm-common-network:node-type"] == "SRG":
        srg_nodes.append(n["node-id"])
        term_points[n["node-id"]] = n["ietf-network-topology:termination-point"]
    elif n["org-openroadm-common-network:node-type"] == "DEGREE":
        deg_nodes.append(n["node-id"])
        conn_map_delete.add(n["supporting-node"][0]["node-ref"])
xpdr_nodes.sort()
srg_nodes.sort()
deg_nodes.sort()

for n in conn_map_delete:
    tpce.get_connection_map_delete_links(n)

def on_message(ws, message):
    notification = json.loads(message)
    print(json.dumps(notification, indent = 4))

def on_error(ws, error):
    print(error)

#external_stylesheets = None
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
#external_stylesheets = ['https://adi.tilde.institute/default.css/default.css']
#external_stylesheets = ['https://andybrewer.github.io/mvp/mvp.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, prevent_initial_callbacks=True)

app.layout = html.Div([
    #html.H1("OpenROADM controller"),
    
    html.Div([

        html.Div([
            dcc.Dropdown(
                id='xpdr-1',
                options=[{'label': n, 'value': n} for n in xpdr_nodes],
                placeholder="Select transponder 1 (or leave empty for SRG-to-SRG service)"
            ),
            html.Div(
                dcc.Dropdown(
                    id='xpdr-pp-1',
                    placeholder="Select transponder 1 port",
                    disabled=True
                ),
                id='xpdr-pp-1-dd'
            ),
            dcc.Dropdown(
                id='srg-1',
                options=[{'label': n, 'value': n} for n in srg_nodes],
                placeholder="Select SRG 1"
            ),
            html.Div(
                dcc.Dropdown(
                    id='srg-pp-1',
                    placeholder="Select SRG 1 port",
                    disabled=True
                ),
                id='srg-pp-1-dd'
            )
        ],
        style={'width': '50%', 'display': 'inline-block'}),

        html.Div([
            html.Div(
                dcc.Dropdown(
                    id='xpdr-2',
                    placeholder="Select transponder 2",
                    disabled=True
                ),
                id='xpdr-2-dd'
            ),
            html.Div(
                dcc.Dropdown(
                    id='xpdr-pp-2',
                    placeholder="Select transponder 2 port",
                    disabled=True
                ),
                id='xpdr-pp-2-dd'
            ),
            html.Div(
                dcc.Dropdown(
                    id='srg-2',
                    placeholder="Select SRG 2",
                    disabled=True
                ),
                id='srg-2-dd'
            ),
            html.Div(
                dcc.Dropdown(
                    id='srg-pp-2',
                    placeholder="Select SRG 2 port",
                    disabled=True
                ),
                id='srg-pp-2-dd'
            )
        ],
        style={'width': '50%', 'display': 'inline-block'}),
        
        html.Div([
            html.Div(
                dcc.Dropdown(
                    id='wl',
                    options = [{'label': f"Ch: {n}", 'value': n} for n in range(944,952)],
                    placeholder="Select wavelength channel (or leave empty for automatic assignment)"
                ),
            style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'middle'}),
            html.Div(
                dcc.Dropdown(
                    id='degrees',
                    options = [{'label': n, 'value': n} for n in deg_nodes],
                    placeholder="Select degree for OCM"
                ),
            style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'middle'}),
            html.Div(
                dcc.RadioItems(
                    id='booster-or-pre',
                    options=[
                        {'label': 'Booster', 'value': 'booster'},
                        {'label': 'Pre-amp', 'value': 'preamp'},
                    ],
                    value='booster',
                    labelStyle={'display': 'inline-block'}
                    ),
                style={'margin-left': '1%', 'display': 'inline-block', 'verticalAlign': 'middle'}),
            html.Div(
                html.Button('Show/Hide OCM', id='ocm-button'),
            style={'float': 'right', 'display': 'inline-block'}),
        ]),
    ]),
    
    html.Div([
        html.Div(
            dcc.Dropdown(
                id='service-path-name',
                placeholder="Select service path to show"
            ),
            id='service-path-name-dd',
        style={'width': '74%', 'display': 'inline-block', 'verticalAlign': 'middle'}),
    
        html.P(id='service-channel',
        style={'width': '6%', 'text-align': 'center', 'display': 'inline-block'}),
            
        
        html.Div(
            html.Button('Delete Service', id='service-delete-button'),
        style={'display': 'inline-block'}),
            
        html.Div(
            html.Button('Clear All', id='clear-input-button'),
        style={'display': 'inline-block', 'float': 'right'}),
    ],
    style={'margin-top': '5px'}),
    
    html.Div([
        html.Div([
            html.Div(
                html.Button('Request', id='request-button'),
            style={'display': 'inline-block'}),
            
            html.Div(dcc.RadioItems(
                        id='path-computation-only',
                        options=[
                            {'label': 'Service Creation', 'value': "false"},
                            {'label': 'Path Computation', 'value': "true"}
                        ],
                        value="false",
                        labelStyle={'display': 'inline-block'}),
            style={'margin-left': '1%', 'display': 'inline-block'}),
            
            html.Div(dcc.Loading(children=[html.Div(id="subscribe-waiting")], type="default"),
            style={'margin-left': '3%', 'display': 'inline-block'}),
            
            html.Div(html.P(id='status-text'), id='status-text-div',
            style={'margin-left': '3%', 'display': 'inline-block', 'text-align': 'center'})],      
        style={'width': '80%', 'display': 'inline-block'}),
        
        html.Div(
            html.Button('Update Spanloss', id='spanloss-button'),
        style={'display': 'inline-block', 'float': 'right'}),
    ],
    style={'margin-top': '5px'}),
    
    html.Div(
        dcc.Graph(
            style={'height': 1000},
            id='topology'
        ),
        id='topology-graph'),
        
    html.Div(
        dcc.Graph(
            style={'height': 1000},
            id='ocm'
        ),
        id='ocm-graph',
    style={'display': 'none'}),
    
    dcc.Store(id='path'),
    html.Div(id='requested-service-name', hidden=True),
    html.Div(id='ws-trigger', hidden=True),
    html.Div(id='graph', hidden=True)
])

@app.callback(
    [Output('xpdr-1', 'value'),
     Output('xpdr-2', 'value'),
     Output('srg-1', 'value'),
     Output('srg-2', 'value'),
     Output('degrees', 'value')],
    [Input('topology', 'clickData'),
     Input('clear-input-button', 'n_clicks')],
    [State('xpdr-1', 'value'),
     State('xpdr-2', 'value'),
     State('srg-1', 'value'),
     State('srg-2', 'value')])
def click_node(click_data, n_clicks, xpdr_1, xpdr_2, srg_1, srg_2):
    trig = dash.callback_context.triggered[0]

    if trig["prop_id"] == "clear-input-button.n_clicks":
        return None, dash.no_update, None, dash.no_update, None
        
    if trig["prop_id"] == "." or click_data is None:
        raise PreventUpdate
    
    node_id = click_data.get("points", [{}])[0].get("text")
    if node_id in xpdr_nodes:
        if xpdr_1 is None and xpdr_2 is None:
            return node_id, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        if xpdr_2 is None and xpdr_1 is not None:
            return dash.no_update, node_id, dash.no_update, dash.no_update, dash.no_update
        
    if node_id in srg_nodes:       
        if srg_1 is None and srg_2 is None:
            return dash.no_update, dash.no_update, node_id, dash.no_update, dash.no_update
        if srg_2 is None and srg_1 is not None:
            return dash.no_update, dash.no_update, dash.no_update, node_id, dash.no_update
            
    if node_id in deg_nodes:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, node_id
    
    raise PreventUpdate

@app.callback(
    [Output('topology-graph', 'style'),
     Output('ocm-graph', 'style'),
     Output('ocm', 'figure')],
    [Input('ocm-button', 'n_clicks'),
     Input('degrees', 'value'),
     Input('booster-or-pre', 'value')],
    [State('topology-graph', 'style')])
def show_ocm(n_clicks, deg, amp, cur):
    if n_clicks is None:
        raise PreventUpdate
    
    trig = dash.callback_context.triggered[0]
    if trig["prop_id"] == "ocm-button.n_clicks" and (deg is None or cur is not None):
        return (None,
                {'display': 'none'},
                dash.no_update)

    node_id = supp_nodes[deg]
    deg_nbr = deg.split("-")[-1].lstrip("DEG")
    
    osa_data = tpce.get_ocm_data(node_id, deg_nbr, amp)
    freq = [191.478125 + 0.00625 * n for n in range(len(osa_data))]
    
    osa_trace = go.Scatter(x=freq, y=osa_data,
                           line=dict(color="#0d0887"), mode='lines')
                            
    fig = go.Figure(data=[osa_trace],
                    layout=go.Layout(showlegend=False,
                                     title=f"OCM data: {deg} {amp}",
                                     xaxis_title='Frequency [THz]',
                                     yaxis_title='Power [dBm]'))
    
    return ({'width': '60%', 'display': 'inline-block'},
        {'width': '40%', 'display': 'inline-block'},
        fig)
        
@app.callback(
    [Output('topology', 'figure'),
     Output('ws-trigger', 'children'),
     Output('graph', 'children'),
     Output('service-channel', 'children')],
    [Input('service-path-name', 'value'),
     Input('status-text', 'children'),
     Input('spanloss-button', 'n_clicks')],
    [State('path', 'data'),
     State('graph', 'children')],
     prevent_initial_call=False)
def update_graph(service_path_name, status_text, n_clicks, path, G_old):
    trig = dash.callback_context.triggered[0]
    
    if trig["prop_id"] == "status-text.children" and status_text == "Service deletion in progress":
        return dash.no_update, 2, dash.no_update, dash.no_update

    if trig["prop_id"] == "spanloss-button.n_clicks":
        spans = tpce.measure_and_add_oms_spanloss()
        #print(json.dumps(spans, indent = 4))
    
    if G_old is not None:
        G_old = nx.readwrite.json_graph.jit_graph(G_old, create_using=nx.DiGraph())
        
    topology = tpce.get_topology()
    G = tg.graph_from_topology(topology, G_old)
    fig = tg.figure_from_graph(G, port_mapping)
    
    if trig["prop_id"] == "service-path-name.value":
        if service_path_name is None:
            return fig, dash.no_update, nx.readwrite.json_graph.jit_data(G), None
        
        sp = tpce.get_service_path(service_path_name)
        wl = sp['path-description']["aToZ-direction"]['aToZ-wavelength-number']
        #wl = 
        print(sp)
        path_trace = tg.trace_from_service_path(sp["path-description"]["aToZ-direction"]["aToZ"], G)
        fig.add_trace(path_trace)
        return fig, dash.no_update, nx.readwrite.json_graph.jit_data(G), 'Ch: ' + str(961 - wl)
  
    if path is not None:
        path_trace = tg.trace_from_service_path(path, G)
        fig.add_trace(path_trace)
        
    if trig["prop_id"] == "status-text.children" and status_text == "Service setup in progress":
        return fig, 1, nx.readwrite.json_graph.jit_data(G), dash.no_update
        
    return fig, None, nx.readwrite.json_graph.jit_data(G), dash.no_update

@app.callback(
     Output('wl', 'value'),
    [Input('clear-input-button', 'n_clicks')])
def clear_wl(n_clicks):
    if n_clicks is None:
        raise PreventUpdate
    
    return None

@app.callback(
    [Output('xpdr-2-dd', 'children'),
     Output('xpdr-pp-1-dd', 'children')],
    [Input('xpdr-1', 'value'),
     Input('clear-input-button', 'n_clicks')])
def set_xpdr_2_and_xpdr_pp_1(xpdr_1, n_clicks):
    trig = dash.callback_context.triggered[0]
    
    if xpdr_1 is None or trig["prop_id"] == "clear-input-button.n_clicks":
        return (dcc.Dropdown(
                    id='xpdr-2',
                    placeholder="Select transponder 2",
                    disabled=True
                ),
                dcc.Dropdown(
                    id='xpdr-pp-1',
                    placeholder="Select transponder 1 port",
                    disabled=True
                ))
    
    tps = term_points[xpdr_1]
    pps = [tp["tp-id"] for tp in tps if tp["org-openroadm-common-network:tp-type"] == "XPONDER-NETWORK"]
    pps.sort()
    
    return (dcc.Dropdown(
                id='xpdr-2',
                placeholder="Select transponder 2",
                options = [{'label': n, 'value': n} for n in xpdr_nodes if supp_nodes[n] != supp_nodes[xpdr_1]]
            ),
            dcc.Dropdown(
                id='xpdr-pp-1',
                placeholder="Select transponder 1 port",
                options = [{'label': pp, 'value': pp} for pp in pps]
            ))

@app.callback(
     Output('xpdr-pp-2-dd', 'children'),
    [Input('xpdr-1', 'value'),
     Input('xpdr-2', 'value'),
     Input('clear-input-button', 'n_clicks')])
def set_xpdr_pp_2(xpdr_1, xpdr_2, n_clicks):
    trig = dash.callback_context.triggered[0]
    
    if xpdr_1 is None or xpdr_2 is None or trig["prop_id"] == "clear-input-button.n_clicks":
        return dcc.Dropdown(
                    id='xpdr-pp-2',
                    placeholder="Select transponder 2 port",
                    disabled=True
                )
    
    tps = term_points[xpdr_2]
    pps = [tp["tp-id"] for tp in tps if tp["org-openroadm-common-network:tp-type"] == "XPONDER-NETWORK"]
    pps.sort()
    
    return dcc.Dropdown(
                id='xpdr-pp-2',
                placeholder="Select transponder 2 port",
                options = [{'label': pp, 'value': pp} for pp in pps]
            )

@app.callback(
    [Output('srg-2-dd', 'children'),
     Output('srg-pp-1-dd', 'children')],
    [Input('srg-1', 'value'),
     Input('clear-input-button', 'n_clicks')])
def set_srg_2(srg_1, n_clicks):
    trig = dash.callback_context.triggered[0]
    
    if srg_1 is None or trig["prop_id"] == "clear-input-button.n_clicks":
        return (dcc.Dropdown(
                    id='srg-2',
                    placeholder="Select SRG 2",
                    disabled=True
                ),
                dcc.Dropdown(
                    id='srg-pp-1',
                    placeholder="Select SRG 1 port",
                    disabled=True
                ))
    
    tps = term_points[srg_1]
    pps = [tp["tp-id"] for tp in tps if tp["org-openroadm-common-network:tp-type"] == "SRG-TXRX-PP"]
    pps.sort()
    
    return (dcc.Dropdown(
                id='srg-2',
                placeholder="Select SRG 2",
                options = [{'label': n, 'value': n} for n in srg_nodes if supp_nodes[n] != supp_nodes[srg_1]]
            ),
            dcc.Dropdown(
                id='srg-pp-1',
                placeholder="Select SRG 1 port",
                options = [{'label': pp, 'value': pp} for pp in pps]
            ))

@app.callback(
     Output('srg-pp-2-dd', 'children'),
    [Input('srg-1', 'value'),
     Input('srg-2', 'value'),
     Input('clear-input-button', 'n_clicks')])
def set_srg_pp_2(srg_1, srg_2, n_clicks):
    trig = dash.callback_context.triggered[0]
    if srg_1 is None or srg_2 is None or trig["prop_id"] == "clear-input-button.n_clicks":
        return dcc.Dropdown(
                    id='srg-pp-2',
                    placeholder="Select SRG 2 port",
                    disabled=True
                )
    
    tps = term_points[srg_2]
    pps = [tp["tp-id"] for tp in tps if tp["org-openroadm-common-network:tp-type"] == "SRG-TXRX-PP"]
    pps.sort()
    
    return dcc.Dropdown(
                id='srg-pp-2',
                placeholder="Select SRG 2 port",
                options = [{'label': pp, 'value': pp} for pp in pps]
            )

@app.callback(
    [Output('status-text', 'children'),
     Output('path', 'data'),
     Output('requested-service-name', 'children')],
    [Input('request-button', 'n_clicks'),
     Input('service-delete-button', 'n_clicks'),
     Input('clear-input-button', 'n_clicks')],
    [State('xpdr-1', 'value'), State('xpdr-pp-1', 'value'), State('srg-1', 'value'), State('srg-pp-1', 'value'),
     State('xpdr-2', 'value'), State('xpdr-pp-2', 'value'), State('srg-2', 'value'), State('srg-pp-2', 'value'),
     State('wl', 'value'), State('path-computation-only', 'value'),
     State('service-path-name', 'value'), State('service-path-name', 'options')])
def create_or_delete_service(n_clicks_request, n_clicks_delete, clear_trigger, xpdr_1, xpdr_pp_1,
                            srg_1, srg_pp_1, xpdr_2, xpdr_pp_2, srg_2, srg_pp_2, wl, path_computation_only, delete_service_name, sp_options):

    if n_clicks_request is None and n_clicks_delete is None:
        raise PreventUpdate

    trig = dash.callback_context.triggered[0]
    
    if trig["prop_id"] == ".":
        raise PreventUpdate
    
    if trig["prop_id"] == "clear-input-button.n_clicks":
        return "", None, None
        
    if trig["prop_id"] == "service-delete-button.n_clicks":

        if delete_service_name not in [sp["value"] for sp in sp_options]:
            return "Select service to delete", None, None
        
        delete_path = tpce.get_service_path(delete_service_name)["path-description"]["aToZ-direction"]["aToZ"]
        response = tpce.delete_service(service_name = delete_service_name)
        status = response["configuration-response-common"]["response-message"]
        if status == "Renderer service delete in progress":
            return "Service deletion in progress", delete_path, None
        
        return status, dash.no_update, dash.no_update
    
    if not all([srg_1, srg_pp_1, srg_2, srg_pp_2]):
        return "You must select two SRGs with corresponding ports", None, None
    if xpdr_1 is not None and not all([xpdr_pp_1, xpdr_2, xpdr_pp_2]):
        return "You must select two transponders with corresponding ports", None, None
    
    roadm_1 = supp_nodes[srg_1]
    roadm_2 = supp_nodes[srg_2]

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
    else:
        xpdr_node_1 = supp_nodes[xpdr_1]
        xpdr_node_2 = supp_nodes[xpdr_2]
        service_name = (f"{xpdr_node_1}_{xpdr_pp_1}_{roadm_1}_{srg_pp_1}_to_"
                        f"{xpdr_node_2}_{xpdr_pp_2}_{roadm_2}_{srg_pp_2}")
        node_1.update({"xpdr_node_id": xpdr_node_1, "xpdr_logical_connection_point": xpdr_pp_1})
        node_2.update({"xpdr_node_id": xpdr_node_2, "xpdr_logical_connection_point": xpdr_pp_2})
    
    computed_path = None
    requested_service_name = None
    
    path_computation_only = (path_computation_only == "true")
    
    if not path_computation_only:
        ws_loc = tpce.subscribe_pce_result()["location"]
        ws = websocket.create_connection(ws_loc)
    
    if wl is None:
        wl = list(range(10,18))
    else:
        wl = 961 - wl
    
    response = tpce.provision_service(node_1, node_2, wl, path_computation_only, service_name)
    status = response["configuration-response-common"]["response-message"]
    
    if status == "PCE calculation in progress":
        notification = json.loads(ws.recv())["ietf-restconf:notification"]["transportpce-pce:service-path-rpc-result"]
        status_text = notification["status-message"]
        if status_text == "Service compliant, submitting pathComputation Request ...":
            notification = json.loads(ws.recv())["ietf-restconf:notification"]["transportpce-pce:service-path-rpc-result"]
            if notification["status-message"] == "Path is calculated":
                status_text = "Service setup in progress"
                computed_path = notification["path-description"]["aToZ-direction"]["aToZ"]
                requested_service_name = service_name
            elif notification["status-message"] == "Path not calculated":
                status_text = "No path available"
            else:
                status_text = notification["status-message"]
    elif status == "Path is calculated":
        atoz_direction = response["response-parameters"]["path-description"]["aToZ-direction"]
        computed_path = atoz_direction["aToZ"]
        computed_path_ztoa = response["response-parameters"]["path-description"]["zToA-direction"]["zToA"]
        topology = tpce.get_topology()
        osnr_atoz, gsnr_atoz = calculate_gsnr(computed_path, topology, version="so")
        osnr_ztoa, gsnr_ztoa = calculate_gsnr(computed_path_ztoa, topology, version="so")
        status_text = ("Path available with wavelength Ch: " + str(961-atoz_direction['aToZ-wavelength-number']) +
                       f" | 1 -> 2: OSNR = {osnr_atoz}, GSNR = {gsnr_atoz} | 2 -> 1: OSNR = {osnr_ztoa}, GSNR = {gsnr_ztoa}")
    else:
        status_text = status
        
    if not path_computation_only:
        ws.close()
    
    return status_text, computed_path, requested_service_name
        
@app.callback(
    [Output('service-path-name', 'options'),
     Output('status-text-div', 'children'),
     Output('topology-graph', 'children'),
     Output('subscribe-waiting', 'children')],
    [Input('ws-trigger', 'children')],
    [State('requested-service-name', 'children'),
     State('service-path-name', 'value'),
     State('path', 'data'),
     State('graph', 'children')])
def subsribe_service_update(ws_trigger, requested_service_name, delete_service_name, path, G_old):
    if ws_trigger == 2:
        ws_loc = tpce.subscribe_service_status(delete_service_name)["location"] 
        ws = websocket.create_connection(ws_loc)
        while True:
            message = ws.recv()
            notification = json.loads(message)
            #print(json.dumps(notification, indent = 4))
            if notification["notification"]["data-changed-notification"]["data-change-event"]["operation"] == "deleted":
                service_result = "Service deleted"
                for p in path:
                    link_id = p["resource"].get("link-id")                    
                    if link_id is not None:
                        link = tpce.get_link(link_id)
                        if link["org-openroadm-common-network:link-type"] in ("XPONDER-INPUT", "XPONDER-OUTPUT"):
                            opposite_link_id = link["org-openroadm-common-network:opposite-link"]
                            tpce.delete_link(link_id)
                            tpce.delete_link(opposite_link_id)
                break     
        ws.close()
    elif ws_trigger == 1:
        ws_loc = tpce.subscribe_service_status(requested_service_name)["location"] 
        ws = websocket.create_connection(ws_loc)
        while True:
            message = ws.recv()
            notification = json.loads(message)
            #print(json.dumps(notification, indent = 4))
            if notification["notification"]["data-changed-notification"]["data-change-event"]["operation"] == "deleted":
                service_result = "Service setup failed"
                break
            if notification["notification"]["data-changed-notification"]["data-change-event"]["data"]["operational-state"]["content"] == "inService":
                service_result = "Service created"
                break
        ws.close()
    
    service_path_list = tpce.get_service_path_list()
    if service_path_list is None:
        options = []
    else:
        options = [{'label': sp["service-path-name"], 'value': sp["service-path-name"]} for sp in service_path_list["service-paths"]]
    
    if ws_trigger is None:
        return options, dash.no_update, dash.no_update, dash.no_update
        
    if G_old is not None:
        G_old = nx.readwrite.json_graph.jit_graph(G_old, create_using=nx.DiGraph())
    
    topology = tpce.get_topology()
    G = tg.graph_from_topology(topology, G_old)
    fig = tg.figure_from_graph(G, port_mapping)
    
    if ws_trigger == 1:
        path_trace = tg.trace_from_service_path(path, G)
        fig.add_trace(path_trace)
        
    graph = dcc.Graph(
                figure = fig,
                style={'height': 1000},
                id='topology'
            )
    
    return options, html.P(id='status-text', children=service_result), graph, None

if __name__ == '__main__':
    ws_loc = tpce.subscribe_all()["location"]
    ws = websocket.WebSocketApp(ws_loc, on_message = on_message, on_error = on_error)
    ws_thread = Thread(target = ws.run_forever, daemon = True)
    ws_thread.start()
    app.run_server(debug=True)
