import streamlit as st

st.set_page_config(
    page_title="Visiontech CRM | Home",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
    <div style="padding: 2.5rem; background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%); border-radius: 16px; text-align: center; color: white;">
        <h1>⚡ Visiontech CRM⚡</h1>
        <p style="font-size: 1.1rem; margin-top: 10px;">Select a page from the sidebar to manage your workflows & database.</p>
    </div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.success("✅ Multi-page mode active hai! Left sidebar se koi bhi page select karein.")
