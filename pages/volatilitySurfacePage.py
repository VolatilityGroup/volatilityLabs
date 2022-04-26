import streamlit as st

def render():
    volatilitySurfaceBlurb = '''
    In theory, implied volatility should be constant over option strikes and expirations.  In practice this is far from true.  Below we visualize the volatility surface for ETH options which is clearly not flat!
    '''

    st.write(volatilitySurfaceBlurb)
    st.write(f"### Volatility Surface - COMING SOON!")