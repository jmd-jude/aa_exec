import streamlit as st
import json
import os
import time
from openai import OpenAI
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="SIG Explorer",
    page_icon="🔗",
    layout="wide"
)

# Initialize session state
if "use_case_results" not in st.session_state:
    st.session_state.use_case_results = {}

# System instructions for the LLM
SYSTEM_INSTRUCTIONS = """You are an expert system designed to suggest valuable business use cases for identity graph data. 
Your core capability is analyzing identity graph schemas and suggesting actionable marketing and analytics opportunities.

For each user selection, generate specific, high-value use cases that:
1. Clearly explain the business objective
2. Identify required identity data elements
3. Outline implementation steps
4. Estimate expected outcomes

Focus particularly on use cases that:
- Connect online and offline customer journeys
- Enable personalization across channels
- Create valuable audience segments
- Improve marketing attribution
- Enhance customer acquisition strategies

Structure your response with clear section headers and subsections. Use bullet points for clarity where appropriate. 
Balance technical accuracy with business relevance and provide concrete examples rather than generic insights."""

# ----- SIDEBAR -----
with st.sidebar:
    st.title("SIG Explorer")
    st.subheader("Discover what you can do with SIG")
    
    # API configuration
    api_provider = st.selectbox("Select Platform", ["OpenAI", "Anthropic"])
    
    if api_provider == "OpenAI":
        model_options = ["gpt-4o", "gpt-4o-mini"]
        selected_model = st.selectbox("Select Model", model_options)
    else:
        model_display_names = ["claude 3-7 sonnet", "claude 3-5 sonnet"]
        model_api_mapping = {
            "claude 3-7 sonnet": "claude-3-7-sonnet-20250219",
            "claude 3-5 sonnet": "claude-3-5-sonnet"
        }
        selected_display_name = st.selectbox("Select Model", model_display_names)
        selected_model = model_api_mapping[selected_display_name]
    
    st.markdown("---")
    
    # Business objective selection
    st.markdown("### Business Objective")
    business_objective = st.selectbox(
        "What are you trying to achieve?",
        ["Customer Acquisition", "Conversion Optimization", "Customer Retention", "Cross-sell & Upsell", "Audience Creation"],
        help="Focuses the recommendations on specific goals, ensuring relevance to your current business priorities"
    )
    
    # Business Context (replaces Industry selection)
    st.markdown("### Business Context")
    industry_description = st.text_area(
        "Describe your business and specific goals",
        placeholder="Example: We're a regional bank focusing on small businesses. We want to identify customers likely to need additional financial products.",
        height=100,
        help="Allows you to describe your specific business situation, goals, and challenges, enabling highly personalized recommendations"
    )
    
    # Data availability checkboxes
    st.markdown("### Available Identity Data")
    has_email = st.checkbox(
        "Email Addresses", 
        value=True,
        help="Email addresses are powerful identifiers that connect online and offline data"
    )
    
    has_device_id = st.checkbox(
        "Device IDs", 
        value=True,
        help="Device IDs allow tracking and targeting across mobile devices and applications"
    )
    
    has_cookie = st.checkbox(
        "Cookie Data", 
        value=True,
        help="Cookies track web browsing behavior and site interactions"
    )
    
    has_maid = st.checkbox(
        "Mobile Advertising IDs", 
        value=True,
        help="MAIDs are resettable identifiers used for mobile app tracking and targeting"
    )
    
    has_phone = st.checkbox(
        "Phone Numbers", 
        value=True,
        help="Phone numbers connect SMS, call center, and other telecommunications channels"
    )
    
    has_physical_address = st.checkbox(
        "Physical Addresses", 
        value=False,
        help="Physical addresses link online behavior to direct mail and geographic data"
    )
    
    has_transaction_data = st.checkbox(
        "Transaction History", 
        value=False,
        help="Purchase data enables powerful segmentation and propensity modeling"
    )
    
    has_website_behavior = st.checkbox(
        "Website Behavior", 
        value=True,
        help="Web analytics data allows for interest-based targeting and personalization"
    )
    
    has_app_behavior = st.checkbox(
        "App Usage Data", 
        value=False,
        help="App engagement data provides insights into mobile user behavior and preferences"
    )
    
    has_demographics = st.checkbox(
        "Demographic Data", 
        value=False,
        help="Demographic information allows for audience segmentation by age, income, etc."
    )

# ----- MAIN AREA -----
st.title("Super Identity Graph (SIG) Use Case Explorer")

# Expandable section with detailed description
with st.expander("Click to Expand and Learn More About This Tool"):
    st.markdown("""
    ## SIG Use Case Explorer
    
    This app empowers marketers and data strategists to unlock the full value of their identity graph data through personalized, actionable use cases tailored to their specific business goals.
    
    ### Value Proposition
    The Identity Graph Explorer bridges the critical gap between raw identity data and business outcomes by instantly generating high-value marketing use cases that would otherwise require specialized expertise in identity resolution technology and marketing strategy. It transforms technical possibilities into tangible business opportunities.
    
    ### Loved By
    - **Marketing Technology Leaders** who have invested in identity graph technology but struggle to communicate its full potential to business stakeholders
    - **Sales and Customer Success Leaders** who need to quickly demonstrate value propositions for diverse clients
    
    ### Problems Solved
    1. **Technical-to-Business Translation**: Converts complex identity graph capabilities into clear, actionable marketing use cases that business users can understand and implement
    2. **Value Discovery**: Reveals specific, high-impact applications of identity data that might otherwise remain undiscovered
    """)

st.markdown("Upload your identity graph schema or use our example schema to get started.")

# Input methods
input_method = st.radio("Input Method", ["Upload JSON Schema", "Use Example Schema"])

schema_json = None

if input_method == "Upload JSON Schema":
    uploaded_file = st.file_uploader("Choose a schema file", type="json")
    if uploaded_file is not None:
        schema_json = json.loads(uploaded_file.read())
else:
    # Example identity graph schema
    schema_json = {
        "tables": {
            "CUSTOMER_IDENTITIES": {
                "description": "Core table linking all customer identifiers across platforms",
                "fields": {
                    "IDENTITY_ID": {"type": "TEXT", "nullable": False, "primary_key": True},
                    "CUSTOMER_ID": {"type": "TEXT", "nullable": True},
                    "EMAIL_HASH": {"type": "TEXT", "nullable": True},
                    "PHONE_HASH": {"type": "TEXT", "nullable": True},
                    "COOKIE_ID": {"type": "TEXT", "nullable": True},
                    "DEVICE_ID": {"type": "TEXT", "nullable": True},
                    "MOBILE_AD_ID": {"type": "TEXT", "nullable": True},
                    "PHYSICAL_ADDRESS_ID": {"type": "TEXT", "nullable": True},
                    "LOYALTY_ID": {"type": "TEXT", "nullable": True},
                    "FIRST_SEEN_DATE": {"type": "TIMESTAMP_NTZ", "nullable": True},
                    "LAST_UPDATED": {"type": "TIMESTAMP_NTZ", "nullable": True},
                    "IDENTITY_CONFIDENCE": {"type": "FLOAT", "nullable": True},
                    "IDENTITY_SOURCE": {"type": "TEXT", "nullable": True}
                }
            },
            "CUSTOMER_ATTRIBUTES": {
                "description": "Demographic and preference data for known customers",
                "fields": {
                    "CUSTOMER_ID": {"type": "TEXT", "nullable": False},
                    "AGE_RANGE": {"type": "TEXT", "nullable": True},
                    "GENDER": {"type": "TEXT", "nullable": True},
                    "INCOME_RANGE": {"type": "TEXT", "nullable": True},
                    "GEOGRAPHY": {"type": "TEXT", "nullable": True},
                    "LIFESTYLE_SEGMENTS": {"type": "VARIANT", "nullable": True},
                    "BEHAVIORAL_SEGMENTS": {"type": "VARIANT", "nullable": True},
                    "PURCHASE_PROPENSITY": {"type": "FLOAT", "nullable": True},
                    "PRIVACY_PREFERENCES": {"type": "VARIANT", "nullable": True},
                    "ATTRIBUTE_CONFIDENCE": {"type": "FLOAT", "nullable": True},
                    "LAST_UPDATED": {"type": "TIMESTAMP_NTZ", "nullable": True}
                }
            },
            "IDENTITY_EVENTS": {
                "description": "Record of identity resolution events and updates",
                "fields": {
                    "EVENT_ID": {"type": "TEXT", "nullable": False, "primary_key": True},
                    "IDENTITY_ID": {"type": "TEXT", "nullable": False},
                    "EVENT_TYPE": {"type": "TEXT", "nullable": False},
                    "EVENT_SOURCE": {"type": "TEXT", "nullable": True},
                    "EVENT_TIMESTAMP": {"type": "TIMESTAMP_NTZ", "nullable": False},
                    "PREVIOUS_STATE": {"type": "VARIANT", "nullable": True},
                    "CURRENT_STATE": {"type": "VARIANT", "nullable": True},
                    "CONFIDENCE_SCORE": {"type": "FLOAT", "nullable": True},
                    "PROCESSING_DETAILS": {"type": "VARIANT", "nullable": True}
                }
            },
            "DEVICE_PROFILE": {
                "description": "Information about devices used by customers",
                "fields": {
                    "DEVICE_ID": {"type": "TEXT", "nullable": False, "primary_key": True},
                    "DEVICE_TYPE": {"type": "TEXT", "nullable": True},
                    "OPERATING_SYSTEM": {"type": "TEXT", "nullable": True},
                    "BROWSER": {"type": "TEXT", "nullable": True},
                    "IP_ADDRESS_HASH": {"type": "TEXT", "nullable": True},
                    "USER_AGENT": {"type": "TEXT", "nullable": True},
                    "FIRST_SEEN_DATE": {"type": "TIMESTAMP_NTZ", "nullable": True},
                    "LAST_SEEN_DATE": {"type": "TIMESTAMP_NTZ", "nullable": True},
                    "GEO_DATA": {"type": "VARIANT", "nullable": True}
                }
            },
            "INTERACTION_HISTORY": {
                "description": "Customer interactions across all touchpoints",
                "fields": {
                    "INTERACTION_ID": {"type": "TEXT", "nullable": False, "primary_key": True},
                    "IDENTITY_ID": {"type": "TEXT", "nullable": False},
                    "INTERACTION_TYPE": {"type": "TEXT", "nullable": False},
                    "CHANNEL": {"type": "TEXT", "nullable": False},
                    "TIMESTAMP": {"type": "TIMESTAMP_NTZ", "nullable": False},
                    "SESSION_ID": {"type": "TEXT", "nullable": True},
                    "ACTION": {"type": "TEXT", "nullable": True},
                    "CONTENT_ID": {"type": "TEXT", "nullable": True},
                    "PRODUCT_ID": {"type": "TEXT", "nullable": True},
                    "CAMPAIGN_ID": {"type": "TEXT", "nullable": True},
                    "INTERACTION_DETAILS": {"type": "VARIANT", "nullable": True}
                }
            }
        }
    }
    
    st.markdown("### Example Identity Graph Schema")
    with st.expander("View Example Schema"):
        st.json(schema_json)

# Additional context fields
st.markdown("### Additional Context")
col1, col2 = st.columns(2)

with col1:
    customer_count = st.number_input(
        "Approximate number of customers", 
        min_value=1000, 
        value=1000000, 
        step=100000,
        help="Provides scale context, as strategies differ between small and large customer bases"
    )
    
    data_freshness = st.selectbox(
        "Data freshness", 
        ["Real-time", "Daily", "Weekly", "Monthly"],
        help="Establishes recency parameters, influencing real-time vs. batch processing recommendations"
    )

with col2:
    channels = st.multiselect(
        "Activation channels", 
        ["Email", "Social Media", "Display Ads", "Search", "Mobile Push", "Website", "Direct Mail", "In-store"],
        default=["Email", "Social Media", "Display Ads", "Website"],
        help="Defines where use cases can be activated, ensuring recommendations match existing channel capabilities"
    )
    
    privacy_requirement = st.selectbox(
        "Privacy requirements", 
        ["GDPR Compliant", "CCPA Compliant", "Both GDPR and CCPA", "Minimal requirements"],
        help="Sets compliance boundaries for recommendations, ensuring use cases respect relevant regulations"
    )

# Generate use cases
if schema_json and st.button("Generate Use Cases"):
    with st.spinner("Working on it..."):
        # Collect all the context
        available_identifiers = []
        if has_email: available_identifiers.append("Email Addresses")
        if has_device_id: available_identifiers.append("Device IDs")
        if has_cookie: available_identifiers.append("Cookie Data")
        if has_maid: available_identifiers.append("Mobile Advertising IDs")
        if has_phone: available_identifiers.append("Phone Numbers")
        if has_physical_address: available_identifiers.append("Physical Addresses")
        
        available_data = []
        if has_transaction_data: available_data.append("Transaction History")
        if has_website_behavior: available_data.append("Website Behavior")
        if has_app_behavior: available_data.append("App Usage Data")
        if has_demographics: available_data.append("Demographic Data")
        
        # Build our prompt
        use_case_prompt = f"""
        Generate high-value business use cases for an identity graph with the following context:
        
        SCHEMA:
        {json.dumps(schema_json, indent=2)}
        
        BUSINESS CONTEXT:
        - Business Description: {industry_description}
        - Primary Objective: {business_objective}
        - Customer Base Size: {customer_count:,}
        - Data Freshness: {data_freshness}
        - Marketing Channels: {', '.join(channels)}
        - Privacy Requirements: {privacy_requirement}
        
        AVAILABLE IDENTITY DATA:
        {', '.join(available_identifiers)}
        
        AVAILABLE BEHAVIORAL DATA:
        {', '.join(available_data)}
        
        Please provide 3-5 specific, high-value use cases that would help achieve the business objective.
        For each use case:
        1. Provide a descriptive title and clear explanation of the business goal
        2. List the specific identity graph data elements required
        3. Outline implementation steps in business-friendly language
        4. Estimate expected outcomes and business impact
        5. Include any relevant considerations or limitations
        
        Format the response in markdown for readability with clear sections.
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
                        {"role": "user", "content": use_case_prompt}
                    ],
                    temperature=0.2
                )
                
                result = response.choices[0].message.content
                
            else:
                # Anthropic API
                client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
                
                # Add retry logic for potential overloaded errors
                max_retries = 3
                retry_count = 0
                result = None
                
                while retry_count < max_retries and result is None:
                    try:
                        response = client.messages.create(
                            model=selected_model,
                            max_tokens=4000,
                            temperature=0.2,
                            messages=[{"role": "user", "content": use_case_prompt}],
                            system=SYSTEM_INSTRUCTIONS
                        )
                        
                        result = response.content[0].text
                    except Exception as e:
                        retry_count += 1
                        if "overloaded" in str(e).lower() and retry_count < max_retries:
                            st.warning(f"Service is busy. Retrying ({retry_count}/{max_retries})...")
                            time.sleep(2 * retry_count)  # Exponential backoff
                        else:
                            raise e
            
            # Store results in session state
            if result:
                st.session_state.use_case_results = {
                    "schema": schema_json,
                    "business_context": {
                        "business_description": industry_description,
                        "objective": business_objective,
                        "channels": channels,
                        "available_identifiers": available_identifiers,
                        "available_data": available_data
                    },
                    "generated_use_cases": result
                }
            else:
                st.error("Unable to generate use cases. Please try again or select a different model.")
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Display results
if "generated_use_cases" in st.session_state.use_case_results:
    st.markdown("## Identity Graph Use Cases")
    
    tab1, tab2 = st.tabs(["Business Use Cases", "Technical Details"])
    
    with tab1:
        st.markdown(st.session_state.use_case_results["generated_use_cases"])
    
    with tab2:
        st.subheader("Schema Used")
        st.json(st.session_state.use_case_results["schema"])
        
        st.subheader("Business Context")
        st.json(st.session_state.use_case_results["business_context"])
    
    # Export options
    st.download_button(
        label="Download Use Cases as Markdown",
        data=st.session_state.use_case_results["generated_use_cases"],
        file_name="identity_graph_use_cases.md",
        mime="text/markdown"
    )
    
    # Implementation considerations
    st.markdown("## Implementation Considerations")
    st.info("""
    **Next Steps:**
    1. Share these use cases with your technical team to confirm feasibility
    2. Prioritize based on business impact and technical complexity
    3. Create a roadmap for implementing the top use cases
    4. Establish metrics to measure success
    """)