import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Configure the page
st.set_page_config(
    page_title="Conversational Identity Intelligence",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS - simplified
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #1E3A8A;
    }
    .metric-card {
        background-color: #F3F4F6;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1E3A8A;
    }
    .metric-label {
        font-size: 1rem;
        color: #4B5563;
    }
    .quote {
        font-style: italic;
        padding: 15px;
        border-left: 5px solid #1E3A8A;
        background-color: #F3F4F6;
        margin: 20px 0;
    }
    .quote-author {
        font-weight: bold;
        text-align: right;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">Conversational Identity Intelligence</div>', unsafe_allow_html=True)
st.markdown("### Executive Proposal for Audience Acuity")

# Navigation tabs - simplified
tabs = st.tabs([
    "Press Release", 
    "Executive Summary", 
    "Strategic Roadmap", 
    "Competitive Advantage",
    "FAQ & Next Steps"
])

# Tab 1: Press Release
with tabs[0]:
    st.markdown("# Audience Acuity Unveils Conversational Identity Intelligence")
    st.markdown("##### Enabling Non-Technical Users to Extract Strategic Value from Identity Data")
    st.markdown("**Las Vegas, June 1, 2025**")
    
    st.markdown("""
    Audience Acuity, the leading identity resolution provider, today announced the launch of Conversational Identity Intelligence, a transformative addition to its Super Identity Graph (SIG) that enables marketers and business strategists to interact with complex identity data through natural language. This industry-first capability eliminates the technical barriers that have traditionally limited identity data insights to SQL-proficient analysts, democratizing access to the company's industry-leading identity resolution platform.
    """)
    
    st.markdown('<div class="quote">With Conversational Identity Intelligence, we\'re fundamentally changing how enterprises interact with identity data. By removing technical barriers, we\'re empowering strategic marketers to directly transform our unparalleled identity data into business outcomes without dependency on data teams. This represents a paradigm shift from identity as a technical asset to identity as a strategic advantage.</div><div class="quote-author">— Jeff Berke, CEO of Audience Acuity</div>', unsafe_allow_html=True)
    
    st.markdown("""
    Identity data has long been trapped behind complex query languages, forcing marketers to rely on technical teams to extract insights. Audience Acuity's new capability allows users to simply ask questions like "Which customer segments had the highest response rates to our last campaign?" or "What's the best channel mix to reach our high-value customers?" and receive instant, actionable answers with visualizations and strategic recommendations.
    """)
    
    st.markdown('<div class="quote">Before Conversational Identity Intelligence, getting answers from our identity data required submitting tickets to our analytics team with a 2-week turnaround. Now my team can explore identity insights in real-time during our strategy sessions, test hypotheses on the spot, and move directly from insights to activation. We\'ve reduced our campaign planning cycle from weeks to days.</div><div class="quote-author">— Jane Smith, VP of Customer Acquisition at a Fortune 100 retailer</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="quote">This isn\'t just a chat interface slapped onto an identity graph. We\'ve built a true reasoning layer that understands both identity resolution concepts and strategic marketing objectives, creating a bridge between technical data and business outcomes.</div><div class="quote-author">— Jeff Sopko, Chief Growth Officer at Audience Acuity</div>', unsafe_allow_html=True)

# Tab 2: Executive Summary
with tabs[1]:
    st.markdown("## Executive Summary")
    
    st.markdown("### The Opportunity")
    st.markdown("""
    Audience Acuity's Super Identity Graph (SIG) delivers unparalleled identity resolution capabilities, but a critical gap exists between raw identity data and actionable business strategy. By integrating a conversational reasoning layer, we can bridge this gap – empowering business users to translate identity insights into strategic action through natural conversation.
    """)
    
    st.markdown("### Strategic Impact")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="metric-card"><div class="metric-value">+30-40%</div><div class="metric-label">Revenue: Increase in ARPU through premium tier</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-card"><div class="metric-value">+25%</div><div class="metric-label">Growth: Reduction in CAC with intuitive demos</div></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card"><div class="metric-value">-25%</div><div class="metric-label">Retention: Reduction in churn through deeper adoption</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-card"><div class="metric-value">+50%</div><div class="metric-label">Customer Expansion: Increase in users per account</div></div>', unsafe_allow_html=True)

# Tab 3: Strategic Roadmap
with tabs[2]:
    st.markdown("## Strategic Roadmap")
    
    # Simple timeline data
    current_date = datetime.now()
    q2_start = datetime(current_date.year, 4, 1)
    if current_date.month > 6:
        q2_start = datetime(current_date.year + 1, 4, 1)
    
    timeline_data = [
        dict(Task="NOW: Snowflake MVP", Start=q2_start.strftime('%Y-%m-%d'), 
             Finish=(q2_start + timedelta(days=180)).strftime('%Y-%m-%d'), Phase="NOW"),
        dict(Task="NEXT: Snowflake GA", Start=(q2_start + timedelta(days=180)).strftime('%Y-%m-%d'), 
             Finish=(q2_start + timedelta(days=360)).strftime('%Y-%m-%d'), Phase="NEXT"),
        dict(Task="LATER: Multi-Platform", Start=(q2_start + timedelta(days=360)).strftime('%Y-%m-%d'), 
             Finish=(q2_start + timedelta(days=540)).strftime('%Y-%m-%d'), Phase="LATER"),
    ]
    
    df = pd.DataFrame(timeline_data)
    
    # Timeline visualization
    fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Phase",
                     color_discrete_map={"NOW":"#1E3A8A", "NEXT":"#3B82F6", "LATER":"#93C5FD"})
    
    fig.update_layout(
        title="Strategic Roadmap Timeline",
        xaxis_title="",
        yaxis_title="",
        legend_title="Phase",
        xaxis=dict(
            tickformat="%b %Y",
            dtick="M3"
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # NOW/NEXT/LATER details
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### NOW (Q2-Q3 2025)")
        st.markdown("**Snowflake MVP Integration**")
        st.markdown("""
        - Refactor prototype for native Snowflake app integration
        - Deploy with 3-5 strategic customers for validation
        - Develop initial success metrics and testimonials
        
        **Goal**: Validate market fit with minimal development while gathering customer testimonials
        """)
    
    with col2:
        st.markdown("### NEXT (Q4 2025 - Q1 2026)")
        st.markdown("**Snowflake General Availability**")
        st.markdown("""
        - Enhance user experience based on beta feedback
        - Scale reasoning and performance for enterprise-level usage
        - Add integration with activation platforms
        
        **Goal**: Drive adoption across Snowflake customer base and demonstrate ROI
        """)
    
    with col3:
        st.markdown("### LATER (2026+)")
        st.markdown("**Multi-Platform Expansion**")
        st.markdown("""
        - Extend capability to additional data cloud platforms (Databricks, etc.)
        - Develop specialized vertical solutions that align with other AA GTMs
        - Enable cross-platform identity intelligence
        
        **Goal**: Expand addressable market and reinforce AA as the identity authority across all data environments
        """)

# Tab 4: Competitive Advantage
with tabs[3]:
    st.markdown("## Competitive Advantage")
    
    st.markdown("""
    This capability establishes Audience Acuity as the innovation leader in the identity space with three market-differentiating benefits:
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### Accessibility Advantage")
        st.markdown("Expands identity data value from technical teams to business decision-makers")
    
    with col2:
        st.markdown("### Execution Advantage")
        st.markdown("Reduces time from insight to activation from weeks to minutes")
    
    with col3:
        st.markdown("### Strategic Advantage")
        st.markdown("Transforms identity from a data asset to a strategic decision engine")

# Tab 5: FAQ & Next Steps
with tabs[4]:
    st.markdown("## Key Questions & Answers")
    
    with st.expander("How is this different from other natural language interfaces to data?"):
        st.markdown("""
        Unlike general natural language query tools, Conversational Identity Intelligence is specifically designed for identity data. It understands complex identity concepts like match rates, identity resolution, cross-channel recognition, and audience activation. It's not just translating language to SQL—it's providing a reasoning layer that bridges identity data with marketing strategy.
        """)
    
    with st.expander("Does this require sharing our data outside of Snowflake?"):
        st.markdown("""
        No. Like all Audience Acuity services, Conversational Identity Intelligence operates entirely within your Snowflake environment. No data leaves your secure environment, maintaining complete data governance and privacy compliance.
        """)
    
    with st.expander("How does this position us against competitors?"):
        st.markdown("""
        This capability establishes a significant competitive moat by transforming our identity graph from a technical resource into a strategic business tool. No competitor currently offers natural language interaction with identity data, giving us a first-mover competitive advantage in the enterprise market.
        """)
    
    with st.expander("What resources are required to build this?"):
        st.markdown("""
        This capability would be developed through a combination of internal resources and specialized Data Cloud with AI expertise. The total development time would be approximately 2 quarters from concept to GA, with 3 months of intensive beta testing with strategic customers.
        """)
    
    st.markdown("## Next Steps")
    
    next_week = (datetime.now() + timedelta(days=7)).strftime('%B %d, %Y')
    kickoff_week = (datetime.now() + timedelta(days=14)).strftime('%B %d, %Y')
    validation_week = (datetime.now() + timedelta(days=21)).strftime('%B %d, %Y')
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"### Executive Approval (Week of {next_week})")
        st.markdown("""
        - Confirm strategic alignment
        - Align on resource allocation
        - Finalize timeline and metrics
        """)
    
    with col2:
        st.markdown(f"### Development Kickoff (Week of {kickoff_week})")
        st.markdown("""
        - Assemble technical resources
        - Establish project management framework
        - Begin MVP implementation
        """)
    
    with col3:
        st.markdown(f"### Customer Validation (Week of {validation_week})")
        st.markdown("""
        - Identify beta customers
        - Confirm use cases and success metrics
        - Schedule initial feedback sessions
        """)

# Footer
st.markdown("---")
st.markdown("© 2025 Audience Acuity | Confidential - For Internal Use Only")