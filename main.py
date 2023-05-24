import streamlit as st
import io
import pandas as pd
import plotly.express as px
import numpy as np
import plotly.graph_objects as go

# st.set_option('deprecation.showfileUploaderEncoding', False)

with open('favicon.png', 'rb') as f:
    favicon = io.BytesIO(f.read())

st.set_page_config(page_title='Bus Timings',
                   page_icon=favicon, 
                   initial_sidebar_state='expanded',layout='wide')
st.image("./siemens_logo.png", width = 150)
option = 'No missing timings'
st.title('Fleet Management Analytics')

def compute_wt(df):
    swt_df = df.diff()/pd.Timedelta(minutes=1)
    swt_df.dropna(inplace=True)
    swt_df = swt_df.to_numpy()
    return np.sum(swt_df**2)/(2*np.sum(swt_df))


dict_of_keywords = {'No missing timings':'no_missing','Missing start timings':'missing_front','Missing end timings':'missing_end'}

keyword = dict_of_keywords[option]
df_nm_sched = pd.read_excel('data.xlsx',sheet_name=f'{keyword}_sched')
df_nm_oper = pd.read_excel('data.xlsx',sheet_name=f'{keyword}_operated')
df_nm_sched.set_index('Trip',inplace=True)
df_nm_oper.set_index('Trip',inplace=True)
df_nm_oper = df_nm_oper.apply(pd.to_datetime,format='%H:%M:%S')
df_nm_sched = df_nm_sched.apply(pd.to_datetime,format='%H:%M:%S')
delta = (df_nm_oper - df_nm_sched)/ pd.Timedelta(minutes=1)
delta = delta.T
delta.fillna(method="bfill",inplace=True)
delta.fillna(method="ffill",inplace=True)

nan_iloc = np.where(df_nm_oper.isna()) # find nan locations
delta_T = delta.copy()
delta_T = delta.T

for xy in zip(nan_iloc[0],nan_iloc[1]):
    df_nm_oper.iloc[xy] = df_nm_sched.iloc[xy] + pd.Timedelta(delta_T.iloc[xy], "min") 

for col in df_nm_oper.columns: #sorting
    df_nm_oper[col] = df_nm_oper[col].sort_values(ignore_index=True).values

# computing delta again after updating df_nm_oper
delta = (df_nm_oper - df_nm_sched)/ pd.Timedelta(minutes=1)
delta = delta.T

swt = np.round(compute_wt(df_nm_sched),2) # scheduled
awt = np.round(compute_wt(df_nm_oper),2) # operated
ewt = awt - swt

service_col, service_pkg, operator, col1, col2 = st.columns([1,1,1,2,2])

with service_col:
    fig = go.Figure()
    fig.add_trace(go.Indicator(
    mode = "number",
    value = 900,
    title = {"text": "Service no."},
))

    fig.update_layout(paper_bgcolor = "lavender", font = {'color': "darkblue", 'family': "Arial"}, height=200,margin={'t': 0,'l':0,'b':0,'r':0})
    st.plotly_chart(fig, use_container_width=True)


with service_pkg:
    fig = go.Figure()
    fig.add_trace(go.Indicator(
    mode = "number",
    value=6,
    number = { "prefix": "PT-21"},
    title = {"text": "Service package"},
))

    fig.update_layout(paper_bgcolor = "lavender", font = {'color': "darkblue", 'family': "Arial"}, height=200,margin={'t': 0,'l':0,'b':0,'r':0})
    st.plotly_chart(fig, use_container_width=True)

with operator:
    fig = go.Figure()
    fig.add_trace(go.Indicator(
    mode = "number",
    value = 1,
    title = {"text": "Operator"},
))

    fig.update_layout(paper_bgcolor = "lavender", font = {'color': "darkblue", 'family': "Arial"}, height=200,margin={'t': 0,'l':0,'b':0,'r':0})
    st.plotly_chart(fig, use_container_width=True)


with col1:
    fig = go.Figure()

    fig.add_trace(go.Indicator(
        mode = "number+delta",
        value = ewt,
        number = { "suffix": " mins."},
        delta={'reference': 2.0, 'position': "bottom", 'relative': True, 'increasing': {'color': 'red'},'decreasing': {'color': 'green'}},
        title = {"text": "Excess Waiting Time"},
    ))
    fig.update_layout(paper_bgcolor = "lavender", font = {'color': "darkblue", 'family': "Arial"}, height=200,margin={'t': 0,'l':0,'b':0,'r':0})
    st.plotly_chart(fig, use_container_width=True)

OTA = (1-((delta>5) | (delta<-2)).sum().sum()/delta.size)*100
fig = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = OTA,
    number = { "suffix": "%"},
    title = {'text': "On-Time Adherence (%)"},
    domain = {'x': [0, 1], 'y': [0, 1]},
    gauge = {'axis': {'range': [0, 100]},
              'bar': {'color': "darkblue"},'borderwidth': 2, 
             'steps' : [
                 {'range': [0, 50], 'color': "cyan"},
                 {'range': [50, 100], 'color': "royalblue"}]}
))

fig.update_layout(paper_bgcolor = "lavender", font = {'color': "darkblue", 'family': "Arial"}, height=200, margin={'t': 60,'l':0,'b':10,'r':0})

with col2:
    st.plotly_chart(fig, use_container_width=True)

text = df_nm_sched.applymap(lambda x: x.strftime('%H:%M')).to_numpy()[::-1,:]
z = delta.to_numpy().T[::-1,:] 
text = text + ' + (' + z.astype(str) + "')"
# Create heatmap object
# Set the minimum and maximum values
zmin = delta.min().min()
zmax = delta.max().max()
zrange = zmax - zmin

green_1 = (-2-zmin)/zrange # -2
green_2 =  (5-zmin)/zrange # 5
# Define the colorscale
colorscale = [[0, 'red'],[green_1-0.0001,'red'] ,[green_1, 'green'], [green_2,'green'],[green_2+0.0001,'red'],[1,'red']]
# Create heatmap object
fig = go.Figure(data=go.Heatmap(z=z, textfont=dict(size=16),text=text,xgap=1,ygap=2, texttemplate="%{text}",colorscale=colorscale
                               ,hovertemplate='Trip=%{y} <br>Bus-stop=%{x} <br>Delay (in minutes)=%{z}<extra></extra>'))

# Define x-axis and y-axis objects
xaxis = go.layout.XAxis(
    tickmode='array',
    tickvals= np.arange(df_nm_sched.shape[1]),
    ticktext=list(df_nm_sched.columns),
    title='Bus stop',
    tickfont=dict(size=18)
)
yaxis = go.layout.YAxis(
    tickmode='array',
    tickvals=np.arange(df_nm_sched.shape[0]),
    ticktext=np.arange(df_nm_sched.shape[0])[::-1]+1,
    title='Trips',
    tickfont=dict(size=18)
)

# Set axis labels and title
fig.update_layout(
    xaxis=xaxis,
    yaxis=yaxis,
    title='Trip-wise Adherence to schedule (Heatmap)',
    hoverlabel=dict(
        font_size=16,
    )     
)
# Set the colorscale for the heatmap
# fig.update_traces(colorscale='Reds')
fig.update_traces(zmin=zmin, zmax=zmax)
fig.update_layout(xaxis_title_font=dict(size=20), yaxis_title_font=dict(size=20))
st.plotly_chart(fig, use_container_width=True)

fig = px.line(delta,markers=True,title='Trip-wise Adherence to schedule (Line Chart)',labels={"value": "Delay (in minutes)","index":"Bus stop"}
             ,range_y=[min(-4,delta.min().min()-2),max(delta.max().max()+2,10)],symbol='Trip')
fig.update_layout(margin={'t': 60,'l':10,'b':10,'r':0},xaxis_title_font=dict(size=20), yaxis_title_font=dict(size=20), xaxis=dict(tickfont=dict(size=18)), yaxis=dict(tickfont=dict(size=18)))
st.plotly_chart(fig, use_container_width=True)