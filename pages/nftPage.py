import streamlit as st
import os, sys
import plotly.express as px
from dateutil import parser

moralisPath = os.path.dirname(__file__) + '/../moralis'
sys.path.append(moralisPath)
import moralis

collectionDict = {'Bored Ape Yacht Club':'0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D',
                  'Azuki': '0xED5AF388653567Af2F388E6224dC7C4b3241C544',
                  'Art Blocks Curated': '0xa7d8d9ef8D8Ce8992Df33D8b8CF4Aebabd5bD270'}

def render(moralisKey):
    collectionName = st.selectbox('Select NFT Collection:', list(collectionDict.keys()))

    tokenAddress = collectionDict[collectionName]

    urlTrades = moralis.nftTradesURL(tokenAddress, daysBack=10)
    allResults = moralis.moralisAll(urlTrades, moralisKey, False)

    x = [parser.parse(i['block_timestamp']) for i in allResults]
    y = [float(i['price'])/10**18 for i in allResults]

    fig = px.scatter(x=x, y=y, title=collectionName + " Recent Trades")
    fig.update_layout(xaxis_title="Date", yaxis_title="Price (ETH)",)
    st.plotly_chart(fig, use_container_width=True)


