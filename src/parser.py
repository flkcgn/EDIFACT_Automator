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
    Returns the description for a given segment code using official GS1 EANCOM standard names.
    Source: GS1 EANCOM documentation
    """
    descriptions = {
        'UNH': 'Message Header - To head, identify and specify a message',
        'BGM': 'Beginning of Message - To indicate the beginning of a message and to transmit identifying number',
        'DTM': 'Date/Time/Period - To specify date, time or period',
        'RFF': 'Reference - To specify a reference',
        'NAD': 'Name and Address - To specify the name/address and their related function',
        'CTA': 'Contact Information - To identify a person or department to whom communication should be directed',
        'COM': 'Communication Contact - To identify a communication number of a person or department',
        'TAX': 'Duty/Tax/Fee Details - To specify relevant duty/tax/fee information',
        'CUX': 'Currencies - To specify currencies used in the transaction',
        'PAT': 'Payment Terms Basis - To specify the payment terms basis',
        'LIN': 'Line Item - To identify a line item and specify its configuration',
        'PIA': 'Additional Product ID - To specify additional or substitutional item identification codes',
        'IMD': 'Item Description - To describe an item in free form or coded format',
        'QTY': 'Quantity - To specify a pertinent quantity',
        'PRI': 'Price Details - To specify price information',
        'MOA': 'Monetary Amount - To specify a monetary amount',
        'UNS': 'Section Control - To separate header, detail and summary sections',
        'CNT': 'Control Total - To provide control total',
        'UNT': 'Message Trailer - To end and check the completeness of a message'
    }
    return descriptions.get(segment_code, 'Unknown Segment')

def determine_segment_status(segment_code: str) -> str:
    """
    Determines if a segment is mandatory or conditional based on GS1 EANCOM standard.
    """
    # Updated according to GS1 EANCOM standard
    mandatory_segments = {
        'UNH',  # Message header
        'BGM',  # Beginning of message
        'LIN',  # Line item
        'QTY',  # Quantity
        'UNT'   # Message trailer
    }
    return 'Mandatory' if segment_code in mandatory_segments else 'Conditional'

def assign_hierarchy(segment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assigns hierarchy levels based on segment data and EDIFACT message structure.
    Uses full segment descriptions in the Name field.
    """
    hierarchy = {
        'M/C/X': '',  # Left empty for user input
        'HL1': '',
        'HL2': '',
        'HL3': '',
        'HL4': '',
        'HL5': '',
        'HL6': '',
        'Name': segment_data['description'],  # Using full description instead of segment code
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
