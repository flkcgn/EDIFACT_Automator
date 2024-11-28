import streamlit as st
import pandas as pd
import io
from parser import parse_segment, assign_hierarchy, validate_input_file

st.set_page_config(
    page_title="EDIFACT Specification Automation",
    page_icon="📊",
    layout="wide"
)

def process_file(uploaded_file):
    try:
        # Read the uploaded file
        df = pd.read_csv(uploaded_file, encoding='utf-8')
        
        # Validate the input file
        validation_result = validate_input_file(df)
        if not validation_result['valid']:
            st.error(f"Validation Error: {validation_result['message']}")
            return None
            
        # Process each row
        processed_data = []
        progress_bar = st.progress(0)
        
        for idx, row in df.iterrows():
            # Parse segment
            parsed_segment = parse_segment(row)
            # Assign hierarchy
            hierarchy_data = assign_hierarchy(parsed_segment)
            processed_data.append(hierarchy_data)
            
            # Update progress
            progress_bar.progress((idx + 1) / len(df))
            
        # Create output DataFrame
        columns = ['M/C/X', 'HL1', 'HL2', 'HL3', 'HL4', 'HL5', 'HL6', 
                  'Name', 'M/C Std', 'Max-Use', 'Note']
        result_df = pd.DataFrame(processed_data, columns=columns)
        
        return result_df
        
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None

def main():
    st.title("EDIFACT Specification Automation")
    
    st.write("""
    Upload your GS1 standard segments file to generate a hierarchical specification.
    The file should be in CSV format with UTF-8 encoding.
    """)
    
    uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])
    
    if uploaded_file is not None:
        st.info("Processing file...")
        
        result_df = process_file(uploaded_file)
        
        if result_df is not None:
            st.success("File processed successfully!")
            
            # Display preview
            st.subheader("Preview of processed data")
            st.dataframe(result_df.head())
            
            # Generate download link
            csv = result_df.to_csv(index=False)
            csv_bytes = csv.encode('utf-8')
            
            st.download_button(
                label="Download processed file",
                data=csv_bytes,
                file_name="output_specification.csv",
                mime="text/csv"
            )
            
            # Display statistics
            st.subheader("Processing Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Segments", len(result_df))
            with col2:
                st.metric("Mandatory Segments", len(result_df[result_df['M/C/X'] == 'M']))
            with col3:
                st.metric("Conditional Segments", len(result_df[result_df['M/C/X'] == 'C']))

if __name__ == "__main__":
    main()
