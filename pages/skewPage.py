import streamlit as st

def render():
    skewBlurb = '''
    Skew is the implied volatility disparity between different strike prices with the same expiration. Below we graph the skew as a function of time.
    '''
    
    st.write(skewBlurb)
    st.write(f"### Volatility Skew - COMING SOON!")