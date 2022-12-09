import datetime

import streamlit as st
import configparser
import pandas as pd
from parse_data import *
import numpy as np


# Config
st.set_page_config(
    page_title='천안시 성환읍 농가 모니터링'
)
config = configparser.ConfigParser()
config.read('config.ini')


# Set Max Width
def _max_width_():
    max_width_str = f"max-width: 1400px;"
    st.markdown(
        f"""
    <style>
    .reportview-container .main .block-container{{
        {max_width_str}
    }}
    </style>    
    """,
        unsafe_allow_html=True,
    )

_max_width_()

st.title("새팜 솔루션 보고서")
st.header("")

map = pd.DataFrame(
    {'lat': [131.9, 131.8],
     'lon': [43.1333, 43.111]}
)

crop_to_select = '쌀'
crop_code = {'옥수수': 'maize',
             '대두': 'soybean',
             '쌀': 'rice'}
# Read Data
summary = parse_summary('{0}/summary.csv'.format(crop_code[crop_to_select]))
events_sol = parse_mgmtevent('{0}/MgmtEvent.OUT'.format(crop_code[crop_to_select]))['Solution']
events_stage = parse_mgmtevent('{0}/MgmtEvent.OUT'.format(crop_code[crop_to_select]))['Stage']
plantgro= parse_plantgro('{0}/plantgro.csv'.format(crop_code[crop_to_select]))


st.markdown("## 최적 솔루션")
Today = datetime.datetime(2022, 5, 7) if crop_to_select == '옥수수' else datetime.datetime(2022, 7, 7)
to_day = lambda x: datetime.datetime(2022, 1, 1) + datetime.timedelta(int(x) - 1)
st.markdown("### {0}".format(Today.strftime("%Y - %m - %d")))

col1, col2 = st.columns(2)
planting_date = to_day(int(str(summary['Planting'])[4:]))
germinate_date = to_day(int(str(summary['Germinate'])[4:]))
harvest_date = to_day(int(str(summary['Harvest'])[4:])+32)

col1.metric("모내기", planting_date.strftime("%Y - %m - %d"), (Today-planting_date).days)
col2.metric("수확일", harvest_date.strftime("%Y - %m - %d"), (Today-harvest_date).days)

st.markdown('')

st.markdown("### **예상 수확량**: *{0}*kg/Ha".format(summary["Yield"]))

translate = {"Planting": "파종",
             "Fertilizer": "시비",
             "Irrigation": "관개",
             "Organic matter": "유기 비료",
             "Harvest Yield": "수확"}
events_sol = pd.DataFrame(events_sol)
events_sol.columns = ['농작업', '양','일자']
events_sol.replace(np.NAN, 0.0)
events_sol = events_sol[['일자', '농작업', '양']]
events_sol['일자'] = events_sol['일자'].map(to_day)
events_sol['일자'] = events_sol['일자'].map(lambda x: x.strftime("%Y / %m / %d"))

events_sol['농작업'] = events_sol['농작업'].map(lambda x: translate[x])

st.dataframe(events_sol,
             width=10000)

st.markdown("## 생육 모니터링")
st.markdown("### 현재 {0}는 *{1}*입니다".format(crop_to_select, '무효 분얼기'))
st.markdown("**현 시기에 해야 할 농작업은 아래와 같습니다**")
st.markdown("* 둑 열기 (중간 물떼기): 뿌리의 활력을 증대시키고 질소 흡수율을 줄여 도복을 방지")
st.markdown("* 논바닥에 살짝 실금이 갈 정도로 물을 빼야 합니다")

st.subheader("엽면적지수")
st.area_chart(plantgro["LAID"])

st.subheader("수분 스트레스")
st.area_chart(pd.concat([
    plantgro['Water Stress'],
    plantgro['Nitrogen Stress'],
], axis=1))

c1, c2 = st.columns(2)
c1.subheader("지상부 크기")
c1.line_chart(plantgro["Canopy Height"])

c2.subheader("지하부 크기")
c2.line_chart(plantgro["Root Depth"])


