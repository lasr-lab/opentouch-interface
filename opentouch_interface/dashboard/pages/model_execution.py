import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

container = st.container()

with container:

    file: UploadedFile = st.file_uploader(
        label="Upload your pre-trained model",
        type=['pth'],
        accept_multiple_files=False,
        label_visibility="collapsed"
    )

    # if file:
    #     BaseCNN.load(file)
