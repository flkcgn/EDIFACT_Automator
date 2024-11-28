import streamlit as st
import pandas as pd
from parser import get_segment_description, determine_segment_status, determine_max_use, assign_hierarchy

def generate_standard_segments(message_type: str) -> list:
    """Generate standard segments based on message type"""
    segments = {
        'INVOIC': ['UNB', 'UNH', 'BGM', 'DTM', 'NAD', 'CUX', 'LIN', 'QTY', 'MOA', 'UNS', 'CNT', 'UNT', 'UNZ'],
        'CONTRL': ['UNB', 'UNH', 'UCI', 'UCM', 'UCS', 'UCD', 'UNT', 'UNZ']
    }
    
    result = []
    for segment_code in segments.get(message_type, []):
        segment_data = {
            'segment_code': segment_code,
            'description': get_segment_description(segment_code),
            'status': determine_segment_status(segment_code, message_type),
            'max_use': determine_max_use(segment_code),
            'note': '',
            'elements': []
        }
        hierarchy_data = assign_hierarchy(segment_data)
        result.append(hierarchy_data)
    return result

def main():
    st.title("EDIFACT Specification Automation")
    
    st.write("""
    Select a message type to generate its standard segment specification.
    The table will show the hierarchical structure and segment details.
    """)
    
    # Message type selection
    message_type = st.selectbox(
        "Select Message Type",
        options=['INVOIC', 'CONTRL'],
        format_func=lambda x: f"{x} - {'Invoice' if x == 'INVOIC' else 'Control'} Message"
    )
    
    if message_type:
        st.info(f"Generating specification for {message_type} message type...")
        
        # Generate segments based on selected message type
        result_data = generate_standard_segments(message_type)
        
        if result_data:
            # Create DataFrame with the specified columns
            columns = ['M/C/X', 'HL1', 'HL2', 'HL3', 'HL4', 'HL5', 'HL6', 
                      'Name', 'M/C Std', 'Max-Use', 'Note']
            result_df = pd.DataFrame(result_data, columns=columns)
            
            # Display preview
            st.subheader("Message Specification")
            st.dataframe(result_df)
            
            # Generate download link
            csv = result_df.to_csv(index=False)
            csv_bytes = csv.encode('utf-8')
            
            st.download_button(
                label="Download specification CSV",
                data=csv_bytes,
                file_name=f"{message_type.lower()}_specification.csv",
                mime="text/csv"
            )
            
            # Display statistics
            st.subheader("Message Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Segments", len(result_df))
            with col2:
                st.metric("Mandatory Segments", len(result_df[result_df['M/C Std'] == 'Mandatory']))
            with col3:
                st.metric("Conditional Segments", len(result_df[result_df['M/C Std'] == 'Conditional']))

if __name__ == "__main__":
    main()