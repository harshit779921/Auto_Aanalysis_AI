import sqlite3 
from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai
import pandas as pd
import matplotlib.pyplot as plt

# Load environment variables
load_dotenv()

# Configure Genai Key
#genai_key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Set page configuration
st.set_page_config(page_title="I can Retrieve Any SQL query")

# Function to Load Google Gemini Model and provide queries as response
def get_gemini_response(question, prompt):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content([prompt[0], question])
    return response.text

# Function to retrieve query from the database
def read_sql_query(sql, db):
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        print("Executing SQL query:", sql)  # Print SQL query
        cur.execute(sql)
        rows = cur.fetchall()
        conn.commit()
        conn.close()
        return rows
    except Exception as e:
        print("Error executing SQL query:", e)
        return None

# Add file uploader widget
uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

# Initialize df as None
df = None

# Initialize SessionState for managing database deletion
class SessionState:
    delete_database = False

state = SessionState()

# Read uploaded CSV file into DataFrame
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Display the contents of the uploaded CSV file
    st.subheader("Uploaded CSV file:")
    st.write(df)

    # Convert DataFrame to SQLite database
    st.subheader("Converting CSV to SQLite database...")

    # Connect to SQLite database
    conn = sqlite3.connect("uploaded_data.db")

    # Write DataFrame to SQLite database
    df.to_sql("data", conn, index=False, if_exists="replace")

    # Close the database connection
    conn.close()

    st.success("CSV file converted to SQLite database successfully!")

    # Convert DataFrame columns to a string
    columns_str = ', '.join(df.columns)

    # Define Your Prompt based on the columns in the CSV file
    prompt = [
        f"""
        You are an expert in converting English questions to SQL query!
        The SQL database has the name 'data' and has the following columns - {columns_str}
        
        For example,
        - How many entries of records are present? (SQL command: SELECT COUNT(*) FROM data;)
        - Make a graph between price and sqft_living (SQL command: SELECT price, sqft_living FROM data;)
        
        Note: The SQL code should not have triple backticks in the beginning or end, and the output should not contain the word 'sql'.
        """
    ]

# Streamlit App
st.header("Gemini App To Retrieve SQL Data")

# User input for the question
question = st.text_input("Input: ", key="input")

# Button to submit the question
submit = st.button("Ask the question")

# When submit button is clicked
if submit:
    # Generate response using Gemini model
    response = get_gemini_response(question, prompt)
    
    # Retrieve data from the database
    df = pd.DataFrame(read_sql_query(response, "uploaded_data.db"))
    
    # Display the response
    st.subheader("The Response is")
    st.dataframe(df)

    # Check if data is suitable for visualization
   # Check if data is suitable for visualization
    if not df.empty:
        numeric_columns = df.select_dtypes(include=['int', 'float']).columns
        if len(numeric_columns) > 0:
            st.subheader("Visualization")
            chart_type = st.selectbox("Select a chart type", options=["Bar Chart","Line Chart" , "Histogram"])
            column = st.selectbox("Select a column for visualization", options=numeric_columns)
            
            # Check if selected column is not empty
            if not df[column].empty:
                if chart_type == "Line Chart":
                    st.line_chart(df[column])
                elif chart_type == "Bar Chart":
                    st.bar_chart(df[column])
                elif chart_type == "Histogram":
                    st.pyplot(plt.hist(df[column]))
                elif chart_type == "Pie Chart":
                    plt.pie(df[column].value_counts(), labels=df[column].unique())
                    st.pyplot()    
            else:
                st.warning("Selected column is empty.")
        else:
            st.warning("No numerical columns found for visualization.")
    else:
        st.warning("No data retrieved from the database.")



# Input components to manually enter additional data
st.header("Enter Additional Data Manually")
num_additional_rows = st.number_input("Number of additional rows to add", value=1, min_value=1)

additional_data = {}
if df is not None:
    for i in range(num_additional_rows):
        st.subheader(f"Row {i+1}")
        for col in df.columns:
            additional_data[col] = st.text_input(f"{col}:", key=f"{col}_{i}")

# Button to append additional data
if st.button("Add Additional Data"):
    if df is not None:
        # Convert additional data to DataFrame and append to SQLite database
        additional_df = pd.DataFrame([additional_data])
        conn = sqlite3.connect("uploaded_data.db")
        additional_df.to_sql("data", conn, if_exists="append", index=False)
        conn.close()
        st.success("Additional data appended to the SQLite database successfully!")
    else:
        st.warning("Please upload a CSV file first to add additional data.")
  
# Checkbox to delete database
state.delete_database = st.checkbox("Delete database when closing the app")

# Delete database when closing the app
if state.delete_database:
    os.remove("uploaded_data.db")
