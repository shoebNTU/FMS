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
st.sidebar.image("./siemens_logo.png", width = 300)
with st.sidebar:
    st.info('''We give an option to the user to select and analyze one among the following datasets at a time - 
            \n * No missing timings (selected by default) \n * Missing start timings \n * Missing end timings''')
    option = st.selectbox(
    'Which dataset do you want to analyze?',
    ('No missing timings', 'Missing start timings', 'Missing end timings'))

st.title('Fleet Management Analytics')
st.subheader(f'Dataset - _:blue[{option}]_')


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

swt = np.round(compute_wt(df_nm_sched),2) # scheduled
awt = np.round(compute_wt(df_nm_oper),2) # operated
ewt = awt - swt

col1, col2 = st.columns(2)

fig = go.Figure()

fig.add_trace(go.Indicator(
    mode = "number",
    value = ewt,
    number = { "suffix": " mins."},
    title = {"text": "Excess Waiting Time"},
))

fig.update_layout(paper_bgcolor = "lavender", font = {'color': "darkblue", 'family': "Arial"}, height=200,margin={'t': 0,'l':0,'b':0,'r':0})
with col1:
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

fig = px.line(delta,markers=True,title='Trip-wise Adherence to schedule',labels={"value": "Delay (in minutes)","index":"Bus stop"}
             ,range_y=[min(-4,delta.min().min()-2),max(delta.max().max()+2,10)],symbol='Trip')
fig.update_layout(margin={'t': 60,'l':10,'b':10,'r':0},font=dict(size=18))
st.plotly_chart(fig, use_container_width=True)