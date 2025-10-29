"""Plotly Dash application embedded inside Django for live analytics."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List

import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate
from dash_extensions import WebSocket
from django.db import OperationalError, ProgrammingError
from django.utils.timezone import localtime
from django_plotly_dash import DjangoDash

from .. import models

MAX_POINTS = 50


def _parse_datetime(value: datetime | str | None) -> str:
    if value is None:
        return ''
    if isinstance(value, str):
        return value
    return localtime(value).isoformat()


def _initial_payload() -> Dict[str, List[Dict[str, Any]]]:
    state = {'sensor': [], 'finance': [], 'traffic': [], 'weather': [], 'kafka': []}
    try:
        for reading in models.SensorReading.objects.order_by('-created_at')[:MAX_POINTS]:
            payload = reading.payload if isinstance(reading.payload, dict) else {'raw': reading.payload}
            state['sensor'].append(
                {
                    'id': reading.pk,
                    'source': reading.source,
                    'timestamp': _parse_datetime(reading.created_at),
                    'payload': payload,
                    'value': payload.get('value'),
                }
            )
        for metric in models.FinancialMetric.objects.order_by('-created_at')[:MAX_POINTS]:
            quote = metric.payload if isinstance(metric.payload, dict) else {}
            state['finance'].append(
                {
                    'id': metric.pk,
                    'symbol': metric.symbol,
                    'timestamp': _parse_datetime(metric.created_at),
                    'price': float(quote.get('05. price', 0) or 0),
                }
            )
        for update in models.TrafficUpdate.objects.order_by('-created_at')[:MAX_POINTS]:
            payload = update.payload if isinstance(update.payload, dict) else {}
            state['traffic'].append(
                {
                    'id': update.pk,
                    'region': update.region,
                    'timestamp': _parse_datetime(update.created_at),
                    'congestion_index': float(payload.get('congestion_index', 0) or 0),
                }
            )
        for snapshot in models.WeatherSnapshot.objects.order_by('-created_at')[:MAX_POINTS]:
            payload = snapshot.payload if isinstance(snapshot.payload, dict) else {}
            state['weather'].append(
                {
                    'id': snapshot.pk,
                    'location': snapshot.location,
                    'timestamp': _parse_datetime(snapshot.created_at),
                    'temperature': float(payload.get('main', {}).get('temp', 0) or 0),
                    'humidity': float(payload.get('main', {}).get('humidity', 0) or 0),
                }
            )
    except (OperationalError, ProgrammingError):  # Database not ready yet.
        return state

    for key, values in state.items():
        state[key] = list(reversed(values))
    return state


def _default_state() -> Dict[str, List[Dict[str, Any]]]:
    return {'sensor': [], 'finance': [], 'traffic': [], 'weather': [], 'kafka': []}


app: Dash = DjangoDash('RealTimeDashboard', serve_locally=True)

app.layout = html.Div(
    className='dashboard-container',
    children=[
        WebSocket(id='dashboard-websocket', url='/ws/dashboard/'),
        dcc.Store(id='dashboard-store', data=_initial_payload()),
        html.Div(
            className='dashboard-header',
            children=[
                html.H2('Real-time Monitoring Dashboard'),
                html.P('Powered by Django Channels, Celery, and Plotly Dash'),
            ],
        ),
        html.Div(
            className='dashboard-grid',
            children=[
                html.Div(className='dashboard-card', children=[dcc.Graph(id='sensor-graph')]),
                html.Div(className='dashboard-card', children=[dcc.Graph(id='finance-graph')]),
                html.Div(className='dashboard-card', children=[dcc.Graph(id='traffic-graph')]),
                html.Div(className='dashboard-card', children=[dcc.Graph(id='weather-graph')]),
            ],
        ),
    ],
)


@app.callback(
    Output('dashboard-store', 'data'),
    Input('dashboard-websocket', 'message'),
    State('dashboard-store', 'data'),
    prevent_initial_call=True,
)
def on_websocket_message(message: Dict[str, Any] | None, current: Dict[str, Any] | None) -> Dict[str, Any]:
    if not message:
        raise PreventUpdate

    data = message.get('data')
    if data is None:
        raise PreventUpdate

    if isinstance(data, str):
        event = json.loads(data)
    else:
        event = data

    event_type = event.get('event_type')
    event_payload = event.get('data', {})
    if not event_type:
        raise PreventUpdate

    store = current or _default_state()
    bucket = store.setdefault(event_type, [])
    bucket.append(event_payload)
    store[event_type] = bucket[-MAX_POINTS:]
    return store


@app.callback(Output('sensor-graph', 'figure'), Input('dashboard-store', 'data'))
def render_sensor_graph(store: Dict[str, Any] | None) -> go.Figure:
    store = store or _default_state()
    entries = store.get('sensor', [])
    if not entries:
        return go.Figure(layout={'title': 'Sensor Streams', 'template': 'plotly_dark'})

    x = [_parse_datetime(item.get('timestamp')) for item in entries]
    y = []
    for item in entries:
        value = item.get('value', item.get('payload', {}).get('value'))
        try:
            y.append(float(value))
        except (TypeError, ValueError):
            y.append(None)
    fig = go.Figure(
        data=[go.Scatter(x=x, y=y, mode='lines+markers', name='Value')],
        layout={'title': 'Sensor Streams', 'template': 'plotly_dark', 'xaxis_title': 'Time', 'yaxis_title': 'Value'},
    )
    return fig


@app.callback(Output('finance-graph', 'figure'), Input('dashboard-store', 'data'))
def render_finance_graph(store: Dict[str, Any] | None) -> go.Figure:
    store = store or _default_state()
    entries = store.get('finance', [])
    if not entries:
        return go.Figure(layout={'title': 'Financial Quotes', 'template': 'plotly'})

    symbols = [item.get('symbol') for item in entries]
    prices = [item.get('price') or 0 for item in entries]
    fig = go.Figure(
        data=[go.Bar(x=symbols, y=prices, marker_color='#2ca02c')],
        layout={'title': 'Financial Quotes', 'template': 'plotly', 'yaxis_title': 'Price (USD)'},
    )
    return fig


@app.callback(Output('traffic-graph', 'figure'), Input('dashboard-store', 'data'))
def render_traffic_graph(store: Dict[str, Any] | None) -> go.Figure:
    store = store or _default_state()
    entries = store.get('traffic', [])
    if not entries:
        return go.Figure(layout={'title': 'Traffic Congestion', 'template': 'plotly_dark'})

    x = [_parse_datetime(item.get('timestamp')) for item in entries]
    y = [item.get('congestion_index') or 0 for item in entries]
    fig = go.Figure(
        data=[go.Scatter(x=x, y=y, mode='lines', line={'color': '#ff7f0e'})],
        layout={'title': 'Traffic Congestion', 'template': 'plotly_dark', 'yaxis_range': [0, 1]},
    )
    return fig


@app.callback(Output('weather-graph', 'figure'), Input('dashboard-store', 'data'))
def render_weather_graph(store: Dict[str, Any] | None) -> go.Figure:
    store = store or _default_state()
    entries = store.get('weather', [])
    if not entries:
        return go.Figure(layout={'title': 'Weather - Temperature & Humidity', 'template': 'plotly'})

    x = [_parse_datetime(item.get('timestamp')) for item in entries]
    temperature = [item.get('temperature') for item in entries]
    humidity = [item.get('humidity') for item in entries]

    fig = go.Figure(
        data=[
            go.Scatter(x=x, y=temperature, mode='lines+markers', name='Temperature (°C)', line={'color': '#1f77b4'}),
            go.Scatter(x=x, y=humidity, mode='lines+markers', name='Humidity (%)', line={'color': '#17becf'}, yaxis='y2'),
        ],
        layout={
            'title': 'Weather - Temperature & Humidity',
            'template': 'plotly',
            'yaxis': {'title': 'Temperature (°C)'},
            'yaxis2': {'title': 'Humidity (%)', 'overlaying': 'y', 'side': 'right'},
        },
    )
    return fig
