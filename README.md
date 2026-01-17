
# AI Automation From Requirements

This project automates the process of converting natural language requirements into Gherkin feature files, verifies them, and generates Java automation scripts for API testing. It leverages LLMs, Streamlit, and modular prompt engineering for end-to-end automation.

## Features
- Generate Gherkin feature files from raw requirements
- Verify feature files against requirements
- Generate Java step definitions for API automation (RestAssured, Cucumber, TestNG)
- Modular prompt system for easy extension
- Streamlit UI for interactive usage
- Utilities for merging, parsing, and handling feature files and Java code

## Setup and Installation

### Quick Start (Recommended)

**For Unix/Mac/Linux:**
```bash
# Make setup script executable (first time only)
chmod +x setup.sh

# Run setup script
./setup.sh
```

**For Windows:**
```cmd
# Run setup script
setup.bat
```

The setup script will:
- Create a virtual environment (`.venv/`)
- Install all dependencies from `requirements.txt`
- Create a `.env` file template (if it doesn't exist)

### Manual Setup

If you prefer to set up manually:

1. **Create a virtual environment:**
   ```bash
   python3 -m venv .venv
   ```

2. **Activate the virtual environment:**
   - **Unix/Mac/Linux:**
     ```bash
     source .venv/bin/activate
     ```
   - **Windows:**
     ```cmd
     .venv\Scripts\activate
     ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Set up your `.env` file:**
   Create a `.env` file in the root directory with your API keys:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```
   
   Get your GROQ API key from: https://console.groq.com/keys

## How to Run

1. **Activate the virtual environment** (if not already activated):
   - **Unix/Mac/Linux:**
     ```bash
     source .venv/bin/activate
     ```
   - **Windows:**
     ```cmd
     .venv\Scripts\activate
     ```

2. **Start the Streamlit app:**
   ```bash
   streamlit run app.py
   ```

3. The app will open in your browser automatically. If not, navigate to the URL shown in the terminal (usually `http://localhost:8501`)

4. **Configure API Key:**
   - You can enter your GROQ API key in the sidebar, OR
   - Set it in the `.env` file (recommended for convenience)

## Requirements

- **Python 3.8+** (Python 3.13.5 or higher recommended)
- **GROQ API Key** (free tier available at https://console.groq.com/keys)

## Troubleshooting

### Error: "Completions.create() got an unexpected keyword argument 'reasoning_effort'"
This error occurs if you're using an older version of `langchain-groq`. The setup script will install the correct version. If you encounter this:
```bash
pip install --upgrade langchain-groq langchain-core
```

### Virtual Environment Not Activating
Make sure you're using the correct activation command for your operating system:
- Unix/Mac/Linux: `source .venv/bin/activate`
- Windows: `.venv\Scripts\activate`

## Directory Structure

```text
ai-automation-from-requirements/
├── README.md
├── requirements.txt
├── .env
├── app.py
├── test_notebook.ipynb
├── test_notebook-v2.ipynb
├── llm_prompts/
│   ├── requirement_agent.py
│   ├── verification_agent.py
│   ├── java_automation_script_agent.py
│   └── __init__.py
├── utils/
│   ├── utils.py
│   ├── llm_config.py
│   └── __init__.py
├── old_files/                # Archive of previous/experimental notebooks and scripts
├── features/                 # (Optional) For feature file and Java code parsing/=
│   ├── parser.py
│   ├── merger.py
│   └── ...
├── llm_prompts/
│   └── ...
└── ...
```

### Notebooks
- `test_notebook.ipynb`, `test_notebook-v2.ipynb`: Interactive testing and demonstration of the pipeline.

### Prompts
- `llm_prompts/`: Contains all system prompt templates for the agents.

### Utilities
- `utils/`: Common utility functions and LLM configuration.

### Old Files
- `old_files/`: Contains legacy or experimental notebooks/scripts for reference.

### Features (Optional)
- `features/`: (If present) Modules for parsing and merging Gherkin/Java files.

## Contributing
Contributions are welcome! Please open issues or submit pull requests for improvements.

## License
MIT License (add your license file if not present)
