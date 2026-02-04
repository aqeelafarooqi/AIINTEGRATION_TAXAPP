#!/usr/bin/env python3
"""
PDF Filler Utility for Backend
Generates editable PDFs from JSON data using PyMuPDF

ADAPTED FROM: Stage 3 pipeline (fill_pdf.py)
FOR: Django backend integration

FILE LOCATION: Place this file at the SAME level as views.py
Example: /path/to/django_app/pdf_filler.py (next to views.py)
"""

import fitz  # PyMuPDF
import os
from django.conf import settings

# PDF Templates directory (on server)
# This will be: /path/to/django_project/templates/pdf_blanks/
TEMPLATE_DIR = os.path.join(settings.BASE_DIR, 'templates', 'pdf_blanks')

# Template files (MUST be uploaded to server)
TEMPLATES = {
    'form_1040': 'f1040.pdf',
    'schedule_a': 'f1040sa.pdf',
    'schedule_b': 'f1040sb.pdf',
    'schedule_c': 'f1040sc.pdf',
    'schedule_d': 'f1040sd.pdf',
}

# Form ID to template mapping
# UPDATE THESE with actual form IDs from your database!
FORM_ID_TO_TEMPLATE = {
    16026: ('form_1040', 'f1040.pdf'),      # Form 1040
    # ADD MORE MAPPINGS:
    # 16027: ('schedule_a', 'f1040sa.pdf'),   # Schedule A
    # 16028: ('schedule_b', 'f1040sb.pdf'),   # Schedule B
    # 16029: ('schedule_c', 'f1040sc.pdf'),   # Schedule C
    # 16030: ('schedule_d', 'f1040sd.pdf'),   # Schedule D
}

# Form 1040 Manual Mappings
# These are verified field paths in the official IRS PDF
FORM_1040_MAPPINGS = {
    # Taxpayer info
    'first_name': 'topmostSubform[0].Page1[0].f1_14[0]',
    'last_name': 'topmostSubform[0].Page1[0].f1_18[0]',
    'ssn': 'topmostSubform[0].Page1[0].f1_16[0]',
    
    # Income lines (Line numbers from Form 1040)
    '1a': 'topmostSubform[0].Page1[0].f1_47[0]',      # W-2 wages
    '1z': 'topmostSubform[0].Page1[0].f1_73[0]',      # Total wages (calculated)
    '2a': 'topmostSubform[0].Page1[0].f1_58[0]',      # Tax-exempt interest
    '9': 'topmostSubform[0].Page1[0].f1_73[0]',       # Total income (calculated)
    '11': 'topmostSubform[0].Page1[0].f1_75[0]',      # AGI (calculated)
    
    # ADD MORE MAPPINGS as needed...
    # See LINE_NUMBERS_MAP.pdf for full field paths
}


def fill_form_1040(data, grey_out_calculated=True):
    """
    Fill Form 1040 using manual field mappings
    
    Args:
        data (dict): JSON data with structure:
            {
                "taxpayer": {
                    "first_name": "sid",
                    "last_name": "garg",
                    "ssn": "123-45-6789",
                    ...
                },
                "fields": {
                    "1a": {
                        "value": "50000",
                        "label": "Total amount from Form(s) W-2...",
                        "ftype": "number",
                        "can_be_modified": true
                    },
                    "1z": {
                        "value": "50000",
                        "can_be_modified": false  # This gets greyed out!
                    },
                    ...
                }
            }
        grey_out_calculated (bool): If True, grey out fields where can_be_modified=False
    
    Returns:
        bytes: PDF file content (editable PDF with form fields)
    """
    # Load blank template
    template_path = os.path.join(TEMPLATE_DIR, TEMPLATES['form_1040'])
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found: {template_path}")
    
    doc = fitz.open(template_path)
    page = doc[0]
    
    filled_count = 0
    grey_count = 0
    
    # Get data
    taxpayer = data.get('taxpayer', {})
    fields_data = data.get('fields', {})
    
    # Fill taxpayer name and SSN
    name_ssn_mappings = {
        'first_name': taxpayer.get('first_name', ''),
        'last_name': taxpayer.get('last_name', ''),
        'ssn': taxpayer.get('ssn', ''),
    }
    
    # Fill all fields
    for field_key, pdf_field_name in FORM_1040_MAPPINGS.items():
        # Check if it's taxpayer info or field data
        if field_key in name_ssn_mappings:
            value = name_ssn_mappings[field_key]
            can_modify = True
        elif field_key in fields_data:
            field_info = fields_data[field_key]
            value = field_info.get('value')
            can_modify = field_info.get('can_be_modified', True)
        else:
            continue
        
        # Skip null or empty values
        if value is None or value == '':
            continue
        
        # Find and fill the widget
        for widget in page.widgets():
            if widget.field_name == pdf_field_name:
                widget.field_value = str(value)
                widget.update()
                filled_count += 1
                
                # Grey out if it's a calculated field (can_be_modified=false)
                if grey_out_calculated and not can_modify:
                    widget.field_flags |= fitz.PDF_FIELD_IS_READ_ONLY
                    widget.fill_color = (0.9, 0.9, 0.9)  # Light grey background
                    widget.update()
                    grey_count += 1
                
                break
    
    # Return PDF as bytes
    pdf_bytes = doc.tobytes()
    doc.close()
    
    return pdf_bytes


def fill_schedule(data, form_name, grey_out_calculated=True):
    """
    Fill Schedule A/B/C/D using sequential mapping
    
    Schedules use sequential field numbering (f1_3, f1_4, f1_5, ...)
    First two fields are always name and SSN
    
    Args:
        data (dict): Same structure as fill_form_1040
        form_name (str): 'schedule_a', 'schedule_b', 'schedule_c', or 'schedule_d'
        grey_out_calculated (bool): If True, grey out calculated fields
    
    Returns:
        bytes: PDF file content
    """
    # Load blank template
    template_path = os.path.join(TEMPLATE_DIR, TEMPLATES[form_name])
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found: {template_path}")
    
    doc = fitz.open(template_path)
    page = doc[0]
    
    filled_count = 0
    grey_count = 0
    
    taxpayer = data.get('taxpayer', {})
    fields_data = data.get('fields', {})
    
    # Get all widgets and create short name mapping
    all_widgets = list(page.widgets())
    field_path_map = {}
    
    for widget in all_widgets:
        full_name = widget.field_name
        if '.f1_' in full_name or '.c1_' in full_name:
            parts = full_name.split('.')
            short_name = parts[-1]  # e.g., "f1_3[0]"
            field_path_map[short_name] = widget
    
    # Determine field naming pattern
    uses_leading_zeros = (form_name == 'schedule_b')
    
    # Fill name and SSN (first two fields)
    name_field = 'f1_01[0]' if uses_leading_zeros else 'f1_1[0]'
    ssn_field = 'f1_02[0]' if uses_leading_zeros else 'f1_2[0]'
    
    full_name_value = f"{taxpayer.get('first_name', '')} {taxpayer.get('last_name', '')}".strip()
    ssn = taxpayer.get('ssn', '')
    
    if name_field in field_path_map and full_name_value:
        field_path_map[name_field].field_value = full_name_value
        field_path_map[name_field].update()
        filled_count += 1
    
    if ssn_field in field_path_map and ssn:
        field_path_map[ssn_field].field_value = ssn
        field_path_map[ssn_field].update()
        filled_count += 1
    
    # Fill data fields sequentially
    for field_num, field_info in fields_data.items():
        value = field_info.get('value')
        can_modify = field_info.get('can_be_modified', True)
        
        if value is None or value == '':
            continue
        
        # Generate possible field names
        possible_fields = []
        if '_' in field_num:
            possible_fields.append(f'f1_{field_num}[0]')
        elif uses_leading_zeros and field_num.replace('.', '').isdigit():
            try:
                num = int(float(field_num))
                possible_fields.append(f'f1_{num:02d}[0]')
            except:
                possible_fields.append(f'f1_{field_num}[0]')
        else:
            possible_fields.append(f'f1_{field_num}[0]')
        
        # Try to find and fill
        for pdf_field in possible_fields:
            if pdf_field in field_path_map:
                widget = field_path_map[pdf_field]
                widget.field_value = str(value)
                widget.update()
                filled_count += 1
                
                # Grey out if calculated
                if grey_out_calculated and not can_modify:
                    widget.field_flags |= fitz.PDF_FIELD_IS_READ_ONLY
                    widget.fill_color = (0.9, 0.9, 0.9)
                    widget.update()
                    grey_count += 1
                
                break
    
    # Return PDF as bytes
    pdf_bytes = doc.tobytes()
    doc.close()
    
    return pdf_bytes


def generate_form_pdf(form_instance):
    """
    Main function to generate editable PDF for any form
    
    This is called by the Django view to generate PDFs
    
    Args:
        form_instance: Django model instance with:
            - id: Form ID (e.g., 16026 for Form 1040)
            - name: Form name (e.g., "FORM 1040")
            - data: JSON field containing taxpayer and fields data
    
    Returns:
        bytes: PDF file content (editable PDF)
    
    Raises:
        ValueError: If form type is unknown
        FileNotFoundError: If PDF template is missing
    """
    # Get form type from form ID
    form_id = form_instance.id
    
    if form_id not in FORM_ID_TO_TEMPLATE:
        raise ValueError(f"Unknown form ID: {form_id}. Please add mapping in FORM_ID_TO_TEMPLATE")
    
    form_type, template_file = FORM_ID_TO_TEMPLATE[form_id]
    
    # Get JSON data from form instance
    data = form_instance.data
    
    # Validate data structure
    if not isinstance(data, dict):
        raise ValueError("form_instance.data must be a dictionary")
    
    if 'taxpayer' not in data:
        raise ValueError("data missing 'taxpayer' key")
    
    if 'fields' not in data:
        raise ValueError("data missing 'fields' key")
    
    # Route to appropriate filler
    if form_type == 'form_1040':
        return fill_form_1040(data)
    elif form_type in ['schedule_a', 'schedule_b', 'schedule_c', 'schedule_d']:
        return fill_schedule(data, form_type)
    else:
        raise ValueError(f"Unknown form type: {form_type}")
