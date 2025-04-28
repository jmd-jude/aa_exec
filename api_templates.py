import streamlit as st
import json
from datetime import datetime
from anthropic import Anthropic
import re

# Set page configuration
st.set_page_config(
    page_title="SIG Explorer & Template Builder",
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
    .template-card {
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        background-color: #F8FAFC;
    }
    .template-card:hover {
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .template-title {
        font-weight: bold;
        color: #4F46E5;
    }
    .field-tag {
        display: inline-block;
        background-color: #E2E8F0;
        border-radius: 4px;
        padding: 0.25rem 0.5rem;
        margin: 0.25rem;
        font-size: 0.8rem;
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
if 'suggested_templates' not in st.session_state:
    st.session_state.suggested_templates = []
if 'selected_template' not in st.session_state:
    st.session_state.selected_template = None

# Constants
ANTHROPIC_MODEL = "claude-3-7-sonnet-20250219"

# Title
st.title("Super Identity Graph Explorer & Template Builder")
st.subheader("Explore Data and Build API Templates with AI")

# Main content
def main():
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Data Exploration", "Use Case Generator", "Template Builder"])
    
    with tab1:
        data_exploration_tab()
        
    with tab2:
        use_case_generator_tab()
            
    with tab3:
        template_builder_tab()

def data_exploration_tab():
    """
    Tab for exploring the Identity Graph Schema and asking questions
    """
    st.markdown("### Explore Your Identity Graph Schema")
    st.write("Ask questions about your identity data to understand capabilities and opportunities.")
    
    # Schema upload area
    col1, col2 = st.columns([1, 2])
    
    with col1:
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
                    st.session_state.schema = schema_json
                    st.success(f"Successfully loaded schema with {len(schema_json)} attributes")
                except Exception as e:
                    st.error(f"Error loading JSON: {e}")
        else:
            try:
                with open('sig_schema.json', 'r') as f:
                    schema_json = json.load(f)
                st.session_state.schema = schema_json
                st.success(f"Using example schema with {len(schema_json)} attributes")
            except Exception as e:
                st.error(f"Error loading example schema: {e}")
                st.info("Make sure the example schema file 'sig_schema.json' is in the same directory as this app")
    
    with col2:
        if st.session_state.schema:
            # Show schema statistics
            tables = set()
            for item in st.session_state.schema:
                table_name = item.get("\ufeffTable", "") or item.get("Table", "")
                if table_name:
                    tables.add(table_name)
            
            st.markdown("#### Schema Overview")
            st.write(f"Your schema contains {len(st.session_state.schema)} attributes across {len(tables)} tables.")
            
            # Display table names
            st.markdown("#### Tables")
            for table in tables:
                st.write(f"- {table}")
    
    # Question answering section
    st.markdown("### Ask Questions About Your Data")
    
    if st.session_state.schema:
        user_question = st.text_input("Ask a question about your identity graph:", 
                                     placeholder="E.g., What customer attributes do we have? How could we segment users by engagement level?")
        
        if user_question and st.button("Get Answer"):
            with st.spinner("Analyzing your question..."):
                answer = generate_schema_answer(user_question, st.session_state.schema)
                
                st.markdown("### Answer")
                st.markdown(answer)
                
                # Add a "Create Template from This" button
                if st.button("Suggest Templates Based on This Insight"):
                    with st.spinner("Generating template suggestions..."):
                        suggested_templates = generate_template_suggestions(user_question, answer, st.session_state.schema)
                        st.session_state.suggested_templates = suggested_templates
                        
                        st.success("Template suggestions generated! View them in the Template Builder tab.")
                        
    else:
        st.info("Please load a schema first to ask questions about your data.")

def use_case_generator_tab():
    """
    Tab for generating business use cases based on the Identity Graph
    """
    st.markdown("### Generate Actionable Business Use Cases")
    
    if not st.session_state.schema:
        st.info("Please load a schema in the Data Exploration tab first.")
        return
    
    # Business context inputs
    with st.form("use_case_generator"):
        col1, col2 = st.columns(2)
        
        # Left column content
        with col1:
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
        
        # Store all input data in session state when form is submitted
        submit_button = st.form_submit_button("Generate Use Cases")
        
    # Process form submission outside the form context
    if submit_button and st.session_state.schema:
        # Collect all inputs into a structured format
        st.session_state.all_input_data = {
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
        }
        
        # Generate the use cases
        with st.spinner("Generating use cases... This may take 30-60 seconds."):
            report = generate_use_cases(
                business_objective,
                business_context,
                st.session_state.all_input_data["identity_data"],
                st.session_state.all_input_data["activation_channels"],
                customer_base_size,
                data_freshness,
                privacy_requirements,
                st.session_state.schema
            )
            
            if report:
                st.session_state.generated_report = report
                # Parse the report into discrete use cases
                st.session_state.parsed_use_cases = parse_use_cases(report)
                
                # Show the report
                st.markdown("### Generated Use Cases")
                st.markdown(report)
                
                # Add a button to generate template suggestions from use cases
                if st.button("Generate API Templates from These Use Cases"):
                    with st.spinner("Creating API template suggestions..."):
                        templates = generate_templates_from_use_cases(
                            st.session_state.parsed_use_cases, 
                            st.session_state.schema
                        )
                        st.session_state.suggested_templates = templates
                        st.success("API templates created! View them in the Template Builder tab.")

def template_builder_tab():
    """
    Tab for building and managing API templates
    """
    st.markdown("### API Template Builder")
    
    if not st.session_state.schema:
        st.info("Please load a schema in the Data Exploration tab first.")
        return
    
    # Check if we have suggested templates
    if not st.session_state.suggested_templates:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write("No templates have been suggested yet. You can:")
            st.write("- Explore your data in the Data Exploration tab and click 'Suggest Templates'")
            st.write("- Generate use cases and click 'Generate API Templates from These Use Cases'")
            st.write("- Manually create a template below")
        
        with col2:
            if st.button("Generate Templates Now"):
                with st.spinner("Analyzing schema and generating template suggestions..."):
                    templates = generate_template_suggestions_direct(st.session_state.schema)
                    st.session_state.suggested_templates = templates
    
    # Display suggested templates
    if st.session_state.suggested_templates:
        st.markdown("### Suggested API Templates")
        st.write("These templates are automatically suggested based on your data schema and business needs.")
        
        # Create tabs for browsing and editing templates
        template_tabs = st.tabs(["Browse Templates", "Edit Template", "Create Custom Template"])
        
        with template_tabs[0]:
            browse_templates(st.session_state.suggested_templates)
            
        with template_tabs[1]:
            edit_template(st.session_state.suggested_templates)
            
        with template_tabs[2]:
            create_custom_template(st.session_state.schema)

def browse_templates(templates):
    """
    Display and browse suggested templates
    """
    # Filter options
    st.markdown("#### Filter Templates")
    filter_col1, filter_col2 = st.columns([2, 3])
    
    with filter_col1:
        filter_purpose = st.selectbox(
            "Filter by Purpose",
            ["All"] + list(set(t['purpose'] for t in templates)),
            index=0
        )
    
    with filter_col2:
        # Create a list of all tables used across templates
        all_tables = set()
        for template in templates:
            for field in template['fields']:
                table = field.get('table', '')
                if table:
                    all_tables.add(table)
        
        filter_table = st.selectbox(
            "Filter by Table",
            ["All"] + list(all_tables),
            index=0
        )
    
    # Apply filters
    filtered_templates = templates
    if filter_purpose != "All":
        filtered_templates = [t for t in filtered_templates if t['purpose'] == filter_purpose]
    if filter_table != "All":
        filtered_templates = [t for t in filtered_templates if any(f['table'] == filter_table for f in t['fields'])]
    
    st.markdown(f"#### Templates ({len(filtered_templates)} results)")
    
    # Display templates
    for i, template in enumerate(filtered_templates):
        with st.container():
            st.markdown(f"""
            <div class="template-card">
                <div class="template-title">{template['name']}</div>
                <p>{template['description']}</p>
                <p><strong>Purpose:</strong> {template['purpose']}</p>
                <p><strong>Fields:</strong> {len(template['fields'])}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Create a collapsible section for viewing template details
            with st.expander("View Template Details"):
                st.markdown(f"**Template Name:** {template['name']}")
                st.markdown(f"**Description:** {template['description']}")
                st.markdown(f"**Purpose:** {template['purpose']}")
                
                st.markdown("**Fields:**")
                for field in template['fields']:
                    st.markdown(f"- **{field['table']}.{field['name']}** - {field['description']}")
                
                # Button to select this template for editing
                if st.button("Edit This Template", key=f"edit_btn_{i}"):
                    st.session_state.selected_template = i
                    st.rerun()
                    
                # Button to create API template
                if st.button("Create API Template", key=f"create_btn_{i}"):
                    # Generate JSON for this template
                    template_json = {
                        "template_name": template['name'],
                        "description": template['description'],
                        "fields": [{"table": f['table'], "field": f['name']} for f in template['fields']]
                    }
                    
                    # Create a downloadable JSON file
                    template_json_str = json.dumps(template_json, indent=2)
                    st.download_button(
                        label="Download Template JSON",
                        data=template_json_str,
                        file_name=f"{template['name'].lower().replace(' ', '_')}_template.json",
                        mime="application/json"
                    )
                    
                    st.success("Template created! You can now download the JSON configuration.")

def edit_template(templates):
    """
    Edit a selected template
    """
    if len(templates) == 0:
        st.info("No templates available to edit. Generate templates first.")
        return
    
    # Template selection
    if st.session_state.selected_template is None:
        template_names = [t['name'] for t in templates]
        selected_index = st.selectbox("Select Template to Edit", range(len(template_names)), format_func=lambda i: template_names[i])
        st.session_state.selected_template = selected_index
    
    if st.session_state.selected_template is not None:
        # Get the selected template
        template = templates[st.session_state.selected_template]
        
        # Create a form for editing
        with st.form("edit_template_form"):
            # Basic template info
            new_name = st.text_input("Template Name", value=template['name'])
            new_description = st.text_area("Description", value=template['description'])
            new_purpose = st.selectbox(
                "Purpose",
                ["Customer Acquisition", "Conversion Optimization", "Customer Retention", "Cross-sell & Upsell", "Audience Creation", "Other"],
                index=["Customer Acquisition", "Conversion Optimization", "Customer Retention", "Cross-sell & Upsell", "Audience Creation", "Other"].index(template['purpose']) if template['purpose'] in ["Customer Acquisition", "Conversion Optimization", "Customer Retention", "Cross-sell & Upsell", "Audience Creation", "Other"] else 0
            )
            
            # Field management
            st.markdown("#### Template Fields")
            
            # Group fields by table for easier management
            fields_by_table = {}
            for field in template['fields']:
                table = field.get('table', 'Other')
                if table not in fields_by_table:
                    fields_by_table[table] = []
                fields_by_table[table].append(field)
            
            # Display fields grouped by table with checkboxes
            selected_fields = []
            for table, fields in fields_by_table.items():
                st.markdown(f"**{table}**")
                for field in fields:
                    if st.checkbox(f"{field['name']} - {field['description']}", value=True, key=f"field_{table}_{field['name']}"):
                        selected_fields.append(field)
            
            # Option to add new fields
            st.markdown("#### Add New Fields")
            
            # Get all available fields from schema
            all_tables = {}
            for item in st.session_state.schema:
                table_name = item.get("\ufeffTable", "") or item.get("Table", "Other")
                field_name = item.get("Attribute Name", "")
                field_desc = item.get("Attribute Description", "")
                
                if table_name not in all_tables:
                    all_tables[table_name] = []
                
                all_tables[table_name].append({
                    'name': field_name,
                    'description': field_desc,
                    'table': table_name
                })
            
            # Let user select a table and fields to add
            table_to_add = st.selectbox("Select Table", list(all_tables.keys()))
            
            if table_to_add:
                # Filter out fields that are already in the template
                existing_field_names = [f['name'] for f in template['fields'] if f['table'] == table_to_add]
                available_fields = [f for f in all_tables[table_to_add] if f['name'] not in existing_field_names]
                
                if available_fields:
                    st.write(f"Select fields from {table_to_add} to add:")
                    new_fields = []
                    for field in available_fields:
                        if st.checkbox(f"{field['name']} - {field['description']}", key=f"new_{table_to_add}_{field['name']}"):
                            new_fields.append(field)
                    
                    # Add selected new fields
                    selected_fields.extend(new_fields)
                else:
                    st.info(f"All fields from {table_to_add} are already in the template.")
            
            # Submit button
            submit = st.form_submit_button("Update Template")
            
            if submit:
                # Update the template
                templates[st.session_state.selected_template] = {
                    'name': new_name,
                    'description': new_description,
                    'purpose': new_purpose,
                    'fields': selected_fields
                }
                
                st.success("Template updated successfully!")
                st.session_state.selected_template = None
                st.rerun()

def create_custom_template(schema):
    """
    Create a custom template from scratch
    """
    st.markdown("#### Create a New Template")
    
    with st.form("create_template_form"):
        # Basic template info
        new_name = st.text_input("Template Name", placeholder="e.g., Basic Customer Profile")
        new_description = st.text_area("Description", placeholder="Describe the purpose and use case for this template")
        new_purpose = st.selectbox(
            "Purpose",
            ["Customer Acquisition", "Conversion Optimization", "Customer Retention", "Cross-sell & Upsell", "Audience Creation", "Other"]
        )
        
        # Get all available fields from schema
        all_tables = {}
        for item in schema:
            table_name = item.get("\ufeffTable", "") or item.get("Table", "Other")
            field_name = item.get("Attribute Name", "")
            field_desc = item.get("Attribute Description", "")
            
            if table_name not in all_tables:
                all_tables[table_name] = []
            
            all_tables[table_name].append({
                'name': field_name,
                'description': field_desc,
                'table': table_name
            })
        
        # Field selection
        st.markdown("#### Select Fields for Template")
        
        selected_fields = []
        for table_name, fields in all_tables.items():
            with st.expander(f"Fields from {table_name}"):
                for field in fields:
                    if st.checkbox(f"{field['name']} - {field['description']}", key=f"custom_{table_name}_{field['name']}"):
                        selected_fields.append(field)
        
        # Submit button
        submit = st.form_submit_button("Create Template")
        
        if submit:
            if not new_name:
                st.error("Please provide a template name.")
            elif len(selected_fields) == 0:
                st.error("Please select at least one field for the template.")
            else:
                # Create the new template
                new_template = {
                    'name': new_name,
                    'description': new_description,
                    'purpose': new_purpose,
                    'fields': selected_fields
                }
                
                # Add to suggested templates
                if 'suggested_templates' not in st.session_state:
                    st.session_state.suggested_templates = []
                
                st.session_state.suggested_templates.append(new_template)
                st.success("New template created successfully!")
                st.rerun()

def generate_schema_answer(question, schema):
    """
    Generate an answer to a user question about the schema
    """
    # Create a summary of the schema
    table_counts = {}
    for item in schema:
        table = item.get("\ufeffTable", "") or item.get("Table", "")
        if table:
            table_counts[table] = table_counts.get(table, 0) + 1
    
    schema_summary = "Schema Summary:\n"
    for table, count in table_counts.items():
        schema_summary += f"- {table}: {count} attributes\n"
    
    # Sample some attributes from each table (up to 5 per table)
    schema_samples = "Sample Attributes:\n"
    samples_per_table = {}
    
    for item in schema:
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
    
    # Create the prompt
    prompt = f"""
You are a data consultant helping a user explore an Identity Graph schema. Answer the following question about the schema, focusing on helping the user understand what data is available and how it could be used.

User Question: {question}

{schema_summary}

{schema_samples}

Provide a detailed answer that:
1. Directly addresses the user's question
2. References specific tables and fields in the schema that are relevant
3. Suggests potential business applications or use cases where appropriate
4. Keeps the answer focused and practical

Your response should be in markdown format.
"""

    # Call the Anthropic API
    try:
        client = Anthropic()
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1500,
            temperature=0.7,
            system="You are a helpful data consultant specialized in identity graph data and API design. You help users understand their data schema and how to leverage it for business applications.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    except Exception as e:
        st.error(f"Error calling Anthropic API: {e}")
        return "I encountered an error generating your answer. Please try again."

def generate_use_cases(business_objective, business_context, identity_data, 
                     activation_channels, customer_base_size, data_freshness, 
                     privacy_requirements, schema):
    """
    Generate use cases based on the provided inputs.
    """
    # Format the available identity data for the prompt
    available_identity = [k for k, v in identity_data.items() if v]
    available_channels = [k for k, v in activation_channels.items() if v]
    
    # Count number of attributes by table
    table_counts = {}
    for item in schema:
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
    
    for item in schema:
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
    
    # Create the prompt template
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

    # Call the Anthropic API
    try:
        client = Anthropic()
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
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

def parse_use_cases(report):
    """
    Parse the generated report into discrete use cases.
    """
    # Simple regex-based parsing for prototype
    # This will need refinement based on the actual output format
    use_case_pattern = r"## Use Case (\d+): ([^\n]+)\n(.*?)(?=## Use Case \d+:|## Quick Wins|$)"
    
    use_cases = []
    matches = re.finditer(use_case_pattern, report, re.DOTALL)
    
    for match in matches:
        number = match.group(1)
        title = match.group(2).strip()
        content = match.group(3).strip()
        
        # Extract sections within the use case (optional, can be expanded)
        objective_match = re.search(r"### Objective\n(.*?)(?=###|$)", content, re.DOTALL)
        objective = objective_match.group(1).strip() if objective_match else ""
        
        data_match = re.search(r"### Required Identity Graph Data\n(.*?)(?=###|$)", content, re.DOTALL)
        required_data = data_match.group(1).strip() if data_match else ""
        
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
            "required_data": required_data,
            "implementation": implementation,
            "impact": impact,
            "complexity": complexity,
            "full_content": content
        })
    
    return use_cases

def generate_template_suggestions(question, answer, schema):
    """
    Generate template suggestions based on a user question and the AI's answer
    """
    # Create prompt for template generation
    prompt = f"""
Based on the user's question and the answer provided about their identity graph schema, suggest 2-3 API templates that would be useful for implementing the insights discussed. 

User Question: {question}

Answer Provided: {answer}

For each template suggestion, provide:
1. A clear, descriptive name for the template
2. A short description of what the template would be used for
3. The business purpose it would serve (e.g., Customer Acquisition, Retention, etc.)
4. A list of specific fields from the schema that should be included in the template

Focus on creating templates that are:
- Practical and immediately usable
- Aligned with common API use cases
- Optimized with only the necessary fields (not everything)
- Named in a way that clearly communicates their purpose

Format your response as structured JSON that can be parsed programmatically. Use this exact format:

```json
[
  {{
    "name": "Template name",
    "description": "Template description",
    "purpose": "Business purpose",
    "fields": [
      {{
        "table": "Table name",
        "name": "Field name",
        "description": "Field description"
      }}
    ]
  }}
]
```

Use fields that actually exist in the schema where possible.
"""

    # Call the Anthropic API
    try:
        client = Anthropic()
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2000,
            temperature=0.7,
            system="You are a helpful API design expert specialized in identity graph data and API template creation. You help users create efficient and effective API templates based on their data schema.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract the JSON from the response
        json_pattern = r"```json\n(.*?)```"
        json_match = re.search(json_pattern, response.content[0].text, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(1)
            templates = json.loads(json_str)
            return templates
        else:
            # Try to parse the entire response as JSON if no code block is found
            try:
                templates = json.loads(response.content[0].text)
                return templates
            except:
                st.error("Could not parse template suggestions. Please try again.")
                return []
    except Exception as e:
        st.error(f"Error generating template suggestions: {e}")
        return []

def generate_templates_from_use_cases(use_cases, schema):
    """
    Generate API templates based on the generated use cases
    """
    # Extract key information from use cases
    use_case_info = []
    for uc in use_cases:
        use_case_info.append({
            "title": f"Use Case {uc['number']}: {uc['title']}",
            "objective": uc['objective'],
            "required_data": uc['required_data']
        })
    
    # Create the prompt
    prompt = f"""
Based on the following use cases generated for an identity graph, create API templates that would be useful for implementing each use case. Each template should include the specific fields needed.

Use Cases:
{json.dumps(use_case_info, indent=2)}

For each use case, create one API template that includes:
1. A clear, descriptive name for the template (based on the use case title)
2. A short description of what the template would be used for
3. The business purpose it serves (e.g., Customer Acquisition, Retention, etc.)
4. A list of specific fields from the schema that should be included in the template

Focus on creating templates that are:
- Practical and immediately usable
- Aligned with the specific use case objectives
- Optimized with only the necessary fields (not everything)
- Named in a way that clearly communicates their purpose

Format your response as structured JSON that can be parsed programmatically. Use this exact format:

```json
[
  {{
    "name": "Template name",
    "description": "Template description",
    "purpose": "Business purpose",
    "fields": [
      {{
        "table": "Table name",
        "name": "Field name",
        "description": "Field description"
      }}
    ]
  }}
]
```

Include 5-15 highly relevant fields per template, focusing on the data explicitly mentioned in the "required_data" section of each use case.
"""

    # Call the Anthropic API
    try:
        client = Anthropic()
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=3000,
            temperature=0.7,
            system="You are a helpful API design expert specialized in identity graph data and API template creation. You help users create efficient and effective API templates based on their data schema and business use cases.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract the JSON from the response
        json_pattern = r"```json\n(.*?)```"
        json_match = re.search(json_pattern, response.content[0].text, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(1)
            templates = json.loads(json_str)
            return templates
        else:
            # Try to parse the entire response as JSON if no code block is found
            try:
                templates = json.loads(response.content[0].text)
                return templates
            except:
                st.error("Could not parse template suggestions. Please try again.")
                return []
    except Exception as e:
        st.error(f"Error generating templates from use cases: {e}")
        return []

def generate_template_suggestions_direct(schema):
    """
    Generate template suggestions directly from the schema
    """
    # Create a summary of the schema
    table_counts = {}
    for item in schema:
        table = item.get("\ufeffTable", "") or item.get("Table", "")
        if table:
            table_counts[table] = table_counts.get(table, 0) + 1
    
    schema_summary = "Schema Summary:\n"
    for table, count in table_counts.items():
        schema_summary += f"- {table}: {count} attributes\n"
    
    # Sample some attributes from each table (up to 10 per table)
    schema_samples = "Sample Attributes:\n"
    samples_per_table = {}
    
    for item in schema:
        table = item.get("\ufeffTable", "") or item.get("Table", "")
        if table:
            if table not in samples_per_table:
                samples_per_table[table] = []
            
            if len(samples_per_table[table]) < 10:  # Limit to 10 samples per table
                attr_name = item.get("Attribute Name", "")
                attr_desc = item.get("Attribute Description", "")
                if attr_name and attr_desc:
                    samples_per_table[table].append({
                        "name": attr_name,
                        "description": attr_desc
                    })
    
    # Create the prompt
    prompt = f"""
Based on the following identity graph schema, suggest 5 useful API templates that businesses might want to use for common identity-related use cases.

{schema_summary}

Schema Details:
{json.dumps(samples_per_table, indent=2)}

For each template suggestion, provide:
1. A clear, descriptive name for the template
2. A short description of what the template would be used for
3. The business purpose it would serve (e.g., Customer Acquisition, Retention, etc.)
4. A list of specific fields from the schema that should be included in the template

Create templates for these common use cases:
- Basic customer profile information
- Cross-device identity resolution
- Marketing segmentation 
- Personalization
- Customer journey analysis

Focus on creating templates that are:
- Practical and immediately usable
- Aligned with common API use cases
- Optimized with only the necessary fields (not everything)
- Named in a way that clearly communicates their purpose

Format your response as structured JSON that can be parsed programmatically. Use this exact format:

```json
[
  {{
    "name": "Template name",
    "description": "Template description",
    "purpose": "Business purpose",
    "fields": [
      {{
        "table": "Table name",
        "name": "Field name",
        "description": "Field description"
      }}
    ]
  }}
]
```

Include 5-15 fields per template, carefully selecting the most valuable fields for each use case.
"""

    # Call the Anthropic API
    try:
        client = Anthropic()
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=3000,
            temperature=0.7,
            system="You are a helpful API design expert specialized in identity graph data and API template creation. You help users create efficient and effective API templates based on their data schema.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract the JSON from the response
        json_pattern = r"```json\n(.*?)```"
        json_match = re.search(json_pattern, response.content[0].text, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(1)
            templates = json.loads(json_str)
            return templates
        else:
            # Try to parse the entire response as JSON if no code block is found
            try:
                templates = json.loads(response.content[0].text)
                return templates
            except:
                st.error("Could not parse template suggestions. Please try again.")
                return []
    except Exception as e:
        st.error(f"Error generating template suggestions: {e}")
        return []

def generate_follow_up_answer(question, selected_case, schema, context_data):
    """
    Generate a detailed answer to a follow-up question about a specific use case.
    """
    # Create a prompt for the follow-up question
    prompt = f"""
I need a detailed answer to a follow-up question about a specific identity graph use case. Here's the context:

QUESTION: {question}

USE CASE INFORMATION:
Title: Use Case {selected_case['number']}: {selected_case['title']}

Objective:
{selected_case['objective']}

Required Identity Graph Data:
{selected_case['required_data']}

Implementation Approach:
{selected_case['implementation']}

Expected Business Impact:
{selected_case['impact']}

Technical Complexity:
{selected_case['complexity']}

Please provide a comprehensive, detailed answer to the question that is specific to this use case and business context. Include practical examples, implementation details, and actionable advice where appropriate.
"""

    # Call the Anthropic API
    try:
        client = Anthropic()
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
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
