import streamlit as st
import json
import os
from openai import OpenAI
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Schema Genie POC",
    page_icon="🧠",
    layout="wide"
)

# Initialize session state
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = {}

# System instructions for the LLM
SYSTEM_INSTRUCTIONS = """You are an expert system designed to extract strategic business value from database schemas. Your core capability is analyzing the structure, relationships, and metadata in database schemas to generate actionable insights for technical and non-technical stakeholders.

Analyze the schema across four key dimensions:

1. Analytical Boundaries: Determine what questions can and cannot be answered with the current data model.
2. Data Optimization Opportunities: Identify ways to extract more value from existing data without requiring new collection.
3. Strategic Data Expansion: Recommend high-value additions to the data model.
4. Business Logic Extraction: Surface the implicit organizational knowledge encoded in the schema.

Structure your response with clear section headers and subsections. Use bullet points for clarity where appropriate. Balance technical accuracy with business relevance and provide concrete examples rather than generic insights."""

# ----- SIDEBAR -----
with st.sidebar:
    st.title("Schema Genie")
    st.subheader("Extract strategic value from your data model")
    
    # API configuration
    api_provider = st.selectbox("API Provider", ["OpenAI", "Anthropic"])
    
    if api_provider == "OpenAI":
        model_options = ["gpt-4o", "gpt-4o-mini"]
        selected_model = st.selectbox("Select Model", model_options)
    else:
        # Display friendly names in the dropdown
        model_display_names = ["claude 3-7 sonnet", "claude 3-5 sonnet"]
        
        # Map display names to API model IDs
        model_api_mapping = {
            "claude 3-7 sonnet": "claude-3-7-sonnet-20250219",
            "claude 3-5 sonnet": "claude-3-5-sonnet"
        }
        
        # Show friendly names in UI
        selected_display_name = st.selectbox("Select Model", model_display_names)
        
        # Use the mapping to get the actual API model ID
        selected_model = model_api_mapping[selected_display_name]
    
    st.markdown("---")
    st.markdown("### Analysis Options (select at least one)")
    
    include_phylum_1 = st.checkbox("Analytical Boundaries", value=True, 
                                help="What questions can be answered with this data?")
    include_phylum_2 = st.checkbox("Optimization Opportunities", value=False,
                                help="How can we extract more value from existing data?")
    include_phylum_3 = st.checkbox("Strategic Expansion", value=False, 
                                help="What high-value data should we add?")
    include_phylum_4 = st.checkbox("Business Logic", value=False,
                                help="What business assumptions are encoded in this schema?")

# ----- MAIN AREA -----
st.title("Schema Genie POC")
st.markdown("""
Upload your database schema JSON or paste it directly to extract strategic insights.
""")

# Input methods
input_method = st.radio("Input Method", ["Upload JSON File", "Paste JSON"])

schema_json = None

if input_method == "Upload JSON File":
    uploaded_file = st.file_uploader("Choose a schema file", type="json")
    if uploaded_file is not None:
        schema_json = json.loads(uploaded_file.read())
else:
    json_text = st.text_area("Paste your schema JSON", height=200)
    if json_text:
        try:
            schema_json = json.loads(json_text)
        except json.JSONDecodeError:
            st.error("Invalid JSON. Please check the format.")

# Example schema selector
st.markdown("### Or use an example schema:")
example_option = st.selectbox(
    "Select an example schema",
    ["None", "Marketing/Influencer Database", "E-commerce Database", "Sports Analytics Database"]
)

# These would be replaced with your actual example schemas from the CSV
example_schemas = {
    "Marketing/Influencer Database": {
        "base_schema": {
            "tables": {
                "BRANDS": {
                    "fields": {
                        "BRAND_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "NAME": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "SECTOR": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "ANNUAL_BUDGET": {"type": "FLOAT", "nullable": True, "primary_key": False},
                        "CAMPAIGN_FREQUENCY": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "PREFERRED_CATEGORIES": {"type": "VARIANT", "nullable": True, "primary_key": False},
                        "PREFERRED_PLATFORMS": {"type": "VARIANT", "nullable": True, "primary_key": False},
                        "PRIMARY_OBJECTIVE": {"type": "TEXT", "nullable": True, "primary_key": False}
                    }
                },
                "CAMPAIGNS": {
                    "fields": {
                        "CAMPAIGN_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "BRAND_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "CAMPAIGN_NAME": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "OBJECTIVE": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "START_DATE": {"type": "TIMESTAMP_NTZ", "nullable": True, "primary_key": False},
                        "END_DATE": {"type": "TIMESTAMP_NTZ", "nullable": True, "primary_key": False},
                        "BUDGET": {"type": "FLOAT", "nullable": True, "primary_key": False}
                    }
                },
                "INFLUENCERS": {
                    "fields": {
                        "INFLUENCER_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "NAME": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "TIER": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "FOLLOWER_COUNT": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "ENGAGEMENT_RATE": {"type": "FLOAT", "nullable": True, "primary_key": False}
                    }
                }
            }
        }
    },
    "E-commerce Database": {
        "base_schema": {
            "tables": {
                "SHOP_ORDERS": {
                    "fields": {
                        "ORDER_ID": {"type": "TEXT", "nullable": False, "primary_key": False},
                        "CUSTOMER_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "ORDER_DATE": {"type": "TIMESTAMP_NTZ", "nullable": True, "primary_key": False},
                        "TOTAL_AMOUNT": {"type": "NUMBER", "nullable": True, "primary_key": False}
                    }
                },
                "SHOP_ORDER_ITEMS": {
                    "fields": {
                        "ORDER_ITEM_ID": {"type": "TEXT", "nullable": False, "primary_key": False},
                        "ORDER_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "PRODUCT_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "QUANTITY": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "PRICE": {"type": "NUMBER", "nullable": True, "primary_key": False}
                    }
                },
                "SHOP_PRODUCTS": {
                    "fields": {
                        "PRODUCT_ID": {"type": "TEXT", "nullable": False, "primary_key": False},
                        "NAME": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "CATEGORY": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "BASE_PRICE": {"type": "NUMBER", "nullable": True, "primary_key": False}
                    }
                }
            }
        }
    },
    "Sports Analytics Database": {
        "base_schema": {
            "tables": {
                "FANS": {
                    "fields": {
                        "FAN_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "FAN_SINCE": {"type": "TIMESTAMP_NTZ", "nullable": True, "primary_key": False},
                        "LOYALTY_TIER": {"type": "TEXT", "nullable": True, "primary_key": False}
                    }
                },
                "GAMES": {
                    "fields": {
                        "GAME_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "OPPONENT": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "GAME_DATE": {"type": "TIMESTAMP_NTZ", "nullable": True, "primary_key": False},
                        "ATTENDANCE": {"type": "NUMBER", "nullable": True, "primary_key": False}
                    }
                },
                "CONCESSION_SALES": {
                    "fields": {
                        "TRANSACTION_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "GAME_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "FAN_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "TOTAL_AMOUNT": {"type": "FLOAT", "nullable": True, "primary_key": False}
                    }
                }
            }
        }
    }
}

if example_option != "None":
    schema_json = example_schemas[example_option]

# Analysis execution
if schema_json and st.button("Run Analysis"):
    with st.spinner("Working on it..."):
        # Build our analysis prompt based on selected phylums
        analysis_prompt = f"""
        Analyze the following database schema JSON and extract strategic insights:
        
        {json.dumps(schema_json, indent=2)}
        
        Provide a comprehensive analysis focusing on the following areas:
        """
        
        if include_phylum_1:
            analysis_prompt += """
            1. ANALYTICAL BOUNDARIES: 
               - What specific questions can be answered with this data?
               - What are 5-10 specific, detailed analytical queries that would be valuable to a strategic decision maker?
               - For each query, explain what business value it would provide.
            """
        
        if include_phylum_2:
            analysis_prompt += """
            2. OPTIMIZATION OPPORTUNITIES:
               - What derived metrics, calculations, or views could add value?
               - Identify potential segmentations that aren't explicitly modeled but could be derived.
               - Suggest ways to better utilize existing data without new collection.
            """
        
        if include_phylum_3:
            analysis_prompt += """
            3. STRATEGIC EXPANSION:
               - What high-value data is missing that would enhance analytical capabilities?
               - Identify 3-5 specific additions to the schema that would create disproportionate value.
               - For each addition, explain the new insights it would enable.
            """
        
        if include_phylum_4:
            analysis_prompt += """
            4. BUSINESS LOGIC:
               - What business rules and relationships are encoded in this schema?
               - What organizational assumptions are revealed by the data model?
               - What potential blind spots exist in how the business conceptualizes its data?
            """
        
        analysis_prompt += """
        Format your response using markdown for readability. Include section headers and bullet points where appropriate.
        """
        
        try:
            # Call the appropriate API
            if api_provider == "OpenAI":
                client = OpenAI(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    base_url=None,
                    default_headers=None
                )
                response = client.chat.completions.create(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                        {"role": "user", "content": analysis_prompt}
                    ],
                    temperature=0.2
                )
                
                result = response.choices[0].message.content
                
                # Store results in session state
                if result:
                    st.session_state.analysis_results = {
                        "raw_schema": schema_json,
                        "analysis": result
                    }
                else:
                    st.error("Unable to generate analysis. Please try again or select a different model.")
            else:
                # Initialize Anthropic client
                client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
                
                # Function to call Anthropic API with error handling
                def call_anthropic_api(use_system_param=True):
                    try:
                        if use_system_param:
                            # With system parameter
                            response = client.messages.create(
                                model=selected_model,
                                max_tokens=4000,
                                temperature=0.2,
                                messages=[{"role": "user", "content": analysis_prompt}],
                                system=SYSTEM_INSTRUCTIONS
                            )
                        else:
                            # Without system parameter
                            response = client.messages.create(
                                model=selected_model,
                                max_tokens=4000,
                                temperature=0.2,
                                messages=[{
                                    "role": "user", 
                                    "content": f"System instructions: {SYSTEM_INSTRUCTIONS}\n\n{analysis_prompt}"
                                }]
                            )
                        return response.content[0].text
                    except Exception as e:
                        error_type = "Initial" if use_system_param else "Fallback"
                        st.error(f"{error_type} Anthropic API error: {str(e)}")
                        return None
                
                # First try with system parameter
                result = call_anthropic_api(use_system_param=True)
                
                # If first attempt failed, try without system prompt
                if result is None:
                    result = call_anthropic_api(use_system_param=False)
                    if result is None:
                        st.error("Failed to call Anthropic API after multiple attempts")
                
                # Check if we have a valid result
                if result is None:
                    st.error("Unable to generate analysis. Please try again or select a different model.")
                else:
                    # Store results
                    st.session_state.analysis_results = {
                        "raw_schema": schema_json,
                        "analysis": result
                    }
            
        except Exception as e:
            st.error(f"An error occurred during analysis: {str(e)}")

# Display results
if "analysis" in st.session_state.analysis_results:
    st.markdown("## Schema Genie Analysis")
    
    tab1, tab2 = st.tabs(["Analysis", "Raw Schema"])
    
    with tab1:
        st.markdown(st.session_state.analysis_results["analysis"])
    
    with tab2:
        st.json(st.session_state.analysis_results["raw_schema"])
    
    # Export options
    st.download_button(
        label="Download Analysis as Markdown",
        data=st.session_state.analysis_results["analysis"],
        file_name="schema_intelligence_analysis.md",
        mime="text/markdown"
    )
