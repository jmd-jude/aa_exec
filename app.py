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
    api_provider = st.selectbox("Select Platform", ["OpenAI", "Anthropic"])
    
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
                        "PRIMARY_OBJECTIVE": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "TARGET_AUDIENCE_AGE": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "TARGET_AUDIENCE_GENDER": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "CREATED_AT": {"type": "TIMESTAMP_NTZ", "nullable": True, "primary_key": False}
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
                        "BUDGET": {"type": "FLOAT", "nullable": True, "primary_key": False},
                        "TARGET_PLATFORMS": {"type": "VARIANT", "nullable": True, "primary_key": False},
                        "CAMPAIGN_STATUS": {"type": "TEXT", "nullable": True, "primary_key": False}
                    }
                },
                "INFLUENCERS": {
                    "fields": {
                        "INFLUENCER_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "NAME": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "TIER": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "PRIMARY_PLATFORM": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "PRIMARY_CATEGORY": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "FOLLOWER_COUNT": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "ENGAGEMENT_RATE": {"type": "FLOAT", "nullable": True, "primary_key": False},
                        "AUDIENCE_FEMALE_PCT": {"type": "FLOAT", "nullable": True, "primary_key": False},
                        "AUDIENCE_MALE_PCT": {"type": "FLOAT", "nullable": True, "primary_key": False}
                    }
                },
                "CAMPAIGN_INFLUENCERS": {
                    "fields": {
                        "CAMPAIGN_INFLUENCER_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "CAMPAIGN_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "INFLUENCER_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "COMPENSATION": {"type": "FLOAT", "nullable": True, "primary_key": False},
                        "CONTENT_REQUIREMENTS": {"type": "VARIANT", "nullable": True, "primary_key": False},
                        "PLATFORM": {"type": "TEXT", "nullable": True, "primary_key": False}
                    }
                },
                "PERFORMANCE_DATA": {
                    "fields": {
                        "PERFORMANCE_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "CAMPAIGN_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "INFLUENCER_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "CONTENT_TYPE": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "PLATFORM": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "IMPRESSIONS": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "LIKES": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "COMMENTS": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "CLICKS": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "CONVERSIONS": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "ROI": {"type": "FLOAT", "nullable": True, "primary_key": False}
                    }
                }
            }
        },
        "business_context": {
            "description": "Social Growth is a leading influencer marketing agency that connects brands with influential content creators across multiple platforms. This dataset encompasses profiles of influencers across various tiers and niches, brand partnerships, campaign performance metrics, and audience demographics.",
            "table_descriptions": {
                "BRANDS": {
                    "description": "Client company profiles with industry sectors, marketing objectives, budget information, and target audience preferences for campaign planning."
                },
                "CAMPAIGNS": {
                    "description": "Marketing initiatives with defined objectives, timelines, budgets, and target platforms. Tracks campaign status from planning through completion."
                },
                "INFLUENCERS": {
                    "description": "Detailed profiles of content creators across various platforms, categories, and influence tiers. Includes engagement metrics and demographic information."
                },
                "CAMPAIGN_INFLUENCERS": {
                    "description": "Junction table connecting influencers to specific campaigns, including compensation details and content requirements."
                },
                "PERFORMANCE_DATA": {
                    "description": "Content-level performance metrics for influencer posts, including impressions, engagements, clicks, conversions, and ROI calculations."
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
                        "FIRST_NAME": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "LAST_NAME": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "EMAIL_HASH": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "FAN_SINCE": {"type": "TIMESTAMP_NTZ", "nullable": True, "primary_key": False},
                        "ACQUISITION_SOURCE": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "LIFETIME_VALUE": {"type": "FLOAT", "nullable": True, "primary_key": False},
                        "FAN_SEGMENT": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "LOYALTY_TIER": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "AGE_RANGE": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "GENDER": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "MARKETING_CONSENT": {"type": "BOOLEAN", "nullable": True, "primary_key": False}
                    }
                },
                "GAMES": {
                    "fields": {
                        "GAME_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "SEASON_YEAR": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "OPPONENT": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "GAME_DATE": {"type": "TIMESTAMP_NTZ", "nullable": True, "primary_key": False},
                        "IS_HOME_GAME": {"type": "BOOLEAN", "nullable": True, "primary_key": False},
                        "GAME_TYPE": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "ATTENDANCE": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "RESULT": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "TEAM_SCORE": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "OPPONENT_SCORE": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "SPECIAL_PROMOTION": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "TV_NETWORK": {"type": "TEXT", "nullable": True, "primary_key": False}
                    }
                },
                "TICKETS": {
                    "fields": {
                        "TICKET_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "FAN_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "GAME_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "PURCHASE_DATE": {"type": "TIMESTAMP_NTZ", "nullable": True, "primary_key": False},
                        "QUANTITY": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "SECTION": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "TICKET_TYPE": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "PRICE_PER_TICKET": {"type": "FLOAT", "nullable": True, "primary_key": False},
                        "TOTAL_AMOUNT": {"type": "FLOAT", "nullable": True, "primary_key": False},
                        "PURCHASE_CHANNEL": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "IS_SEASON_TICKET": {"type": "BOOLEAN", "nullable": True, "primary_key": False}
                    }
                },
                "MERCHANDISE_SALES": {
                    "fields": {
                        "TRANSACTION_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "FAN_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "GAME_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "TRANSACTION_DATE": {"type": "TIMESTAMP_NTZ", "nullable": True, "primary_key": False},
                        "LOCATION": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "SUBTOTAL_AMOUNT": {"type": "FLOAT", "nullable": True, "primary_key": False},
                        "DISCOUNT_AMOUNT": {"type": "FLOAT", "nullable": True, "primary_key": False},
                        "TOTAL_AMOUNT": {"type": "FLOAT", "nullable": True, "primary_key": False},
                        "PAYMENT_METHOD": {"type": "TEXT", "nullable": True, "primary_key": False}
                    }
                },
                "MERCHANDISE_PRODUCTS": {
                    "fields": {
                        "PRODUCT_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "SKU": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "NAME": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "CATEGORY": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "IS_PLAYER_SPECIFIC": {"type": "BOOLEAN", "nullable": True, "primary_key": False},
                        "PLAYER_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "BASE_PRICE": {"type": "FLOAT", "nullable": True, "primary_key": False},
                        "CURRENT_PRICE": {"type": "FLOAT", "nullable": True, "primary_key": False},
                        "INVENTORY_QUANTITY": {"type": "NUMBER", "nullable": True, "primary_key": False}
                    }
                },
                "CONCESSION_SALES": {
                    "fields": {
                        "TRANSACTION_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "GAME_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "FAN_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "TRANSACTION_TIME": {"type": "TIMESTAMP_NTZ", "nullable": True, "primary_key": False},
                        "CONCESSION_LOCATION": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "PERIOD": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "TOTAL_AMOUNT": {"type": "FLOAT", "nullable": True, "primary_key": False},
                        "PAYMENT_METHOD": {"type": "TEXT", "nullable": True, "primary_key": False}
                    }
                },
                "DIGITAL_ENGAGEMENT": {
                    "fields": {
                        "ENGAGEMENT_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "FAN_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "CHANNEL": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "EVENT_TYPE": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "CONTENT_CATEGORY": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "DEVICE_TYPE": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "TIMESTAMP": {"type": "TIMESTAMP_NTZ", "nullable": True, "primary_key": False},
                        "GAME_RELATED": {"type": "BOOLEAN", "nullable": True, "primary_key": False},
                        "GAME_ID": {"type": "TEXT", "nullable": True, "primary_key": False}
                    }
                }
            }
        },
        "business_context": {
            "description": "The Metro Mavericks are a professional basketball team with diverse fan engagement across digital and in-person channels. This dataset encompasses complete fan profiles, attendance patterns, merchandise purchases, and engagement data to enable data-driven decisions for growing the fanbase and maximizing revenue opportunities.",
            "table_descriptions": {
                "FANS": {
                    "description": "Core profiles of team fans including demographics, segments, and lifetime value. Contains both personally identifiable information (hashed for privacy) and behavioral classifications."
                },
                "GAMES": {
                    "description": "Complete game history with opponent, scores, attendance, and broadcast details. Includes both regular season and playoff games."
                },
                "TICKETS": {
                    "description": "Ticket purchase history for all games, including both individual game tickets and season ticket packages. Contains pricing, seating, and purchase channel information."
                },
                "MERCHANDISE_SALES": {
                    "description": "Transaction records for merchandise purchases, with links to specific fans when available. Includes location, payment method, and summary financial information."
                },
                "MERCHANDISE_PRODUCTS": {
                    "description": "Catalog of all team merchandise available for purchase, with categories, pricing, and inventory information. Includes both player-specific and general team items."
                },
                "CONCESSION_SALES": {
                    "description": "In-stadium food and beverage purchases during games, with details on timing, location, and items purchased. Can be linked to specific fans when loyalty cards are used."
                },
                "DIGITAL_ENGAGEMENT": {
                    "description": "Fan interaction with team's digital properties, including website, mobile app, email, and social media. Contains detailed behavior tracking for engagement analysis."
                }
            }
        }
    },

    "E-commerce Database": {
        "base_schema": {
            "tables": {
                "UNIFIED_CUSTOMERS": {
                    "fields": {
                        "CUSTOMER_ID": {"type": "TEXT", "nullable": False, "primary_key": False},
                        "EMAIL_HASH": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "GA4_USER_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "FIRST_NAME": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "LAST_NAME": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "CUSTOMER_SINCE": {"type": "TIMESTAMP_NTZ", "nullable": True, "primary_key": False},
                        "LIFETIME_VALUE": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "SEGMENT": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "ACQUISITION_CHANNEL": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "LAST_PURCHASE_DATE": {"type": "TIMESTAMP_NTZ", "nullable": True, "primary_key": False},
                        "PURCHASE_COUNT": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "MARKETING_CONSENT": {"type": "BOOLEAN", "nullable": True, "primary_key": False}
                    }
                },
                "CUSTOMER_DEMOGRAPHICS": {
                    "fields": {
                        "CUSTOMER_ID": {"type": "TEXT", "nullable": False, "primary_key": False},
                        "AGE_RANGE": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "INCOME_RANGE": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "EDUCATION_LEVEL": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "OCCUPATION_CATEGORY": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "HOUSEHOLD_SIZE": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "HOMEOWNER_STATUS": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "LIFESTYLE_SEGMENT": {"type": "TEXT", "nullable": True, "primary_key": False}
                    }
                },
                "SHOP_ORDERS": {
                    "fields": {
                        "ORDER_ID": {"type": "TEXT", "nullable": False, "primary_key": False},
                        "CUSTOMER_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "ORDER_DATE": {"type": "TIMESTAMP_NTZ", "nullable": True, "primary_key": False},
                        "TOTAL_AMOUNT": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "SUBTOTAL_AMOUNT": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "TAX_AMOUNT": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "SHIPPING_AMOUNT": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "DISCOUNT_AMOUNT": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "ORDER_STATUS": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "ATTRIBUTION_CHANNEL": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "FIRST_TOUCH_CHANNEL": {"type": "TEXT", "nullable": True, "primary_key": False}
                    }
                },
                "SHOP_ORDER_ITEMS": {
                    "fields": {
                        "ORDER_ITEM_ID": {"type": "TEXT", "nullable": False, "primary_key": False},
                        "ORDER_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "PRODUCT_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "QUANTITY": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "PRICE": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "DISCOUNT_AMOUNT": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "TOTAL_AMOUNT": {"type": "NUMBER", "nullable": True, "primary_key": False}
                    }
                },
                "SHOP_PRODUCTS": {
                    "fields": {
                        "PRODUCT_ID": {"type": "TEXT", "nullable": False, "primary_key": False},
                        "SKU": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "NAME": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "CATEGORY": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "SUBCATEGORY": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "BRAND": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "BASE_PRICE": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "CURRENT_PRICE": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "INVENTORY_QUANTITY": {"type": "NUMBER", "nullable": True, "primary_key": False}
                    }
                },
                "WEB_SESSIONS": {
                    "fields": {
                        "SESSION_ID": {"type": "TEXT", "nullable": False, "primary_key": False},
                        "CUSTOMER_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "START_TIMESTAMP": {"type": "TIMESTAMP_NTZ", "nullable": True, "primary_key": False},
                        "END_TIMESTAMP": {"type": "TIMESTAMP_NTZ", "nullable": True, "primary_key": False},
                        "DEVICE_CATEGORY": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "DEVICE_OS": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "SOURCE": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "MEDIUM": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "LANDING_PAGE": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "SESSION_DURATION": {"type": "NUMBER", "nullable": True, "primary_key": False},
                        "PAGE_VIEWS": {"type": "NUMBER", "nullable": True, "primary_key": False}
                    }
                },
                "WEB_EVENTS": {
                    "fields": {
                        "EVENT_ID": {"type": "TEXT", "nullable": False, "primary_key": False},
                        "SESSION_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "CUSTOMER_ID": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "EVENT_TIMESTAMP": {"type": "TIMESTAMP_NTZ", "nullable": True, "primary_key": False},
                        "EVENT_NAME": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "EVENT_CATEGORY": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "EVENT_ACTION": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "PAGE_URL": {"type": "TEXT", "nullable": True, "primary_key": False},
                        "PRODUCT_ID": {"type": "TEXT", "nullable": True, "primary_key": False}
                    }
                }
            }
        },
        "business_context": {
            "description": "EcoShop is an e-commerce retailer offering products across multiple categories. This data model captures customer interactions across digital touchpoints, purchase behavior, and demographic information to drive personalized marketing and optimize the customer journey.",
            "table_descriptions": {
                "UNIFIED_CUSTOMERS": {
                    "description": "Core customer profiles including identity, segment, acquisition channel, and engagement metrics. Contains summary information on lifetime value and purchase history."
                },
                "CUSTOMER_DEMOGRAPHICS": {
                    "description": "Detailed demographic data for customers including age range, income level, education, occupation, and lifestyle segments for targeted marketing."
                },
                "SHOP_PRODUCTS": {
                    "description": "Product catalog with detailed information on categories, pricing, and inventory status. Includes both current and base pricing for margin analysis."
                },
                "SHOP_ORDERS": {
                    "description": "Transaction records with order totals, tax, shipping, and attribution channels. Contains order status and fulfillment information."
                },
                "SHOP_ORDER_ITEMS": {
                    "description": "Line item details for each product purchased within orders, including quantity, price, and discounts at the item level."
                },
                "WEB_SESSIONS": {
                    "description": "Customer browsing sessions on the e-commerce platform with device information, traffic source, and engagement metrics like duration and page views."
                },
                "WEB_EVENTS": {
                    "description": "Granular user interaction events within web sessions, including page views, product views, cart additions, and purchases with timestamps."
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
               - What are 3-5 specific, detailed analytical queries that would be valuable to a strategic decision maker?
               - For each query, explain what business value it would provide.
            """
        
        if include_phylum_2:
            analysis_prompt += """
            2. OPTIMIZATION OPPORTUNITIES:
               - What derived metrics, calculations, or views could add value?
               - Identify potential segmentations that aren't explicitly modeled but could be easily derived.
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
