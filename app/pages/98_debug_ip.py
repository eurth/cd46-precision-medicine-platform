"""
Helper script to hit an external IP service to debug Streamlit Cloud proxy headers.
"""
import requests
import streamlit as st

st.write("Headers seen by app:")
st.json(dict(st.context.headers))
