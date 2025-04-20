import streamlit as st
import json
from datetime import datetime
import openai
from anthropic import Anthropic
import re

# Set page configuration
st.set_page_config(
    page_title="SIG Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #4F46E5;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 4rem;
        white-space: pre-wrap;
    }
    .stTabs [aria-selected="true"] {
        background-color: #F0F4FF;
        border-radius: 4px;
    }
    /* Add more custom styling as needed */
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'generated_report' not in st.session_state:
    st.session_state.generated_report = None
if 'parsed_use_cases' not in st.session_state:
    st.session_state.parsed_use_cases = []
if 'all_input_data' not in st.session_state:
    st.session_state.all_input_data = {}
if 'schema' not in st.session_state:
    st.session_state.schema = None
if 'provider' not in st.session_state:
    st.session_state.provider = "OpenAI"

# Title
st.title("Super Identity Graph Explorer")
st.subheader("Generate Actionable Business Use Cases from Identity Data")

# Main content
def main():
    # Create tabs
    tab1, tab2 = st.tabs(["Generate Use Cases", "Explore Use Cases"])
    
    with tab1:
        input_section()
        
    with tab2:
        if st.session_state.generated_report:
            explore_use_cases()
        else:
            st.info("Generate use cases first to explore them in detail!")

def input_section():
    # Initialize API provider selection outside the form
    api_col1, api_col2 = st.columns(2)
    
    with api_col1:
        # Provider selection that updates session state immediately
        provider = st.radio(
            "Choose API Provider",
            ["OpenAI", "Anthropic"],
            key="provider_radio",
            horizontal=True,
            on_change=lambda: setattr(st.session_state, 'provider', st.session_state.provider_radio)
        )
    
    with api_col2:
        # Use the session state provider value to determine which models to show
        if st.session_state.provider == "OpenAI":
            model_options = ["gpt-4o", "gpt-4o-mini"]
            model_index = 0 if "openai_model_index" not in st.session_state else st.session_state.openai_model_index
            model_selection = st.radio(
                "Select OpenAI Model",
                model_options,
                index=model_index,
                key="openai_model_radio",
                horizontal=True,
                on_change=lambda: setattr(st.session_state, 'openai_model_index', model_options.index(st.session_state.openai_model_radio))
            )
            model = model_selection
        else:
            # Different models for Anthropic
            anthropic_models = {
                "claude 3-7 sonnet": "claude-3-7-sonnet-20250219", 
                "claude 3-5 sonnet": "claude-3-5-sonnet"
            }
            model_names = list(anthropic_models.keys())
            model_index = 0 if "anthropic_model_index" not in st.session_state else st.session_state.anthropic_model_index
            selected_name = st.radio(
                "Select Anthropic Model",
                model_names,
                index=model_index,
                key="anthropic_model_radio",
                horizontal=True,
                on_change=lambda: setattr(st.session_state, 'anthropic_model_index', model_names.index(st.session_state.anthropic_model_radio))
            )
            model = anthropic_models[selected_name]

    # Now start the form for the rest of the inputs
    with st.form("use_case_generator"):
        col1, col2 = st.columns(2)
        
        # Left column content
        with col1:
            st.markdown("### AI Configuration")
            
            prompt_quality = st.radio(
                "Prompt Quality",
                ["Standard", "Enhanced"],
                help="Standard: Basic output with general use cases. Enhanced: Detailed implementation guidance with complexity assessments and prioritization."
            )
            
            # Business Context Section
            st.markdown("### Business Objectives")
            
            business_objective = st.selectbox(
                "Primary Business Objective",
                [
                    "Customer Acquisition",
                    "Conversion Optimization",
                    "Customer Retention",
                    "Cross-sell & Upsell",
                    "Audience Creation"
                ],
                help="Select your main business goal for using the identity graph"
            )
            
            business_context = st.text_area(
                "Additional Business Context (Optional)",
                placeholder="Describe your business, target audience, and specific challenges or goals...",
                help="Providing more context helps generate more relevant use cases"
            )
            
            # Available Identity Data Section
            st.markdown("### Available Identity Data")
            
            id_col1, id_col2 = st.columns(2)
            
            with id_col1:
                st.markdown("#### Identity Types")
                has_email = st.checkbox("Email", value=True, key="identity_email")
                has_device_id = st.checkbox("Device IDs", value=True, key="identity_device_id")
                has_cookies = st.checkbox("Cookies", value=True, key="identity_cookies")
                has_maids = st.checkbox("Mobile Ad IDs (MAIDs)", value=True, key="identity_maids")
                has_phone = st.checkbox("Phone Numbers", value=True, key="identity_phone")
                has_address = st.checkbox("Physical Addresses", value=True, key="identity_address")
            
            with id_col2:
                st.markdown("#### Behavioral Data")
                has_transactions = st.checkbox("Transaction History", value=True, key="identity_transactions")
                has_website_behavior = st.checkbox("Website Behavior", value=True, key="identity_website")
                has_app_usage = st.checkbox("App Usage", value=True, key="identity_app_usage")
                has_demographics = st.checkbox("Demographics", value=True, key="identity_demographics")
        
        # Additional Context Section - Right Column
        with col2:
            st.markdown("### Additional Context")
            
            customer_base_size = st.selectbox(
                "Customer Base Size",
                ["Less than 10K", "10K-100K", "100K-1M", "1M-10M", "More than 10M"],
                help="Approximate number of customers in your database"
            )
            
            data_freshness = st.selectbox(
                "Data Freshness",
                ["Real-time", "Daily", "Weekly", "Monthly", "Quarterly"],
                help="How frequently your identity data is updated"
            )
            
            st.markdown("#### Activation Channels")
            
            channel_col1, channel_col2 = st.columns(2)
            
            with channel_col1:
                channel_email = st.checkbox("Email", value=True, key="channel_email")
                channel_sms = st.checkbox("SMS/Text", key="channel_sms")
                channel_push = st.checkbox("Push Notifications", key="channel_push")
                channel_social = st.checkbox("Social Media", key="channel_social")
            
            with channel_col2:
                channel_display = st.checkbox("Display Ads", key="channel_display")
                channel_search = st.checkbox("Search", key="channel_search")
                channel_direct_mail = st.checkbox("Direct Mail", key="channel_direct_mail")
                channel_call_center = st.checkbox("Call Center", key="channel_call_center")
            
            privacy_requirements = st.multiselect(
                "Privacy Requirements",
                ["GDPR", "CCPA/CPRA", "HIPAA", "GLBA", "Internal Policies"],
                default=["GDPR", "CCPA/CPRA"],
                help="Regulatory constraints to consider"
            )
            
            # Input Schema Section
            st.markdown("### Input Schema")
            
            schema_option = st.radio(
                "Schema Source",
                ["Upload JSON Schema", "Use Example Schema"],
                help="Provide your custom identity graph structure or use our pre-built example"
            )
            
            if schema_option == "Upload JSON Schema":
                uploaded_file = st.file_uploader("Upload JSON Schema", type="json")
                if uploaded_file:
                    try:
                        schema_json = json.load(uploaded_file)
                        st.success(f"Successfully loaded schema with {len(schema_json)} attributes")
                    except Exception as e:
                        st.error(f"Error loading JSON: {e}")
                        schema_json = None
                else:
                    schema_json = None
            else:
                try:
                    with open('sig_schema.json', 'r') as f:
                        schema_json = json.load(f)
                    st.success(f"Using example schema with {len(schema_json)} attributes")
                except Exception as e:
                    st.error(f"Error loading example schema: {e}")
                    st.info("Make sure the example schema file 'sig_schema.json' is in the same directory as this app")
                    schema_json = None
        
        # Store all input data in session state when form is submitted
        submit_button = st.form_submit_button("Generate Use Cases")
        
        if submit_button and schema_json:
            # Collect all inputs into a structured format
            st.session_state.all_input_data = {
                "provider": st.session_state.provider,
                "model": model,
                "prompt_quality": prompt_quality,
                "business_objective": business_objective,
                "business_context": business_context,
                "identity_data": {
                    "email": has_email,
                    "device_id": has_device_id,
                    "cookies": has_cookies,
                    "maids": has_maids,
                    "phone": has_phone,
                    "address": has_address,
                    "transactions": has_transactions,
                    "website_behavior": has_website_behavior,
                    "app_usage": has_app_usage,
                    "demographics": has_demographics
                },
                "customer_base_size": customer_base_size,
                "data_freshness": data_freshness,
                "activation_channels": {
                    "email": channel_email,
                    "sms": channel_sms,
                    "push": channel_push,
                    "social": channel_social,
                    "display": channel_display,
                    "search": channel_search,
                    "direct_mail": channel_direct_mail,
                    "call_center": channel_call_center
                },
                "privacy_requirements": privacy_requirements,
                "schema_option": schema_option
            }
            
            # Store schema in session state
            st.session_state.schema = schema_json
            
            # Generate the use cases
            with st.spinner("Generating use cases... This may take 30-60 seconds depending on the selected model."):
                report = generate_use_cases(
                    st.session_state.provider, 
                    model,
                    prompt_quality,
                    business_objective,
                    business_context,
                    st.session_state.all_input_data["identity_data"],
                    st.session_state.all_input_data["activation_channels"],
                    customer_base_size,
                    data_freshness,
                    privacy_requirements,
                    schema_json
                )
                
                if report:
                    st.session_state.generated_report = report
                    # Parse the report into discrete use cases
                    st.session_state.parsed_use_cases = parse_use_cases(report)
                    st.success("Use cases generated successfully! Switch to the 'Explore Use Cases' tab to view the results.")
        elif submit_button:
            st.error("Please ensure a schema is loaded before generating use cases.")

def parse_use_cases(report):
    """
    Parse the generated report into discrete use cases.
    """
    # Simple regex-based parsing for prototype
    # This will need refinement based on the actual output format
    use_case_pattern = r"## Use Case (\d+): ([^\n]+)\n(.*?)(?=## Use Case \d+:|$)"
    
    use_cases = []
    matches = re.finditer(use_case_pattern, report, re.DOTALL)
    
    for match in matches:
        number = match.group(1)
        title = match.group(2).strip()
        content = match.group(3).strip()
        
        # Extract sections within the use case (optional, can be expanded)
        objective_match = re.search(r"### Objective\n(.*?)(?=###|$)", content, re.DOTALL)
        objective = objective_match.group(1).strip() if objective_match else ""
        
        implementation_match = re.search(r"### Implementation Approach\n(.*?)(?=###|$)", content, re.DOTALL)
        implementation = implementation_match.group(1).strip() if implementation_match else ""
        
        impact_match = re.search(r"### Expected Business Impact\n(.*?)(?=###|$)", content, re.DOTALL)
        impact = impact_match.group(1).strip() if impact_match else ""
        
        complexity_match = re.search(r"### Technical Complexity\n(.*?)(?=###|$)", content, re.DOTALL)
        complexity = complexity_match.group(1).strip() if complexity_match else ""
        
        use_cases.append({
            "number": number,
            "title": title,
            "objective": objective,
            "implementation": implementation,
            "impact": impact,
            "complexity": complexity,
            "full_content": content
        })
    
    return use_cases

def explore_use_cases():
    """
    Display the generated use cases and allow deeper exploration.
    """
    # Tabs for Report and Use Case Explorer
    report_tab, explorer_tab = st.tabs(["Full Report", "Use Case Explorer"])
    
    with report_tab:
        st.markdown("### Generated Use Cases Report")
        
        # Display the full report
        st.markdown(st.session_state.generated_report)
        
        # Download button for the report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="Download Report as Markdown",
            data=st.session_state.generated_report,
            file_name=f"sig_use_cases_{timestamp}.md",
            mime="text/markdown"
        )
    
    with explorer_tab:
        st.markdown("### Use Case Deep Dive")
        st.write("Select a use case to explore in more detail:")
        
        # Display use case selection
        if st.session_state.parsed_use_cases:
            use_case_titles = [f"Use Case {uc['number']}: {uc['title']}" for uc in st.session_state.parsed_use_cases]
            selected_case_index = st.selectbox("Choose a use case to explore:", range(len(use_case_titles)), format_func=lambda i: use_case_titles[i])
            
            if selected_case_index is not None:
                selected_case = st.session_state.parsed_use_cases[selected_case_index]
                
                # Display the selected use case
                st.markdown(f"## {use_case_titles[selected_case_index]}")
                
                # Expandable sections for the use case details
                with st.expander("Objective", expanded=True):
                    st.markdown(selected_case["objective"])
                
                with st.expander("Implementation Approach", expanded=True):
                    st.markdown(selected_case["implementation"])
                
                with st.expander("Expected Business Impact", expanded=True):
                    st.markdown(selected_case["impact"])
                
                with st.expander("Technical Complexity", expanded=True):
                    st.markdown(selected_case["complexity"])
                
                # Guided Q&A Section
                st.markdown("### Ask Follow-up Questions")
                st.write("Select a question to get more specific details about this use case:")
                
                common_questions = [
                    "What are the technical prerequisites for implementing this use case?",
                    "How would this integrate with my marketing automation platform?",
                    "What KPIs should I track for this use case?",
                    "What's a typical timeline for implementation?",
                    "What are potential challenges or risks with this approach?",
                    "How does this compare to similar use cases?"
                ]
                
                selected_question = st.selectbox("Choose a question:", common_questions)
                
                if st.button("Get Answer", key="get_answer_button"):
                    with st.spinner("Generating detailed answer..."):
                        answer = generate_follow_up_answer(
                            st.session_state.all_input_data["provider"],
                            st.session_state.all_input_data["model"],
                            selected_question,
                            selected_case,
                            st.session_state.schema,
                            st.session_state.all_input_data
                        )
                        st.markdown("### Answer")
                        st.markdown(answer)
                        
                # Custom question option
                st.markdown("### Ask Your Own Question")
                custom_question = st.text_input("Type your question about this use case:")
                
                if custom_question and st.button("Submit Question", key="submit_question_button"):
                    with st.spinner("Generating answer to your question..."):
                        answer = generate_follow_up_answer(
                            st.session_state.all_input_data["provider"],
                            st.session_state.all_input_data["model"],
                            custom_question,
                            selected_case,
                            st.session_state.schema,
                            st.session_state.all_input_data
                        )
                        st.markdown("### Answer")
                        st.markdown(answer)
        else:
            st.info("No use cases have been parsed from the report. Please regenerate the report.")

def generate_use_cases(provider, model, prompt_quality, business_objective, business_context, identity_data, 
                       activation_channels, customer_base_size, data_freshness, privacy_requirements, schema_json):
    """
    Generate use cases based on the provided inputs.
    """
    # Format the available identity data for the prompt
    available_identity = [k for k, v in identity_data.items() if v]
    available_channels = [k for k, v in activation_channels.items() if v]
    
    # Count number of attributes by table
    table_counts = {}
    for item in schema_json:
        table = item.get("\ufeffTable", "") or item.get("Table", "")
        if table:
            table_counts[table] = table_counts.get(table, 0) + 1
    
    # Create a summary of the schema
    schema_summary = "Schema Summary:\n"
    for table, count in table_counts.items():
        schema_summary += f"- {table}: {count} attributes\n"
    
    # Sample some attributes from each table (up to 5 per table)
    schema_samples = "Sample Attributes:\n"
    samples_per_table = {}
    
    for item in schema_json:
        table = item.get("\ufeffTable", "") or item.get("Table", "")
        if table:
            if table not in samples_per_table:
                samples_per_table[table] = []
            
            if len(samples_per_table[table]) < 5:  # Limit to 5 samples per table
                attr_name = item.get("Attribute Name", "")
                attr_desc = item.get("Attribute Description", "")
                if attr_name and attr_desc:
                    samples_per_table[table].append(f"  - {attr_name}: {attr_desc}")
    
    for table, samples in samples_per_table.items():
        schema_samples += f"- {table}:\n"
        schema_samples += "\n".join(samples) + "\n"
    
    # Select the appropriate prompt template based on quality
    if prompt_quality == "Enhanced":
        prompt_template = f"""
You are a strategic identity data consultant helping a business leverage their Super Identity Graph (SIG) for marketing and customer experience use cases. Based on the provided business context and identity data schema, generate specific, actionable business use cases.

Business Objective: {business_objective}
Business Context: {business_context}

Available Identity Data: {', '.join(available_identity)}
Activation Channels: {', '.join(available_channels)}
Customer Base Size: {customer_base_size}
Data Freshness: {data_freshness}
Privacy Requirements: {', '.join(privacy_requirements)}

{schema_summary}

{schema_samples}

Create 5 specific, high-value business use cases that leverage the identity graph data. For each use case:

1. Give it a clear, specific title that communicates the business value
2. Structure each use case with the following sections:

## Use Case X: [Title]

### Objective
[Clear explanation of the business goal]

### Required Identity Graph Data
[Specific data elements needed from the schema, referencing actual attribute names where possible]

### Implementation Approach
[Step-by-step implementation instructions with 5-7 concrete steps]

### Expected Business Impact
[Quantified outcomes with specific metrics and timeframes]

### Technical Complexity
[Assessment of implementation difficulty (Low/Medium/High), key dependencies, and privacy considerations]

After presenting all use cases, add a "Quick Wins" section that identifies which 1-2 use cases offer the best combination of business value and implementation simplicity.

Format your response in Markdown.
"""
    else:
        # Standard prompt template (less detailed)
        prompt_template = f"""
Based on the following business context and identity data schema, suggest business use cases for a Super Identity Graph (SIG).

Business Objective: {business_objective}
Business Context: {business_context}

Available Identity Data: {', '.join(available_identity)}
Activation Channels: {', '.join(available_channels)}
Customer Base Size: {customer_base_size}
Data Freshness: {data_freshness}
Privacy Requirements: {', '.join(privacy_requirements)}

{schema_summary}

{schema_samples}

Create 3-5 business use cases that leverage the identity graph data, explaining the objective, approach, and expected outcomes for each.

Format your response in Markdown.
"""

    # Call the appropriate API based on provider selection
    if provider == "OpenAI":
        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a strategic identity data consultant with expertise in helping businesses leverage identity graph data for marketing and customer experience use cases."},
                    {"role": "user", "content": prompt_template}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            st.error(f"Error calling OpenAI API: {e}")
            return None
    else:  # Anthropic
        try:
            client = Anthropic()
            response = client.messages.create(
                model=model,
                max_tokens=4000,
                temperature=0.7,
                system="You are a strategic identity data consultant with expertise in helping businesses leverage identity graph data for marketing and customer experience use cases.",
                messages=[
                    {"role": "user", "content": prompt_template}
                ]
            )
            return response.content[0].text
        except Exception as e:
            st.error(f"Error calling Anthropic API: {e}")
            return None

def generate_follow_up_answer(provider, model, question, use_case, schema_json, context_data):
    """
    Generate a detailed answer to a follow-up question about a specific use case.
    """
    # Create a prompt for the follow-up question
    prompt = f"""
I need a detailed answer to a follow-up question about a specific identity graph use case. Here's the context:

QUESTION: {question}

USE CASE INFORMATION:
Title: Use Case {use_case['number']}: {use_case['title']}

Objective:
{use_case['objective']}

Implementation Approach:
{use_case['implementation']}

Expected Business Impact:
{use_case['impact']}

Technical Complexity:
{use_case['complexity']}

BUSINESS CONTEXT:
Primary Business Objective: {context_data['business_objective']}
Additional Context: {context_data['business_context']}
Customer Base Size: {context_data['customer_base_size']}
Data Freshness: {context_data['data_freshness']}
Privacy Requirements: {', '.join(context_data['privacy_requirements'])}

AVAILABLE IDENTITY DATA:
{', '.join([k for k, v in context_data['identity_data'].items() if v])}

ACTIVATION CHANNELS:
{', '.join([k for k, v in context_data['activation_channels'].items() if v])}

Please provide a comprehensive, detailed answer to the question that is specific to this use case and business context. Include practical examples, implementation details, and actionable advice where appropriate.
"""

    # Call the appropriate API based on provider selection
    if provider == "OpenAI":
        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a strategic identity data consultant with expertise in helping businesses leverage identity graph data for marketing and customer experience use cases."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            st.error(f"Error calling OpenAI API: {e}")
            return "I encountered an error generating your answer. Please try again."
    else:  # Anthropic
        try:
            client = Anthropic()
            response = client.messages.create(
                model=model,
                max_tokens=2000,
                temperature=0.7,
                system="You are a strategic identity data consultant with expertise in helping businesses leverage identity graph data for marketing and customer experience use cases.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            st.error(f"Error calling Anthropic API: {e}")
            return "I encountered an error generating your answer. Please try again."

if __name__ == "__main__":
    main()