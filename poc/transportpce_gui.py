import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State
from transportpce import Controller
import transportpce_graph as tg
from transportpce_gnpy import calculate_gsnr
import websocket
from threading import Thread
import json

tpce = Controller()
topology = tpce.get_topology()

xpdr_nodes = []
srg_nodes = []
supp_nodes = {}
term_points = {}
for n in topology["node"]:
    if n["org-openroadm-common-network:node-type"] == "XPONDER":
        xpdr_nodes.append(n["node-id"])
        supp_nodes[n["node-id"]] = n["supporting-node"][0]["node-ref"]
        term_points[n["node-id"]] = n["ietf-network-topology:termination-point"]
    elif n["org-openroadm-common-network:node-type"] == "SRG":
        srg_nodes.append(n["node-id"])
        supp_nodes[n["node-id"]] = n["supporting-node"][0]["node-ref"]
        term_points[n["node-id"]] = n["ietf-network-topology:termination-point"]
xpdr_nodes.sort()
srg_nodes.sort()

port_mapping = tpce.get_portmapping()

def on_message(ws, message):
    notification = json.loads(message)
    print(json.dumps(notification, indent = 4))

def on_error(ws, error):
    print(error)

#external_stylesheets = None
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
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
        style={'display': 'inline-block', 'width': '60%'}),
        
        html.Div(
            html.Button('Delete Service', id='service-delete-button'),
        style={'display': 'inline-block'}),
        
        html.Div(
            html.Button('Clear All', id='clear-input-button'),
        style={'display': 'inline-block', 'float': 'right'}),
    ],
    style={'width': '50%', 'display': 'inline-block'}),
            
    html.Div(html.P(id='status-text'),
    style={'width': '40%', 'display': 'inline-block', 'text-align': 'center'}),
    
    html.Div(dcc.Loading(children=[html.Div(id="subscribe-waiting")], type="default"),
    style={'display': 'inline-block'}),

    html.Div(
        dcc.Dropdown(
            id='service-path-name',
            placeholder="Select service path to show"),
    style={'width': '100%', 'display': 'inline-block'}),
    
    dcc.Graph(
        style={'height': 1000},
        id='topology'
    ),
    
    html.Div(id='computed-path', hidden=True),
    html.Div(id='requested-service-name', hidden=True),
    html.Div(id='ws-trigger', hidden=True),
    html.Div(id='service-result', hidden=True),
    html.Div(id='clear-status-trigger', hidden=True),
])

@app.callback(
    [Output('topology', 'figure'),
     Output('ws-trigger', 'children')],
    [Input('service-path-name', 'value'),
     Input('status-text', 'children')],
    [State('computed-path', 'children')])
def update_graph(service_path_name, status_text, computed_path):
    trig = dash.callback_context.triggered[0]
    
    if trig["prop_id"] == "status-text.children" and status_text == "Service deletion in progress":
        return dash.no_update, 2

    topology = tpce.get_topology()
    G = tg.graph_from_topology(topology)
    fig = tg.figure_from_graph(G, port_mapping)
    
    if trig["prop_id"] == "service-path-name.value":
        if service_path_name is None:
            return fig, dash.no_update
        
        sp = tpce.get_service_path(service_path_name)
        path_trace = tg.trace_from_service_path(sp["path-description"]["aToZ-direction"]["aToZ"], G)
        fig.add_trace(path_trace)
        return fig, dash.no_update
       
    if computed_path is not None:
        path_trace = tg.trace_from_service_path(computed_path, G)
        fig.add_trace(path_trace)
        
    if status_text == "Service setup in progress":
        return fig, 1
        
    return fig, dash.no_update

@app.callback(
    [Output('xpdr-1', 'value'), Output('xpdr-pp-1', 'value'),
    Output('xpdr-2', 'value'), Output('xpdr-pp-2', 'value'),
    Output('srg-1', 'value'), Output('srg-pp-1', 'value'),
    Output('srg-2', 'value'), Output('srg-pp-2', 'value'),
    Output('wl', 'value'), Output('clear-status-trigger', 'children')],
    [Input('clear-input-button', 'n_clicks')])
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
    tps = term_points[xpdr_1]
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
    tps = term_points[srg_1]
    pps = [tp["tp-id"] for tp in tps if tp["org-openroadm-common-network:tp-type"] == "SRG-TXRX-PP"]
    pps.sort()
    return ([{'label': n, 'value': n} for n in srg_nodes if supp_nodes[n] != supp_nodes[srg_1]],
            [{'label': pp, 'value': pp} for pp in pps])
    
@app.callback(
    Output('xpdr-pp-2', 'options'),
    [Input('xpdr-2', 'value')])
def set_xpdr_pp_2_options(xpdr_2):
    if xpdr_2 is None:
        return []
    tps = term_points[xpdr_2]
    pps = [tp["tp-id"] for tp in tps if tp["org-openroadm-common-network:tp-type"] == "XPONDER-NETWORK"]
    pps.sort()
    return [{'label': pp, 'value': pp} for pp in pps]
    
@app.callback(
    Output('srg-pp-2', 'options'),
    [Input('srg-2', 'value')])
def set_srg_pp_2_options(srg_2):
    if srg_2 is None:
        return []
    tps = term_points[srg_2]
    pps = [tp["tp-id"] for tp in tps if tp["org-openroadm-common-network:tp-type"] == "SRG-TXRX-PP"]
    pps.sort()
    return [{'label': pp, 'value': pp} for pp in pps]

@app.callback(
    [Output('status-text', 'children'),
     Output('computed-path', 'children'),
     Output('requested-service-name', 'children')],
    [Input('request-button', 'n_clicks'),
     Input('service-delete-button', 'n_clicks'),
     Input('service-result', 'children'),
     Input('clear-status-trigger', 'children')],
    [State('xpdr-1', 'value'), State('xpdr-pp-1', 'value'), State('srg-1', 'value'), State('srg-pp-1', 'value'),
     State('xpdr-2', 'value'), State('xpdr-pp-2', 'value'), State('srg-2', 'value'), State('srg-pp-2', 'value'),
     State('wl', 'value'), State('path-computation-only', 'value'), State('service-path-name', 'value')])
def create_or_delete_service(n_clicks_request, n_clicks_delete, service_result, clear_trigger, xpdr_1, xpdr_pp_1,
                    srg_1, srg_pp_1, xpdr_2, xpdr_pp_2, srg_2, srg_pp_2, wl, path_computation_only, delete_service_name):
    if n_clicks_request is None and n_clicks_delete is None:
        raise PreventUpdate

    trig = dash.callback_context.triggered[0]
    
    if trig["prop_id"] == "service-result.children":
        return service_result, dash.no_update, None
    
    if trig["prop_id"] == "clear-status-trigger.children":
        return "", None, None
        
    if trig["prop_id"] == "service-delete-button.n_clicks":
        if delete_service_name is None:
            return "Select service to delete", dash.no_update, dash.no_update
        
        response = tpce.delete_service(service_name = delete_service_name)
        status = response["configuration-response-common"]["response-message"]
        if status == "Renderer service delete in progress":
            return "Service deletion in progress", dash.no_update, dash.no_update
        
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
    
    if not path_computation_only:
        ws_loc = tpce.subscribe_pce_result()["location"]
        ws = websocket.create_connection(ws_loc)
    
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
        osnr_atoz, gsnr_atoz = calculate_gsnr(computed_path, topology)
        osnr_ztoa, gsnr_ztoa = calculate_gsnr(computed_path_ztoa, topology)
        status_text = ["Path available with wavelength Ch: " + str(atoz_direction['aToZ-wavelength-number']), html.Br(),
                       f"1 -> 2: ONSR = {osnr_atoz}, GSNR = {gsnr_atoz} | 2 -> 1: ONSR = {osnr_ztoa}, GSNR = {gsnr_ztoa}"]
    else:
        status_text = status
        
    if not path_computation_only:
        ws.close()
    
    return status_text, computed_path, requested_service_name    
        
@app.callback(
    [Output('service-path-name', 'options'),
     Output('service-result', 'children'),
     Output('subscribe-waiting', 'children')],
    [Input('ws-trigger', 'children')],
    [State('requested-service-name', 'children'),
     State('service-path-name', 'value')])
def subsribe_service_update(ws_trigger, requested_service_name, delete_service_name):
    
    if ws_trigger == 2:
        ws_loc = tpce.subscribe_service_status(delete_service_name)["location"] 
        ws = websocket.create_connection(ws_loc)
        while True:
            message = ws.recv()
            notification = json.loads(message)
            #print(json.dumps(notification, indent = 4))
            if notification["notification"]["data-changed-notification"]["data-change-event"]["operation"] == "deleted":
                service_result = "Service deleted"
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
    else:
        service_result = dash.no_update
    
    service_path_list = tpce.get_service_path_list()
    if service_path_list is None:
        options = []
    else:
        options = [{'label': sp["service-path-name"], 'value': sp["service-path-name"]} for sp in service_path_list["service-paths"]]
        
    return options, service_result, None

if __name__ == '__main__':
    ws_loc = tpce.subscribe_all()["location"]
    ws = websocket.WebSocketApp(ws_loc, on_message = on_message, on_error = on_error)
    ws_thread = Thread(target = ws.run_forever, daemon = True)
    ws_thread.start()
    app.run_server()
