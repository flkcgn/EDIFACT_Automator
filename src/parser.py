import pandas as pd
from typing import Dict, List, Any, Tuple
import re

class EDIFACTParser:
    def __init__(self):
        self.component_separator = ':'
        self.data_separator = '+'
        self.decimal_point = '.'
        self.release_char = '?'
        self.segment_terminator = "'"
        self.segment_sequence = []
        
    def set_separators(self, una_segment: str = None):
        """Set EDIFACT separators based on UNA segment or defaults"""
        if una_segment and una_segment.startswith('UNA'):
            self.component_separator = una_segment[3]
            self.data_separator = una_segment[4]
            self.decimal_point = una_segment[5]
            self.release_char = una_segment[6]
            self.segment_terminator = una_segment[8]

def read_edi_file(file_content: str) -> Tuple[EDIFACTParser, List[str]]:
    """
    Reads an EDI file and splits it into segments, handling UNA segment if present.
    Returns parser instance and list of segments.
    """
    parser = EDIFACTParser()
    
    # Clean content
    content = file_content.replace('\n', '').replace('\r', '')
    
    # Check for UNA segment and set separators
    una_match = re.match(r'UNA.{6}', content)
    if una_match:
        una_segment = una_match.group(0)
        parser.set_separators(una_segment)
        content = content[9:]  # Remove UNA segment
    
    # Split segments using segment terminator
    segments = [s.strip() for s in content.split(parser.segment_terminator) if s.strip()]
    return parser, segments

def parse_edi_segment(segment: str, parser: EDIFACTParser) -> Dict[str, Any]:
    elements = segment.split(parser.data_separator)
    segment_code = elements[0].strip()
    
    segment_data = {
        'segment_code': segment_code,
        'description': get_segment_description(segment_code),
        'status': determine_segment_status(segment_code),
        'max_use': determine_max_use(segment_code),
        'note': '',
        'elements': elements[1:] if len(elements) > 1 else []
    }
    
    return segment_data

def determine_max_use(segment_code: str) -> str:
    """Determines maximum usage of a segment based on EDIFACT rules"""
    # Default max use values based on EDIFACT standards
    max_use_rules = {
        'UNA': '1',
        'UNB': '1',
        'UNH': '1',
        'UNT': '1',
        'UNZ': '1',
        'BGM': '1',
        'DTM': '9',  # Common max use for date/time segments
        'NAD': '9',  # Multiple parties allowed
        'LIN': '999999',  # Line items can repeat many times
        'RFF': '9',  # References can repeat
    }
    return max_use_rules.get(segment_code, '1')

def validate_envelope_structure(segments: List[Dict[str, Any]]) -> bool:
    if not segments:
        return False
    return True

def get_segment_description(segment_code: str) -> str:
    """
    Returns the description for a given segment code using official GS1 EANCOM standard names.
    Source: GS1 EANCOM documentation
    """
    descriptions = {
        # Service segments
        'UNA': 'Service String Advice - To define the characters selected for use as delimiters and indicators',
        'UNB': 'Interchange Header - To start, identify and specify an interchange',
        'UNH': 'Message Header - To head, identify and specify a message',
        'UNT': 'Message Trailer - To end and check the completeness of a message',
        'UNZ': 'Interchange Trailer - To end and check the completeness of an interchange',
        
        # CONTRL-specific segments
        'UCI': 'Interchange Response - To start, identify and specify an interchange response',
        'UCM': 'Message Response - To identify a message in the interchange and specify the action taken',
        'UCS': 'Segment Error Indication - To identify a segment containing an error',
        'UCD': 'Data Element Error Indication - To identify an error in a specified data element',
        
        # Common segments
        'BGM': 'Beginning of Message - To indicate the type and function of a message',
        'DTM': 'Date/Time/Period - To specify dates, times, periods, and their formats',
        'RFF': 'Reference - To specify a reference that applies to the message',
        'NAD': 'Name and Address - To specify the name and address of a party',
        'LIN': 'Line Item - To identify a line item and specify its configuration',
        'PIA': 'Additional Product ID - To specify additional product identification',
        'IMD': 'Item Description - To describe an item in free form or coded format',
        'QTY': 'Quantity - To specify a pertinent quantity',
        'UNS': 'Section Control - To separate header, detail and summary sections',
        'CNT': 'Control Total - To provide control total',
    }
    return descriptions.get(segment_code, 'Unknown Segment')

def determine_segment_status(segment_code: str) -> str:
    """
    Determines if a segment is mandatory or conditional based on GS1 EANCOM standard.
    """
    mandatory_segments = {
        'UNB',  # Interchange header
        'UNH',  # Message header
        'BGM',  # Beginning of message
        'UNT',  # Message trailer
        'UNZ'   # Interchange trailer
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
        'Name': segment_data['description'],
        'M/C Std': segment_data['status'],
        'Max-Use': segment_data['max_use'],
        'Note': segment_data['note']
    }
    
    segment_code = segment_data['segment_code']
    
    # Enhanced hierarchy assignment based on EDIFACT structure
    if segment_code in ['UNA', 'UNB']:
        hierarchy['HL1'] = segment_code
    elif segment_code == 'UNH':
        hierarchy['HL1'] = 'UNB'
        hierarchy['HL2'] = segment_code
    elif segment_code == 'BGM':
        hierarchy['HL1'] = 'UNB'
        hierarchy['HL2'] = 'UNH'
        hierarchy['HL3'] = segment_code
    elif segment_code in ['DTM', 'RFF']:
        hierarchy['HL1'] = 'UNB'
        hierarchy['HL2'] = 'UNH'
        hierarchy['HL3'] = 'BGM'
        hierarchy['HL4'] = segment_code
    elif segment_code in ['NAD', 'CTA', 'COM']:
        hierarchy['HL1'] = 'UNB'
        hierarchy['HL2'] = 'UNH'
        hierarchy['HL4'] = segment_code
    elif segment_code in ['LIN', 'PIA', 'IMD', 'QTY']:
        hierarchy['HL1'] = 'UNB'
        hierarchy['HL2'] = 'UNH'
        hierarchy['HL5'] = 'LIN'
        hierarchy['HL6'] = segment_code
    elif segment_code in ['UNT', 'UNZ']:
        hierarchy['HL1'] = 'UNB'
        hierarchy['HL2'] = 'UNH'
        
    return hierarchy

def parse_edi_message(content: str) -> List[Dict[str, Any]]:
    """
    Parses a complete EDI message and returns structured data with validation.
    """
    try:
        parser, segments = read_edi_file(content)
        parsed_data = []
        
        for segment in segments:
            if segment.strip():  # Skip empty segments
                try:
                    segment_data = parse_edi_segment(segment, parser)
                    parser.segment_sequence.append(segment_data['segment_code'])
                    hierarchy_data = assign_hierarchy(segment_data)
                    parsed_data.append(hierarchy_data)
                except Exception as e:
                    raise ValueError(f"Error parsing segment '{segment}': {str(e)}")
        
        # Validate envelope structure
        if not validate_envelope_structure(parsed_data):
            raise ValueError("Invalid EDIFACT envelope structure")
        
        return parsed_data
    except Exception as e:
        raise ValueError(f"Error processing EDI file: {str(e)}")
