import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import datetime
import os, sys

monteCarloPath = os.path.dirname(__file__) + '/../monteCarlo'
sys.path.append(monteCarloPath)
import monteCarlo as mc

plt.style.use('ggplot')

SECONDSBACKTORETRIEVE = 3600

def updateBarrier(paths):
    barrierProb = mc.barrierProbGet(paths, float(st.session_state['threshold']))
    st.session_state['barrierProb'] = barrierProb

def render(secretDict):
    st.write(f"### Liquidation Risk")
    liquidationBlurb = '''
    Collateralized positions are subject to liquidation if spot prices experience large movements.
    Here we use recent historical data and Monte Carlo simulation to sample possible near-term future
    price dynamics and assess the probability of hitting liquidation thresholds.
    '''
    st.write(liquidationBlurb)

    #timestampUpper = datetime.datetime(2022, 4, 13)
    timestampUpper = datetime.datetime.now(datetime.timezone.utc)
    timestampLower = timestampUpper - datetime.timedelta(seconds=SECONDSBACKTORETRIEVE)

    try:
        ethPriceFig, samplesFig, currentPrice, paths, temp = mc.monteCarloFigures(secretDict, timestampLower, timestampUpper)
        st.write('here 3')
        st.plotly_chart(ethPriceFig, use_container_width=True)
        st.write('here 4')
        st.plotly_chart(samplesFig, use_container_width=True)
        st.write('here 5')

        if 'threshold' not in st.session_state:
            st.session_state['threshold'] = str(currentPrice * .95)

        if 'barrierProb' not in st.session_state:
            st.session_state['barrierProb'] = updateBarrier(paths)

    except:
        st.write("Temporary memory error.  Please try computation again.")

    st.text_input(label="Enter Threshold: ", key='threshold', on_change=updateBarrier, args=(paths,))
    
    st.write("The frequency of hitting the threshold is: ", st.session_state['barrierProb'])
    #st.write(temp)

#render(st.secrets)

