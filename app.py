from utils.utils import *

load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

# ----------------------------
# Streamlit UI
# ----------------------------

st.set_page_config(page_title = "End to End AI Enabled Test Cases Generation and Automation Dashboard", layout = "wide")

st.title("End to End AI Enabled Test Cases Generation and Automation Dashboard")

inputRequirement = st.text_area(
    "Enter Requirements File/Text",
    height = 300,
    placeholder = "Paste raw requirements here..."
)

generateBtn = st.button("Generate Outputs")

if generateBtn:
    if not inputRequirement.strip():
        st.warning("Please enter some text before generating.")
    else:
        tab1, tab2, tab3 = st.tabs(["Feature File", "Verification Output", "Scripts"])
        with st.spinner("Generating Feature File ..."):
            featureFile = generateFeatureFile(inputRequirement)

        with tab1:
            st.subheader("Generated Feature File")
            st.code(featureFile, language = "gherkin")

        with st.spinner("Generating Verification Agent Output ..."):
            verificationOutput = generateVerificationOutput(featureFile, inputRequirement)

        with tab2:
            st.subheader("Verification Agent Output")
            st.text(verificationOutput)
        
        with st.spinner("Generating Automation Scripts ..."):
            scripts = generateAutomationScripts(featureFile)

        with tab3:
            st.subheader("Generated Scripts")
            st.code(scripts, language = "java")
