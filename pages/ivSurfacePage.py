import streamlit as st
import matplotlib.pyplot as plt
import datetime
import os, sys

vecmPath = os.path.dirname(__file__) + '/../ivSurface'
sys.path.append(vecmPath)
import ivSurfaceStreamlit as ivSurface

plt.style.use('ggplot')

SECONDSBACKTORETRIEVE = 3600

def render(secretDict):
    surfaceBlurb = '''
    This is the implied volatility surface. In theory, implied volatility should be constant over option strikes and expirations.  In practice this is far from true.  Below we visualize the volatility surface for ETH options which is clearly not flat!
    '''
    st.write(surfaceBlurb)

    timestampUpper = datetime.datetime.now(datetime.timezone.utc)
    timestampLower = timestampUpper - datetime.timedelta(seconds=SECONDSBACKTORETRIEVE)

    fig0, temp = ivSurface.ivSurfaceFigures(secretDict, timestampLower, timestampUpper)
    st.plotly_chart(fig0, use_container_width=True)

    if temp is not None:
        st.write(temp)