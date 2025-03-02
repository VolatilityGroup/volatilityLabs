import streamlit as st
import matplotlib.pyplot as plt
import datetime
import os, sys

vecmPath = os.path.dirname(__file__) + '/../garch'
sys.path.append(vecmPath)
import garchStreamlit as garch

plt.style.use('ggplot')

SECONDSBACKTORETRIEVE = 3600

def render(secretDict):
    garchBlurb = '''
    This is where the GARCH blurb goes eventually.
    '''
    st.write(garchBlurb)

    timestampUpper = datetime.datetime.now(datetime.timezone.utc)
    timestampLower = timestampUpper - datetime.timedelta(seconds=SECONDSBACKTORETRIEVE)

    fig0, temp = garch.garchFigures(secretDict, timestampLower, timestampUpper)
    st.plotly_chart(fig0, use_container_width=True)

    if temp != None:
        st.write(temp)