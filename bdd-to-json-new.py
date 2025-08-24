import os
import json
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain.schema import BaseOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.output_parsers.json import SimpleJsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
# Load environment variables from a .env file.
load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Initialize the language model (LLM) using environment variables.
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    google_api_key=google_api_key,
    temperature=0
)

# Custom parser for JSON output.
class StepsOutputParser(BaseOutputParser):
    def parse(self, text: str) -> dict:
        """Parses the JSON output from the LLM, ensuring it's valid and has the correct structure."""
        text = text.strip()
        # Auto-strip non-JSON chatter
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end != -1:
            text = text[start:end]

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        # Validate the parsed data.
        if not isinstance(data, dict) or "steps" not in data:
            raise ValueError("JSON must have a 'steps' key.")
        
        for step in data["steps"]:
            if "step" not in step or "capture" not in step:
                raise ValueError("Each step must have 'step' and 'capture' keys.")
            
            if "page" in step and not isinstance(step["page"], str):
                raise ValueError("'page' must be a string when present.")
        
        return data

# Initialize the custom parser.
parser = StepsOutputParser()


# Define the prompt template for the LLM.
# It acts as a BDD-to-JSON converter.
prompt = ChatPromptTemplate.from_template(
"""You are a BDD-to-JSON converter.
RETURN ONLY VALID JSON - no text before or after.

Format:
{{
  "steps": [
    {{
      "step": "<concise lowercase action>",
      "page": "<pageName>", // include ONLY if mentioned
      "capture": false
    }}
  ]
}}

Rules:
1. Read each step from BDD scenario outline.
2. For each step in the BDD scenario:
a. Check if a semantically similar step already exists in the "steps" list
b. If not, then only create new item in JSON only.
3. The JSON object must have two keys: "step", "capture" and "page" is optional only include if navigation at that step is required.
4. Avoid generating JSON for repetitive steps that are semantically the same. only include unique steps.
5. If a step is repeating with different data, consider generalizing it into a single step.
6. No extra text outside JSON.
7. If there is no page, omit the "page" key entirely.

Here are some examples of BDD steps and their JSON translations:

Example-1
bdd step: the user enters oneBankId
translate to json:
{{ "step": "enter oneBankId", "capture": false}}

Example-2
bdd step: the user enters oneBankPassword
translate to json:
{{ "step": "enter oneBankPassword", "capture": false}}

Example-3
bdd step: the user then clicks on login button on the login page
translate to json:
{{ "step": "click log in button", "page": "LoginPage", "capture": false}}

Now, convert the following BDD scenario to JSON using the same pattern: 

{bdd}

"""
)

# Read the BDD text from a sample feature file.
try:
    with open("sample.feature", "r", encoding="utf-8") as f:
        bdd_text = f.read()
except FileNotFoundError:
    print("Error: 'sample.feature' not found. Please create this file with your BDD steps.")
    exit()

# Create the LangChain processing chain.
chain = prompt | llm | parser

# Read existing JSON data from the output file if it exists.


# Invoke the chain to convert the BDD text.


def is_similar(new_step, existing_embeddings, threshold=0.85):
    """
    Check if new_step is semantically similar to any step in existing_steps.
    threshold: similarity score above which we treat steps as duplicates.
    """
    if not existing_steps:
        return False
    
    # Encode both new step and existing steps
    new_embedding = model.encode([new_step])
    #existing_embeddings = existing_steps
    
    # Compute cosine similarity
    similarities = cosine_similarity(new_embedding, existing_embeddings)[0]
    
    # Return True if any similarity >= threshold
    for sim in similarities:
        if sim >= threshold:
            return True

    return False

try:
    result = chain.invoke({"bdd": bdd_text})
    new_steps = result["steps"]

    try:
        with open("output.json", "r", encoding="utf-8") as f:
                existing_data = json.load(f)
    except FileNotFoundError:
        existing_data = {"steps": []}
    except json.JSONDecodeError:
        print("Error: output.json contains invalid JSON, starting with empty data.")
        existing_data = {"steps": []}

    existing_steps = existing_data["steps"]
    existing_embeddings = model.encode(existing_steps).tolist()  # s
    # Append only unique (semantic) steps
    for new_step in new_steps:
        if not is_similar(new_step, existing_embeddings):
            existing_data["steps"].append(new_step)
        else:
            print(new_step)


    # Write the updated data back to the output JSON file
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=2)

    print("JSON written successfully.")

except Exception as e:
    print(f"Error: {e}")

#88
#pip install sentence-transformers scikit-learn


PROMPT_TEMPLATE = """
You are a precise BDD-to-JSON converter.
Your ONLY job is to transform BDD steps into JSON according to the rules below.

OUTPUT RULES (highest priority):
1. RETURN ONLY valid JSON — no explanations, no commentary, no extra text.
2. Output must strictly follow this structure:
{
  "steps": [
    {
      "step": "<concise lowercase action>",
      "capture": true,
      "page": "<pagename>"   // include only if applicable
    }
  ]
}
3. Each item MUST contain "step" and "capture".
4. Exclude verification/assertion/validation steps (do not output them).
5. For click actions:
   - If the page name is mentioned → include it in "page".
   - If the page name is not mentioned → look ahead at the next 3–4 steps to see if a page name is specified. If yes, assign it.
   - If no page is ever mentioned → omit "page".
6. Do not hallucinate or invent page names.
7. Do not alter given values — only lowercase and rephrase actions concisely.

BEHAVIOR RULES:
- Never output free text, only JSON.
- Every non-verification BDD step becomes one JSON object.
- Verification/assertion steps are skipped completely.

REFERENCE EXAMPLES:
BDD: the user enters oneBankId
JSON: {"step": "enter oneBankId", "capture": true}

BDD: the user then clicks on login button on the login page
JSON: {"step": "click login button", "page": "loginPage", "capture": true}

BDD: And the portfolio manager clicks on the "Cancel" button on the modal
JSON: {"step": "click cancel button", "page": "OnlineCampaignManagementPage", "capture": true}

BDD: Then the modal should not be displayed on the Online Campaign Management Page
(No output – verification step)

Now, convert the following BDD scenario into JSON:
{bdd}
"""


5. "page" key inclusion rules:
   - If the page name is explicitly mentioned in the SAME line → include it.
   - If the step is a click action that explicitly **navigates to a page** → include the page name.
   - Otherwise → OMIT "page".



PAGE RULES:
- For normal input steps (typing, entering, selecting, etc.) → DO NOT include "page" unless explicitly mentioned in the same line.  
- For click actions:
   a. If the page name is mentioned in the same line → include it.  
   b. If the step is a click that navigates to a new page → check the next 3–4 steps for a page reference and assign that page name.  
   c. If no page is ever mentioned → omit "page".  

