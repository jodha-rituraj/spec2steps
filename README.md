
# AI Automation From Requirements

This project automates the process of converting natural language requirements into Gherkin feature files, verifies them, and generates Java automation scripts for API testing. It leverages LLMs, Streamlit, and modular prompt engineering for end-to-end automation.

## Features
- Generate Gherkin feature files from raw requirements
- Verify feature files against requirements
- Generate Java step definitions for API automation (RestAssured, Cucumber, TestNG)
- Modular prompt system for easy extension
- Streamlit UI for interactive usage
- Utilities for merging, parsing, and handling feature files and Java code

## How to Run
1. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2. Set up your `.env` file with required API keys.
3. Start the Streamlit app:
    ```bash
    streamlit run app.py
    ```

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
