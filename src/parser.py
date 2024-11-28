import pandas as pd
from typing import Dict, List, Any
import re

def read_edi_file(file_content: str) -> List[str]:
    """
    Reads an EDI file and splits it into segments.
    """
    # Remove newlines and split by segment terminator
    content = file_content.replace('\n', '').replace('\r', '')
    segments = content.split("'")
    return [s.strip() for s in segments if s.strip()]

def parse_edi_segment(segment: str) -> Dict[str, Any]:
    """
    Parses a single EDI segment into structured data.
    """
    # Split segment into elements (separator is typically +)
    elements = segment.split('+')
    segment_code = elements[0]
    
    segment_data = {
        'segment_code': segment_code,
        'description': get_segment_description(segment_code),
        'status': determine_segment_status(segment_code),
        'max_use': '1',  # Default value
        'note': '',
        'elements': elements[1:] if len(elements) > 1 else []
    }
    
    return segment_data

def get_segment_description(segment_code: str) -> str:
    """
    Returns the description for a given segment code using official GS1 standard names.
    """
    descriptions = {
        'UNH': 'Message Header',
        'BGM': 'Beginning of Message',
        'DTM': 'Date/Time/Period',
        'RFF': 'Reference',
        'NAD': 'Name and Address',
        'CTA': 'Contact Information',
        'COM': 'Communication Contact',
        'TAX': 'Duty/Tax/Fee Details',
        'CUX': 'Currencies',
        'PAT': 'Payment Terms Basis',
        'LIN': 'Line Item',
        'PIA': 'Additional Product ID',
        'IMD': 'Item Description',
        'QTY': 'Quantity',
        'PRI': 'Price Details',
        'MOA': 'Monetary Amount',
        'UNS': 'Section Control',
        'CNT': 'Control Total',
        'UNT': 'Message Trailer'
    }
    return descriptions.get(segment_code, 'Unknown Segment')

def determine_segment_status(segment_code: str) -> str:
    """
    Determines if a segment is mandatory or conditional based on common EDIFACT rules.
    """
    mandatory_segments = {'UNH', 'BGM', 'UNT', 'LIN'}
    return 'Mandatory' if segment_code in mandatory_segments else 'Conditional'

def assign_hierarchy(segment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assigns hierarchy levels based on segment data and EDIFACT message structure.
    """
    hierarchy = {
        'M/C/X': '',  # Left empty for user input
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
    
    # Assign hierarchy based on EDIFACT message structure
    segment_code = segment_data['segment_code']
    
    if segment_code == 'UNH':
        hierarchy['HL1'] = segment_code
    elif segment_code == 'BGM':
        hierarchy['HL1'] = 'UNH'
        hierarchy['HL2'] = segment_code
    elif segment_code in ['DTM', 'RFF']:
        hierarchy['HL1'] = 'UNH'
        hierarchy['HL2'] = 'BGM'
        hierarchy['HL3'] = segment_code
    elif segment_code in ['NAD', 'CTA', 'COM']:
        hierarchy['HL1'] = 'UNH'
        hierarchy['HL2'] = 'BGM'
        hierarchy['HL4'] = segment_code
    elif segment_code in ['LIN', 'PIA', 'IMD', 'QTY', 'PRI', 'MOA']:
        hierarchy['HL1'] = 'UNH'
        hierarchy['HL5'] = 'LIN'
        hierarchy['HL6'] = segment_code
    elif segment_code == 'UNT':
        hierarchy['HL1'] = 'UNH'
        hierarchy['HL2'] = segment_code
    
    return hierarchy

def parse_edi_message(content: str) -> List[Dict[str, Any]]:
    """
    Parses a complete EDI message and returns structured data.
    """
    segments = read_edi_file(content)
    parsed_data = []
    
    for segment in segments:
        if segment:  # Skip empty segments
            segment_data = parse_edi_segment(segment)
            hierarchy_data = assign_hierarchy(segment_data)
            parsed_data.append(hierarchy_data)
    
    return parsed_data
