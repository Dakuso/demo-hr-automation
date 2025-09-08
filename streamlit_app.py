import streamlit as st
import pandas as pd
import math
from pathlib import Path
from langg_automation import main as process_mail

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Email Processing Demo',
    page_icon='📧', # This is an emoji shortcode. Could be a URL too.
)

# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data
def get_employee_data():
    """Grab Employee data from a CSV file.

    This uses caching to avoid having to read the file every time. If we were
    reading from an HTTP endpoint instead of a file, it's a good idea to set
    a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
    """

    # Instead of a CSV on disk, you could read from an HTTP endpoint here too.
    # NOTE: This function and its data are not used in the final app display,
    # but are kept as part of the original script structure.
    # To run this locally, you would need a 'data/employee_data.csv' file.
    try:
        DATA_FILENAME = Path(__file__).parent/'data/employee_data.csv'
        raw_gdp_df = pd.read_csv(DATA_FILENAME)
        return raw_gdp_df
    
    except FileNotFoundError:
        # Return an empty DataFrame if the file is not found
        return pd.DataFrame()



def highlight_changes(current_df, proposed_df):
    """
    Create styled dataframes that highlight changes between current and proposed values
    """
    def style_row(row, other_df, self_col, other_col):
        field = row['Field']
        self_val = row[self_col]
        
        other_row = other_df[other_df['Field'] == field]
        
        # Default style is no background color
        style = [''] * len(row)
        
        if not other_row.empty:
            other_val = other_row[other_col].iloc[0]
            if str(self_val) != str(other_val):
                # Apply red background to the entire row if values differ
                style = ['background-color: #4a272a'] * len(row)
        return style

    # Apply styling
    styled_current = current_df.style.apply(
        style_row, other_df=proposed_df, self_col='Current Value', other_col='Proposed Value', axis=1
    )
    styled_proposed = proposed_df.style.apply(
        style_row, other_df=current_df, self_col='Proposed Value', other_col='Current Value', axis=1
    )
    
    return styled_current, styled_proposed


def process_email_with_langgraph(email_text):
    """
    Process email and generate Giovanni Matadore data comparison.
    Replace this with your actual LangGraph implementation.
    """
    if not st.session_state.anthropic_api_key:
        return {
            "status": "error",
            "error": "Anthropic API Key not provided."
        }
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
                "+41 91 922 3456", 
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
                "Software Engineer"
            ]
        }
        
        result = {
            "status": "success",
            "word_count": word_count,
            "char_count": char_count,
        }

        state = process_mail(email_text, st.session_state.anthropic_api_key)
        return  {**result, **state}
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# -----------------------------------------------------------------------------
# Initialize session state for the API key
# This ensures that these values persist across reruns.

if 'anthropic_api_key' not in st.session_state:
    st.session_state.anthropic_api_key = ''

# Create a secret input field in a sidebar or expander
st.sidebar.header("🔑 API Key Configuration")
st.session_state.anthropic_api_key = st.sidebar.text_input(
    "Enter your Anthropic API Key:",
    type="password"
)


# -----------------------------------------------------------------------------
# Initialize session state variables
# This ensures that these values persist across reruns.
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'processing_result' not in st.session_state:
    st.session_state.processing_result = None
if 'changes_accepted' not in st.session_state:
    st.session_state.changes_accepted = False

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
employee_display = False
if employee_display:
    st.title("🏢 Employee Data Dashboard")

    # Load the data
    employee_df = get_employee_data()

    # Only proceed if the DataFrame is not empty
    if not employee_df.empty:

        # --- Interactive DataFrame (Best for Exploration) ---
        st.header("Interactive Employee Table 📊")
        st.info("You can sort, resize, and scroll through this table.")
        st.dataframe(employee_df)

        
        # Calculate metrics
        total_employees = len(employee_df)
        avg_salary = employee_df['AnnualGrossSalary_CHF'].mean()

        # Display metrics in columns
        col1, col2 = st.columns(2)
        col1.metric(label="Total Employees", value=total_employees)
        col2.metric(label="Average Annual Salary (CHF)", value=f"{avg_salary:,.2f}")

    else:
        st.warning("Could not display data because the DataFrame is empty.")


''
''


# -----------------------------------------------------------------------------
# EMAIL PROCESSING SECTION
st.header('Email input', divider='blue')

# Text area for email input
email_input = st.text_area(
    "Paste your email content here:",
    height=200,
    placeholder="Paste your email content here and click 'Process Email'..."
)

# Button to process email
if st.button('Process Email', type='primary'):
    if email_input.strip():
        with st.spinner('Processing email...'):
            result = process_email_with_langgraph(email_input)
            
            if result["status"] == "success":
                # Store the result in the session state and reset flags
                st.session_state.processing_complete = True
                st.session_state.processing_result = result
                st.session_state.changes_accepted = False # Reset if reprocessing
            else:
                st.error(f"Error processing email: {result['error']}")
                st.session_state.processing_complete = False
    else:
        st.warning("Please paste some email content before processing.")

# This block will now run ONLY if processing was completed successfully in a previous run.
if st.session_state.processing_complete:
    result = st.session_state.processing_result
    
    st.success("Email processed successfully!")
    
    # Display results
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Word Count", result["word_count"])
    with col2:
        st.metric("Character Count", result["char_count"])
    
    # Display the two tables with Giovanni's data
    st.subheader("Data Comparison for Giovanni Matadore")
    
    # Create DataFrames
    current_df = result["current_data"]
    proposed_df = result["proposed_data"]
    
    # Get styled dataframes with highlighted changes
    styled_current, styled_proposed = highlight_changes(current_df, proposed_df)
    
    # Create three columns: table1, arrow, table2
    table_col1, arrow_col, table_col2 = st.columns([5, 1, 5])
    
    with table_col1:
        st.markdown("**📊 From Database**")
        st.dataframe(styled_current, use_container_width=True, hide_index=True)
    
    with arrow_col:
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)  # Add some vertical spacing
        st.markdown("<p style='text-align: center; font-size: 2.5em;'>➡️</p>", unsafe_allow_html=True)
    
    with table_col2:
        st.markdown("**📝 Proposed Changes**")

        # edited_proposed_df = st.data_editor(proposed_df, use_container_width=True, hide_index=True)
        
        st.dataframe(styled_proposed, use_container_width=True, hide_index=True)

    # --- ACCEPT CHANGES LOGIC ---
    # Show the "Accept changes" button only if they haven't been accepted yet.
    if not st.session_state.changes_accepted:
        # Align the button to the right
        b_col1, b_col2 = st.columns([4, 1])
        with b_col2:
            if st.button('Accept changes'):
                st.session_state.changes_accepted = True
                st.rerun() # Rerun the script immediately to show the success message

    # Show the success message if changes have been accepted.
    if st.session_state.changes_accepted:
        st.success('✅ Your changes have been executed and documented! See the documentation [here](https://dakuso.github.io).')


# Add some spacing
''
''
