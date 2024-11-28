import pandas as pd
from typing import Dict, List, Any

def validate_input_file(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validates the input CSV file format and content.
    """
    required_columns = ['Segment', 'Description', 'Status']
    
    # Check for required columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return {
            'valid': False,
            'message': f"Missing required columns: {', '.join(missing_columns)}"
        }
    
    # Check for empty rows
    if df.isnull().values.any():
        return {
            'valid': False,
            'message': "File contains empty cells"
        }
        
    return {'valid': True, 'message': ""}

def parse_segment(row: pd.Series) -> Dict[str, Any]:
    """
    Parses a single segment row into structured data.
    """
    segment_data = {
        'segment_code': row['Segment'],
        'description': row['Description'],
        'status': row['Status'],
        'max_use': '1',  # Default value
        'note': ''
    }
    
    # Extract M/C/X status
    if row['Status'].upper().startswith('M'):
        segment_data['m_c_x'] = 'M'
    elif row['Status'].upper().startswith('C'):
        segment_data['m_c_x'] = 'C'
    else:
        segment_data['m_c_x'] = 'X'
    
    return segment_data

def assign_hierarchy(segment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assigns hierarchy levels based on segment data.
    """
    # Initialize hierarchy levels
    hierarchy = {
        'M/C/X': segment_data['m_c_x'],
        'HL1': '',
        'HL2': '',
        'HL3': '',
        'HL4': '',
        'HL5': '',
        'HL6': '',
        'Name': segment_data['segment_code'],
        'M/C Std': segment_data['status'],
        'Max-Use': segment_data['max_use'],
        'Note': segment_data['note']
    }
    
    # Assign hierarchy based on segment code patterns
    segment_code = segment_data['segment_code']
    
    # Example hierarchy assignment logic
    if segment_code.startswith('UNH'):
        hierarchy['HL1'] = segment_code
    elif segment_code.startswith('BGM'):
        hierarchy['HL1'] = 'UNH'
        hierarchy['HL2'] = segment_code
    elif segment_code.startswith('DTM'):
        hierarchy['HL1'] = 'UNH'
        hierarchy['HL2'] = 'BGM'
        hierarchy['HL3'] = segment_code
    else:
        # Default assignment to HL3
        hierarchy['HL3'] = segment_code
    
    return hierarchy
