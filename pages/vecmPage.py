import streamlit as st
import matplotlib.pyplot as plt
import datetime
import os, sys

vecmPath = os.path.dirname(__file__) + '/../vecm'
sys.path.append(vecmPath)
import vecmStreamlit as vecm

plt.style.use('ggplot')

SECONDSBACKTORETRIEVE = 3600

def render(secretDict):

    vecmBlurb = '''
        What is the current price of Ether right now? This question is more subtle than it may appear. ETH trades on many exchanges all over the world. Arbitrage opportunities keep prices from diverging too much but prices on different exchanges are not always the same. When you look up "the" price of ETH on a website, chances are they are using some sort of weighted average over exchanges to derive a single "true" price. However this method has undesirable statistical properties and there is a more mathematically sound, principled way of aggregating trade prices in order to estimate the latent (or "true") price of a crypto asset. Below we show the “true price” of ETH from a model that does not use weighted averages. To learn more about our method and the research behind it, please reach out to us or stay tuned for the methodology paper.
        '''

    st.write(f"### Crypto Benchmarks")
    st.write(vecmBlurb)

    timestampUpper = datetime.datetime.now(datetime.timezone.utc)
    timestampLower = timestampUpper - datetime.timedelta(seconds=SECONDSBACKTORETRIEVE)

    fig0, fig1, temp = vecm.latentPriceFigures(secretDict, timestampLower, timestampUpper)
    st.plotly_chart(fig0, use_container_width=True)
    
    realizedVolatilityBlurb = '''
        Unlike other benchmarks ours has the desirable statistical property of being Brownian Motion. This enables us to now use this timeseries to calculate realized volatility in the natural way. Otherwise the realized volatility will be biased.
    '''

    st.write(realizedVolatilityBlurb)

    st.plotly_chart(fig1, use_container_width=True)

