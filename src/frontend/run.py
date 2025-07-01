"""
Streamlit Web Interface Runner

This module handles the execution of the Streamlit web interface.
It's designed to be run independently or through the CLI.
"""

import sys
import streamlit.web.cli as stcli

def run_streamlit():
    """Run the Streamlit web interface"""
    sys.argv = ["streamlit", "run", "src/frontend/app.py"]
    sys.exit(stcli.main())

if __name__ == "__main__":
    run_streamlit() 