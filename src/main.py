import streamlit as st
import pandas as pd
import io
from parser import parse_edi_message

st.set_page_config(
    page_title="EDIFACT Specification Automation",
    page_icon="📊",
    layout="wide"
)

def process_file(uploaded_file):
    try:
        # Read the uploaded EDI file with proper error handling
        if uploaded_file is None:
            st.error("No file uploaded")
            return None
            
        try:
            content = uploaded_file.getvalue().decode('utf-8')
        except UnicodeDecodeError:
            try:
                content = uploaded_file.getvalue().decode('latin-1')
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
                return None
                
        if not content.strip():
            st.error("File is empty")
            return None
            
        # Process the EDI content
        processed_data = parse_edi_message(content)
        
        if not processed_data:
            st.error("No valid EDIFACT segments found in the file")
            return None
            
        # Create output DataFrame
        columns = ['M/C/X', 'HL1', 'HL2', 'HL3', 'HL4', 'HL5', 'HL6', 
                  'Name', 'M/C Std', 'Max-Use', 'Note']
        result_df = pd.DataFrame(processed_data, columns=columns)
        
        return result_df
        
    except Exception as e:
        st.error(f"Error processing EDI file: {str(e)}")
        return None

def main():
    st.title("EDIFACT Specification Automation")
    
    st.write("""
    Upload your EDIFACT message file to generate a hierarchical specification.
    The file should be in .edi format with UTF-8 or Latin-1 encoding.
    Maximum file size: 10MB
    """)
    
    uploaded_file = st.file_uploader("Choose an EDI file", type=['edi'])
    
    if uploaded_file is not None:
        # Check file size (limit to 10MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            st.error("File size too large. Please upload a file smaller than 10MB")
            return
            
        st.info("Processing EDIFACT message...")
        
        result_df = process_file(uploaded_file)
        
        if result_df is not None:
            st.success("EDIFACT message processed successfully!")
            
            # Display preview
            st.subheader("Preview of processed segments")
            st.dataframe(result_df)
            
            # Generate download link
            csv = result_df.to_csv(index=False)
            csv_bytes = csv.encode('utf-8')
            
            st.download_button(
                label="Download specification CSV",
                data=csv_bytes,
                file_name="edifact_specification.csv",
                mime="text/csv"
            )
            
            # Display statistics
            st.subheader("Message Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Segments", len(result_df))
            with col2:
                st.metric("Mandatory Segments", len(result_df[result_df['M/C/X'] == 'M']))
            with col3:
                st.metric("Conditional Segments", len(result_df[result_df['M/C/X'] == 'C']))

if __name__ == "__main__":
    main()
