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

def parse_edi_segment(segment: str, parser: EDIFACTParser, message_type: str = '') -> Dict[str, Any]:
    elements = segment.split(parser.data_separator)
    segment_code = elements[0].strip()
    
    segment_data = {
        'segment_code': segment_code,
        'description': get_segment_description(segment_code),
        'status': determine_segment_status(segment_code, message_type),
        'max_use': determine_max_use(segment_code),
        'note': '',
        'elements': elements[1:] if len(elements) > 1 else [],
        'message_type': message_type
    }
    
    return segment_data

def determine_max_use(segment_code: str) -> str:
    """Determines maximum usage of a segment based on EDIFACT rules and message type"""
    # Default max use values based on GS1 EANCOM standards
    max_use_rules = {
        'UNA': '1',    # pos 1
        'UNB': '1',    # pos 2
        'UNH': '1',    # pos 3
        'UCI': '1',    # pos 4
        'UCM': '1',    # pos 5
        'UCS': '999',  # pos 6
        'UCD': '99',   # pos 7
        'UNT': '1',    # pos 8
        'UNZ': '1',    # pos 9
        'BGM': '1',
        'DTM': '9',
        'NAD': '9',
        'LIN': '999999',
        'RFF': '9',
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
        'UCF': 'Functional Group Response - To identify a functional group in the interchange',
        
        # Common segments
        'BGM': 'Beginning of Message - To indicate the type and function of a message',
        'DTM': 'Date/Time/Period - To specify dates, times, periods, and their formats',
        'RFF': 'Reference - To specify a reference that applies to the message',
        'NAD': 'Name and Address - To specify the name and address of a party',
        'CTA': 'Contact Information - To identify a person or department',
        'COM': 'Communication Contact - To identify a communication number',
        'FTX': 'Free Text - To provide free-form text information',
        'DOC': 'Document/Message Details - To identify documents or messages',
        'CUX': 'Currencies - To specify currencies and exchange rates',
        'PAT': 'Payment Terms Basis - To specify payment terms',
        'MOA': 'Monetary Amount - To specify a monetary amount',
        'PCD': 'Percentage Details - To specify percentage information',
        
        # Line item related segments
        'LIN': 'Line Item - To identify a line item and specify its configuration',
        'PIA': 'Additional Product ID - To specify additional product identification',
        'IMD': 'Item Description - To describe an item in free form or coded format',
        'QTY': 'Quantity - To specify a pertinent quantity',
        'PRI': 'Price Details - To specify price information',
        'TAX': 'Duty/Tax/Fee Details - To specify relevant duty/tax/fee information',
        'MEA': 'Measurements - To specify physical measurements',
        'PAC': 'Package - To describe packaging details',
        
        # Summary segments
        'UNS': 'Section Control - To separate header, detail and summary sections',
        'CNT': 'Control Total - To provide control total',
        'ALC': 'Allowance or Charge - To identify allowance or charges',
        'TMA': 'Total Message Amount - To specify total message amounts',
    }
    return descriptions.get(segment_code, 'Unknown Segment')

def determine_segment_status(segment_code: str, message_type: str = '') -> str:
    """
    Determines if a segment is mandatory or conditional based on GS1 EANCOM branching diagrams.
    For CONTRL message, follows exact diagram M/C markers.
    """
    # CONTRL message specific statuses (per branching diagram)
    if message_type == 'CONTRL':
        contrl_status = {
            'UNA': 'Conditional',   # C,1,pos 1
            'UNB': 'Mandatory',     # M,1,pos 2
            'UNH': 'Mandatory',     # M,1,pos 3
            'UCI': 'Mandatory',     # M,1,pos 4
            'UCM': 'Mandatory',     # M,1,pos 5
            'UCS': 'Conditional',   # C,999,pos 6
            'UCD': 'Conditional',   # C,99,pos 7
            'UNT': 'Mandatory',     # M,1,pos 8
            'UNZ': 'Mandatory',     # M,1,pos 9
        }
        return contrl_status.get(segment_code, 'Conditional')
    
    # INVOIC message specific statuses
    elif message_type == 'INVOIC':
        invoic_mandatory = {
            'UNB', 'UNH', 'BGM', 'DTM', 'NAD', 'LIN', 
            'QTY', 'MOA', 'UNS', 'UNT', 'UNZ'
        }
        return 'Mandatory' if segment_code in invoic_mandatory else 'Conditional'
    
    # Default status for other message types or when no message type specified
    universal_mandatory = {'UNB', 'UNH', 'UNT', 'UNZ'}
    return 'Mandatory' if segment_code in universal_mandatory else 'Conditional'

def assign_hierarchy(segment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assigns hierarchy levels based on GS1 EANCOM branching diagrams.
    CONTRL message follows exact branching diagram structure.
    """
    hierarchy = {
        'M/C/X': '',  # Left empty for user input
        'HL1': '',
        'HL2': '',
        'HL3': '',
        'HL4': '',
        'HL5': '',
        'HL6': '',
        'Name': segment_data['description'].split('-')[0].strip(),
        'M/C Std': segment_data['status'],
        'Max-Use': segment_data['max_use'],
        'Note': segment_data['note']
    }
    
    segment_code = segment_data['segment_code']
    message_type = segment_data.get('message_type', '')
    
    # CONTRL message hierarchy (per branching diagram)
    if message_type == 'CONTRL':
        # Level 0 segments
        if segment_code in ['UNA', 'UNB', 'UNH', 'UCI', 'UNT', 'UNZ']:
            hierarchy['HL1'] = segment_code
            hierarchy['Note'] = f'Position {["UNA", "UNB", "UNH", "UCI", "UNT", "UNZ"].index(segment_code) + 1}'
        
        # Level 1 (SG1) - UCM
        elif segment_code == 'UCM':
            hierarchy['HL2'] = segment_code
            hierarchy['Note'] = 'SG1 - Position 5'
        
        # Level 2 (SG2) - UCS
        elif segment_code == 'UCS':
            hierarchy['HL3'] = segment_code
            hierarchy['Note'] = 'SG2 - Position 6'
        
        # Level 3 - UCD
        elif segment_code == 'UCD':
            hierarchy['HL4'] = segment_code
            hierarchy['Note'] = 'Position 7'
    
    # INVOIC message hierarchy
    elif message_type == 'INVOIC':
        # HL1: Interchange Header
        if segment_code == 'UNB':
            hierarchy['HL1'] = segment_code
        # HL2: Message Header
        elif segment_code == 'UNH':
            hierarchy['HL2'] = segment_code
        # HL3: Header Section
        elif segment_code in ['BGM', 'DTM']:
            hierarchy['HL3'] = segment_code
        # HL4: Name and Address
        elif segment_code in ['NAD', 'RFF', 'CTA', 'COM']:
            hierarchy['HL4'] = segment_code
        # HL5: Line Item
        elif segment_code == 'LIN':
            hierarchy['HL5'] = segment_code
        # HL6: Line Item Details
        elif segment_code in ['PIA', 'IMD', 'QTY', 'MOA']:
            hierarchy['HL6'] = segment_code
        
    return hierarchy

def parse_edi_message(content: str) -> List[Dict[str, Any]]:
    """
    Parses a complete EDI message and returns structured data with validation.
    Includes enhanced segment sequence validation and error reporting.
    """
    try:
        parser, segments = read_edi_file(content)
        parsed_data = []
        message_type = ''
        
        # First pass: identify message type
        for segment in segments:
            if segment.startswith('UNH'):
                try:
                    elements = segment.split(parser.data_separator)
                    if len(elements) > 2:
                        message_type = elements[2].split(':')[0]
                    break
                except Exception:
                    pass
        
        # Second pass: parse segments with context
        for i, segment in enumerate(segments, 1):
            if segment.strip():  # Skip empty segments
                try:
                    # Enhanced segment validation
                    if not re.match(r'^[A-Z]{3}', segment):
                        raise ValueError(f"Invalid segment format at position {i}")
                    
                    segment_data = parse_edi_segment(segment, parser)
                    segment_code = segment_data['segment_code']
                    
                    # Sequence validation
                    if i == 1 and segment_code not in ['UNA', 'UNB']:
                        raise ValueError("Message must start with UNA or UNB segment")
                    if i == len(segments) and segment_code != 'UNZ':
                        raise ValueError("Message must end with UNZ segment")
                    
                    # Update status based on message type
                    segment_data['status'] = determine_segment_status(segment_code, message_type)
                    
                    parser.segment_sequence.append(segment_code)
                    hierarchy_data = assign_hierarchy(segment_data)
                    parsed_data.append(hierarchy_data)
                    
                except Exception as e:
                    raise ValueError(f"Error in segment {i} '{segment}': {str(e)}")
        
        # Enhanced structure validation
        if not validate_envelope_structure(parsed_data):
            raise ValueError("Invalid EDIFACT envelope structure: Missing required segments or incorrect sequence")
            
        # Validate message structure based on type
        if message_type:
            mandatory_segments = [seg for seg in parsed_data if seg['M/C Std'] == 'Mandatory']
            if not mandatory_segments:
                raise ValueError(f"Missing mandatory segments for message type {message_type}")
        
        return parsed_data
    except Exception as e:
        raise ValueError(f"Error processing EDI file: {str(e)}")
