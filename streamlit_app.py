import streamlit as st
import pandas as pd
import math
from pathlib import Path

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Email Processing Demo',
    page_icon='📧', # This is an emoji shortcode. Could be a URL too.
)

# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data
def get_gdp_data():
    """Grab GDP data from a CSV file.

    This uses caching to avoid having to read the file every time. If we were
    reading from an HTTP endpoint instead of a file, it's a good idea to set
    a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
    """

    # Instead of a CSV on disk, you could read from an HTTP endpoint here too.
    DATA_FILENAME = Path(__file__).parent/'data/gdp_data.csv'
    raw_gdp_df = pd.read_csv(DATA_FILENAME)

    MIN_YEAR = 1960
    MAX_YEAR = 2022

    # The data above has columns like:
    # - Country Name
    # - Country Code
    # - [Stuff I don't care about]
    # - GDP for 1960
    # - GDP for 1961
    # - GDP for 1962
    # - ...
    # - GDP for 2022
    #
    # ...but I want this instead:
    # - Country Name
    # - Country Code
    # - Year
    # - GDP
    #
    # So let's pivot all those year-columns into two: Year and GDP
    gdp_df = raw_gdp_df.melt(
        ['Country Code'],
        [str(x) for x in range(MIN_YEAR, MAX_YEAR + 1)],
        'Year',
        'GDP',
    )

    # Convert years from string to integers
    gdp_df['Year'] = pd.to_numeric(gdp_df['Year'])

    return gdp_df


def process_email_with_langgraph(email_text):
    """
    Process email and generate Giovanni Matadore data comparison.
    Replace this with your actual LangGraph implementation.
    """
    try:
        # Simulate some processing
        word_count = len(email_text.split())
        char_count = len(email_text)
        
        # Sample data for Giovanni Matadore - Current in database
        current_data = {
            "Field": ["First Name", "Last Name", "Date of Birth", "Address", "City", "Postal Code", "Phone", "Email", "Occupation"],
            "Current Value": [
                "Giovanni", 
                "Matadore", 
                "1985-03-15", 
                "Via Ciseri 12", 
                "Locarno", 
                "6600", 
                "+41 91 751 2847", 
                "g.matadore@email.ch", 
                "Software Engineer"
            ]
        }
        
        # Proposed changes
        proposed_data = {
            "Field": ["First Name", "Last Name", "Date of Birth", "Address", "City", "Postal Code", "Phone", "Email", "Occupation"],
            "Proposed Value": [
                "Giovanni", 
                "Matadore", 
                "1985-03-15", 
                "Via Pretorio 18", 
                "Lugano", 
                "6900", 
                "+41 91 922 3456", 
                "g.matadore@lugano-mail.ch", 
                "Senior Software Engineer"
            ]
        }
        
        result = {
            "status": "success",
            "word_count": word_count,
            "char_count": char_count,
            "summary": f"Email processed successfully. Contains {word_count} words and {char_count} characters.",
            "processed_text": email_text[:100] + "..." if len(email_text) > 100 else email_text,
            "current_data": current_data,
            "proposed_data": proposed_data
        }
        
        return result
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


gdp_df = get_gdp_data()

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
'''
# 📧 Email automation

We're processing incoming email requests by first receiving 
the mail, then generating an action plan and displaying the results. 
Once we get permission to execute, the system handles the 
execution behind the scenes and provides a sample writeback.
'''

# Add some spacing
''
''

# -----------------------------------------------------------------------------
# EMAIL PROCESSING SECTION
st.header('Email input', divider='blue')

# Text area for email input
email_input = st.text_area(
    "Paste your email content here:",
    height=200,
    placeholder="Paste your email content here and click 'Process Email' to run your LangGraph code..."
)

# Button to process email
if st.button('Process Email', type='primary'):
    if email_input.strip():
        with st.spinner('Processing email with LangGraph...'):
            # Call your processing function
            result = process_email_with_langgraph(email_input)
            
            if result["status"] == "success":
                st.success("Email processed successfully!")
                
                # Display results
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Word Count", result["word_count"])
                with col2:
                    st.metric("Character Count", result["char_count"])
                
                st.subheader("Processing Summary")
                st.write(result["summary"])
                
                # Display the two tables with Giovanni's data
                st.subheader("Data Comparison for Giovanni Matadore")
                
                # Create three columns: table1, arrow, table2
                table_col1, arrow_col, table_col2 = st.columns([3, 1, 3])
                
                with table_col1:
                    st.markdown("**📊 From Database**")
                    current_df = pd.DataFrame(result["current_data"])
                    st.dataframe(current_df, use_container_width=True, hide_index=True)
                
                with arrow_col:
                    st.markdown("<br><br><br><br>", unsafe_allow_html=True)  # Add some vertical spacing
                    st.markdown("### ➡️")
                
                with table_col2:
                    st.markdown("**📝 Proposed Changes**")
                    proposed_df = pd.DataFrame(result["proposed_data"])
                    st.dataframe(proposed_df, use_container_width=True, hide_index=True)
                
                # Right-align the Accept changes button
                col1, col2, col3 = st.columns([2, 1, 1])
                with col3:
                    st.button('Accept changes', type='secondary')
                
            else:
                st.error(f"Error processing email: {result['error']}")
    else:
        st.warning("Please paste some email content before processing.")

# Add some spacing
''
''
