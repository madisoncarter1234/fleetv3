import os
import streamlit.web.cli as stcli
import sys

# Note: Set ANTHROPIC_API_KEY environment variable before running
# export ANTHROPIC_API_KEY="your-key-here"

# Run the Streamlit app
if __name__ == "__main__":
    sys.argv = ["streamlit", "run", "app.py", "--server.port", "8501"]
    sys.exit(stcli.main())