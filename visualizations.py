# from attr import s
import streamlit as st 
import pandas as pd
# import geopandas as gpd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

### CONSTANTS
PRIMARY_FEATURE = 'trip_name'
ANALYSIS_FEATURE = 'route_id'
TOKEN = "pk.eyJ1Ijoic2hhbm5vbm5ha2FtdXJhIiwiYSI6ImNrbG9zbG44OTB2d2Eyd20yc3FkYXVib3oifQ.Mck3r247wz8bgWvROUi_ww"
convert_from_km_to_miles = 0.621371

def make_scatter_length(df: pd.DataFrame, value: str, legend: bool):
    temp_df = df.drop_duplicates(subset=['trip_id'],keep='last')
    scatter_route_object = go.Scatter(
                x=pd.date_range('00:00', '23:59', freq='60min').strftime('%-I%p'),
                y=temp_df.loc[temp_df[ANALYSIS_FEATURE]==value].groupby(['start_hour'])['dist_traveled'].sum()*convert_from_km_to_miles,
                # name = str(value),
                hovertemplate =
                    temp_df.loc[temp_df[ANALYSIS_FEATURE]==value, ANALYSIS_FEATURE].astype(str) + '<br>'+
                    '<extra></extra>',
                mode = 'markers+lines',
                marker = dict(
                    color = '#'+temp_df.loc[temp_df[ANALYSIS_FEATURE]==value, 'route_color'],
                    opacity = 0.6,
                ),
                line = dict(
                    color = '#'+temp_df.loc[temp_df[ANALYSIS_FEATURE]==value, 'route_color'].iloc[0],
                ),
                showlegend = legend,
                stackgroup='one',
            )
    return scatter_route_object

def make_scatter_routes(df: pd.DataFrame, value: str, legend: bool):
    temp_df = df.copy()
    scatter_route_object = go.Scatter(
                x=pd.date_range('00:00', '23:59', freq='60min').strftime('%-I%p'),
                y=temp_df.loc[temp_df[ANALYSIS_FEATURE]==value].groupby(['start_hour'])['trip_id'].nunique(),
                name = str(value),
                hovertemplate =
                    temp_df.loc[temp_df[ANALYSIS_FEATURE]==value, ANALYSIS_FEATURE].astype(str) + '<br>'+
                    '<extra></extra>',
                mode = 'markers+lines',
                marker = dict(
                    color = '#'+temp_df.loc[temp_df[ANALYSIS_FEATURE]==value, 'route_color'],
                    opacity = 0.6,
                ),
                line = dict(
                    color = '#'+temp_df.loc[temp_df[ANALYSIS_FEATURE]==value, 'route_color'].iloc[0],
                ),
                showlegend = legend,
                stackgroup='one'
            )
    return scatter_route_object

def make_scattermapbox(df: pd.DataFrame, value: str):
    temp = df.copy()
    # temp.sort_values(by='dt', inplace=True)
    scattermapbox_object = go.Scattermapbox(
                lat = temp.loc[temp[PRIMARY_FEATURE]==value, 'stop_lat'],
                lon = temp.loc[temp[PRIMARY_FEATURE]==value, 'stop_lon'],
                name = str(temp.loc[temp[PRIMARY_FEATURE]==value, 'stop_name'].iloc[0]),
                # name = temp.loc[temp['block_id']==temp.loc[temp[PRIMARY_FEATURE]==value, 'block_id'].iloc[0], 'direction'],
                # name = str(",".join(sorted(item for item in temp.loc[temp['bus_id']==temp.loc[temp[PRIMARY_FEATURE]==value, 'bus_id'].iloc[0], 'direction'].unique() if not(pd.isnull(item))))),
                hovertemplate =
                    temp.loc[temp[PRIMARY_FEATURE]==value, 'stop_name'].astype(str) + '<br>'+
                    'Elevation: '+temp.loc[temp[PRIMARY_FEATURE]==value, 'elevation'].astype(str) + ' ft.'+'<br>'+
                    '<extra></extra>',
                mode='markers+lines',
                showlegend=False
            )
    return scattermapbox_object


def make_JG_location(df: pd.DataFrame, value: str):
    temp = df.copy()
    scattermapbox_object = go.Scattermapbox(
                lat = temp.loc[temp['stop_name']=='5 AV/36 ST', 'stop_lat'],
                lon = temp.loc[temp['stop_name']=='5 AV/36 ST', 'stop_lon'],
                name = 'Jackie Gleason Depot',
                hovertemplate = (
                    'Jackie Gleason Depot' +
                    '<extra></extra>'
                ),
                mode='markers+lines',
                marker = dict(
                    size = 20,
                    # color = temp.loc[temp[PRIMARY_FEATURE]==value, 'color'],
                    symbol = 'circle'
                ),
                # line = dict(
                    # color = temp.loc[temp[PRIMARY_FEATURE]==value, 'color'].iloc[0]
                # ),
                # legendgroup = temp.loc[temp[PRIMARY_FEATURE]==value, 'bus_id'].iloc[0],
                # legendgrouptitle_text= 'Bus ID '+str(temp.loc[temp[PRIMARY_FEATURE]==value, 'bus_id'].iloc[0]),
                # showlegend = temp.loc[temp['bus_id'] == temp.loc[temp[PRIMARY_FEATURE]==value, 'bus_id'].iloc[0], PRIMARY_FEATURE].unique()[0]==value,
                showlegend=False
            )
    return scattermapbox_object

def make_histogram(df: pd.DataFrame, xaxis:str, yaxis:str, value: str):
    histogram_object = go.Histogram(
                x = df.loc[df[yaxis]==df.loc[df[PRIMARY_FEATURE]==value, yaxis].iloc[0], xaxis],
                y = df.loc[df[yaxis]==df.loc[df[PRIMARY_FEATURE]==value, yaxis].iloc[0], yaxis],
                histfunc="max",
                orientation = 'h',
                # hovertemplate =
                    # 'Total distance traveled (mi): %{x}<br>' +
                    # 'Bus ID %{y}<br>'+
                    # '<extra></extra>',
                # marker = dict(
                    # color = df.loc[df[PRIMARY_FEATURE]==value, 'color'],
                # ),
                yaxis=None,
                showlegend = False
            )
    return histogram_object

def make_scatter3d(df: pd.DataFrame, value: str, legend: bool):
    temp_df = df.drop_duplicates(subset=['stop_name'])
    scatter3d_object = go.Scatter3d(
                x = temp_df.loc[temp_df[PRIMARY_FEATURE]==value, 'stop_lat'],
                y = temp_df.loc[temp_df[PRIMARY_FEATURE]==value, 'stop_lon'],
                z = temp_df.loc[temp_df[PRIMARY_FEATURE]==value, 'elevation'],
                # name = str(value),
                # hovertext = round(df.loc[df[PRIMARY_FEATURE]==value, 'elevation'], 0).astype(str)+' ft.',
                # hoverinfo = 'text',
                hovertemplate =
                    temp_df.loc[temp_df[PRIMARY_FEATURE]==value, 'stop_name'].astype(str) + '<br>'+
                    '<extra></extra>',
                # hoverlabel= dict(
                #     bgcolor = df.loc[df[PRIMARY_FEATURE]==value, 'color'].iloc[0]
                # ),
                mode = 'markers',
                marker = dict(
                    size = 5,
                    opacity = 0.6,
                    # color = df.loc[df[PRIMARY_FEATURE]==value, 'color'],
                ),
                # line = dict(
                #     color = df.loc[df[PRIMARY_FEATURE]==value, 'color'].iloc[0]
                # ),
                showlegend = False,
                # legendgroup = df.loc[df[PRIMARY_FEATURE]==value, feature].iloc[0],
                # legendgrouptitle_text= feature + ' ' + str(df.loc[df[PRIMARY_FEATURE]==value, feature].iloc[0])
            )
    return scatter3d_object

def highlight_bus_row(df):
    c1 = ['font-weight: bold; background-color: lightgrey; color: black']*len(df.index)
    c2 = ['background-color: white; color: darkgrey']*len(df.index)
    checklist = list(df.index == st.session_state['vehicle_type_selected']['model_name'].iloc[0])
    formatted_df = np.where(checklist, c1, c2)
    return formatted_df

def make_heatmapbox(df: pd.DataFrame, feature: str):
    temp = df.copy()
    temp.sort_values(by='start_time', inplace=True)
    fig = go.Figure(data= go.Densitymapbox(
                lat = temp['stop_lat'],
                lon = temp['stop_lon'],
                z = temp[feature],
                text = temp['stop_name'].astype(str),
                radius = 50,
                # name = str(",".join(sorted(temp.loc[temp['bus_id']==temp.loc[temp[selected_feat]==value, 'bus_id'].iloc[0], 'direction'].unique()))),
                hovertemplate =
                    "<b>%{text}</b><br>"+
                    # "State of Charge: %{z:.0%}<br>"+
                    '<extra></extra>',
                # legendgroup = temp.loc[temp[selected_feat]==value, 'bus_id'].iloc[0],
                # legendgrouptitle_text= 'Bus ID '+str(temp.loc[temp[selected_feat]==value, 'bus_id'].iloc[0]),
                # showlegend = temp.loc[temp['bus_id'] == temp.loc[temp[selected_feat]==value, 'bus_id'].iloc[0], selected_feat].unique()[0]==value
            ))
    layout = dict(
        height = 500,
        margin = dict(t = 0, b = 0, l = 0, r = 0),
        title = 'Potential Charging Locations',
        mapbox = dict(
            accesstoken = TOKEN,
            center = dict(lon = np.mean(df['stop_lon']), lat = np.mean(df['stop_lat'])),
            pitch = 60,
            zoom = 11,
            style = 'dark'
            )
        )

    fig.update_layout(
        layout
    )
    return fig

def make_scatter_capacity(df: pd.DataFrame, column:str, name:str, color: str, legend: bool):
    scatter_capacity_object = go.Scatter(
                x=pd.date_range('00:00', '23:59', freq='60min').strftime('%-I%p'),
                y=df[column],
                name = name,
                # hovertext = round(df.loc[df[PRIMARY_FEATURE]==value, 'elevation'], 0).astype(str)+' ft.',
                # hoverinfo = 'text',
                hovertemplate =
                    name + '<br>'
                    'Value: ' + df[column].astype(str) +
                    '<extra></extra>',
                # hoverlabel= dict(
                #     bgcolor = df.loc[df[PRIMARY_FEATURE]==value, 'color'].iloc[0]
                # ),
                mode = 'lines',
                line = dict(
                    color = color
                ),
                showlegend = legend,
            )
    return scatter_capacity_object

def make_bar_capacity(df: pd.DataFrame, column:str, name:str, color:str, legend: bool):
    bar_capacity_object = go.Bar(
                x=pd.date_range('00:00', '23:59', freq='60min').strftime('%-I%p'),
                y=df[column],
                name = name,
                # hovertext = round(df.loc[df[PRIMARY_FEATURE]==value, 'elevation'], 0).astype(str)+' ft.',
                # hoverinfo = 'text',
                hovertemplate =
                    '<b>' + name + '<b> <br>'
                    'Value: ' + df[column].astype(str) +
                    '<extra></extra>',
                # hoverlabel= dict(
                #     bgcolor = df.loc[df[PRIMARY_FEATURE]==value, 'color'].iloc[0]
                # ),
                # mode = 'lines',
                marker = dict(
                    color = color
                ),
                showlegend = legend,
            )
    return bar_capacity_object

