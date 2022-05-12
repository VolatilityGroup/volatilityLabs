import streamlit as st
import matplotlib.pyplot as plt
from pages import formalSpecPage, vecmPage, nftPage
from pages import skewPage, volatilitySurfacePage, monteCarloPage

plt.style.use('ggplot')

pwd = st.secrets['labsPassword']
moralisKey = st.secrets['moralisKey']

st.set_page_config(layout="wide")

topic = ['LatestPricesUsingVECM', 
         'FormalSpecification', 
         'NFTAnalytics', 
         'VolatilitySkew', 
         'ImpliedVolatilitySurface', 
         'LiquidationRisk']

params = st.experimental_get_query_params()

topicSelection = params.get('topic')[0]
queryPwd = params.get('pw')[0]

if pwd == queryPwd:
	if topicSelection == topic[0]:
		vecmPage.render(st.secrets)

	elif topicSelection == topic[1]:
		formalSpecPage.render()

	elif topicSelection == topic[2]:
		nftPage.render(moralisKey)

	elif topicSelection == topic[3]:
		skewPage.render()

	elif topicSelection == topic[4]:
		volatilitySurfacePage.render()

	elif topicSelection == topic[5]:
		monteCarloPage.render(st.secrets)