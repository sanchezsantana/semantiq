import sys
import os

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

STREAMLIT_ROOT = os.path.join(PROJECT_ROOT, "streamlit")

# IMPORTANTE: insert(0), no append
sys.path.insert(0, STREAMLIT_ROOT)