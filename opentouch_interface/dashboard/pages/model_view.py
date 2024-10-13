import streamlit as st
from opentouch_interface.dashboard.models.model_registry import ModelRegistry

# Retrieve the model registry from the session state
model_registry: ModelRegistry = st.session_state.model_registry

# Display an info message if no models are available in the registry
if model_registry.model_count <= 0:
    st.info(
        "Add models on the 'Add Model' page to display them here.",
        icon="💡"
    )

# Render the model registry interface (input/output display for all registered models)
model_registry.render()
