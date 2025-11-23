To run this code in streamlit, open terminal and run below command and it will open a window in browser. If streamlit not installed, then run: pip install streamlit

    streamlit run app.py


Directory structure
Below is a suggested directory layout for this repository. It reflects the current language composition (Jupyter Notebooks and Python) and common project organization.

```text
ai-automation-from-requirements/
├── README.md
├── requirements.txt                        # Python dependencies
├── .env                                    # Store API Keys
├── app.py                                  # Streamlit app
├── test_notebook.ipynb                     # test the project using notebook
├── llm_prompts/                            # Define Agent System Prompts
│   ├── requirement_agent.py                # prompt to generate feature files
│   ├── verification_agent.py               # prompt for verification agent
│   ├── java_automation_script_agent.py     # prompt to generate automation scripts based on feature file in JAVA
├── utils/                                  # utils to define the common functions
│   ├── utils.py                            # common util functions
│   ├── llm_config.py                       # define LLM
```
