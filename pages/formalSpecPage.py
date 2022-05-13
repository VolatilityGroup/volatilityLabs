import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import base64
import os
plt.style.use('ggplot')


def render():
    pdfFlag = False
    specPDF = os.path.dirname(__file__) + '/../specs/uma.pdf'
    specTLA = os.path.dirname(__file__) + '/../specs/uma.tla'

    formalBlurb = '''
    To address the insecurity epidemic in DeFi, we are leveraging mathematical tools called "lightweight formal methods". We are preparing formal specifications of decentralized protocols using languages like TLA+ and Alloy. We are also developing new tools to simplify the creation and analysis of formal specifications. Here is a formal specification of UMA's optimistic oracle written in TLA+:
    '''

    st.write(f"### Formal Specification of Protocols")
    st.write(formalBlurb)

    if pdfFlag:
        # PDF GETS BLOCKED BY CHROME!!
        with open(specPDF,"rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="1000" height="1000" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    
    else: 
        with open(specTLA, "r") as fp:
            rawTLA = fp.read()
        st.code(rawTLA)