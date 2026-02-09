#!/usr/bin/env python3
"""
PDF Filler Utility for Backend
Generates editable PDFs from JSON data using PyMuPDF

ARCHITECTURE:
- Input: JSON with field values (e.g., {"1a": {"value": "75000"}, ...})
- Process: Maps JSON fields to PDF fields using verified mappings
- Output: Filled PDF with actual values (not field names)

FILE LOCATION: Place this file at the SAME level as views.py
Example: /path/to/django_app/pdf_filler.py (next to views.py)
"""

import fitz  # PyMuPDF
import os

# Import ALL mappings including new taxpayer_info and checkboxes
try:
    from .form_mappings_complete import ALL_FORM_MAPPINGS, FORM_TEMPLATES
    # Also import taxpayer and checkbox mappings
    from .form_mappings_complete import (
        FORM_1040_TAXPAYER_INFO, FORM_1040_CHECKBOXES,
        SCHEDULE_A_TAXPAYER_INFO, SCHEDULE_A_CHECKBOXES,
        SCHEDULE_B_TAXPAYER_INFO, SCHEDULE_B_CHECKBOXES,
        SCHEDULE_C_TAXPAYER_INFO, SCHEDULE_C_CHECKBOXES,
        SCHEDULE_D_TAXPAYER_INFO, SCHEDULE_D_CHECKBOXES,
        SCHEDULE_E_TAXPAYER_INFO, SCHEDULE_E_CHECKBOXES,
        SCHEDULE_F_TAXPAYER_INFO, SCHEDULE_F_CHECKBOXES,
        SCHEDULE_H_TAXPAYER_INFO, SCHEDULE_H_CHECKBOXES,
        SCHEDULE_1_TAXPAYER_INFO, SCHEDULE_1_CHECKBOXES,
        SCHEDULE_2_TAXPAYER_INFO, SCHEDULE_2_CHECKBOXES,
        SCHEDULE_3_TAXPAYER_INFO,
    )
except ImportError:
    # Standalone mode (not in Django)
    from form_mappings_complete import ALL_FORM_MAPPINGS, FORM_TEMPLATES
    from form_mappings_complete import (
        FORM_1040_TAXPAYER_INFO, FORM_1040_CHECKBOXES,
        SCHEDULE_A_TAXPAYER_INFO, SCHEDULE_A_CHECKBOXES,
        SCHEDULE_B_TAXPAYER_INFO, SCHEDULE_B_CHECKBOXES,
        SCHEDULE_C_TAXPAYER_INFO, SCHEDULE_C_CHECKBOXES,
        SCHEDULE_D_TAXPAYER_INFO, SCHEDULE_D_CHECKBOXES,
        SCHEDULE_E_TAXPAYER_INFO, SCHEDULE_E_CHECKBOXES,
        SCHEDULE_F_TAXPAYER_INFO, SCHEDULE_F_CHECKBOXES,
        SCHEDULE_H_TAXPAYER_INFO, SCHEDULE_H_CHECKBOXES,
        SCHEDULE_1_TAXPAYER_INFO, SCHEDULE_1_CHECKBOXES,
        SCHEDULE_2_TAXPAYER_INFO, SCHEDULE_2_CHECKBOXES,
        SCHEDULE_3_TAXPAYER_INFO,
    )

# Map form names to their taxpayer/checkbox mappings
TAXPAYER_MAPPINGS = {
    '1040': FORM_1040_TAXPAYER_INFO,
    'schedule_1': SCHEDULE_1_TAXPAYER_INFO,
    'schedule_2': SCHEDULE_2_TAXPAYER_INFO,
    'schedule_3': SCHEDULE_3_TAXPAYER_INFO,
    'schedule_a': SCHEDULE_A_TAXPAYER_INFO,
    'schedule_b': SCHEDULE_B_TAXPAYER_INFO,
    'schedule_c': SCHEDULE_C_TAXPAYER_INFO,
    'schedule_d': SCHEDULE_D_TAXPAYER_INFO,
    'schedule_e': SCHEDULE_E_TAXPAYER_INFO,
    'schedule_f': SCHEDULE_F_TAXPAYER_INFO,
    'schedule_h': SCHEDULE_H_TAXPAYER_INFO,
}

CHECKBOX_MAPPINGS = {
    '1040': FORM_1040_CHECKBOXES,
    'schedule_1': SCHEDULE_1_CHECKBOXES,
    'schedule_2': SCHEDULE_2_CHECKBOXES,
    'schedule_a': SCHEDULE_A_CHECKBOXES,
    'schedule_b': SCHEDULE_B_CHECKBOXES,
    'schedule_c': SCHEDULE_C_CHECKBOXES,
    'schedule_d': SCHEDULE_D_CHECKBOXES,
    'schedule_e': SCHEDULE_E_CHECKBOXES,
    'schedule_f': SCHEDULE_F_CHECKBOXES,
    'schedule_h': SCHEDULE_H_CHECKBOXES,
}

# PDF Templates directory
# Templates are in the SAME directory as this file (files_to_send/)
TEMPLATE_DIR = os.path.dirname(os.path.abspath(__file__))

# Form ID to template mapping (OPTIONAL - if using Django model IDs)
# You can skip this if you're passing form_name directly
FORM_ID_TO_TEMPLATE = {
    # Add your database form IDs here if needed:
    # 16026: ('1040', 'f1040.pdf'),
    # 16027: ('schedule_a', 'f1040sa.pdf'),
    # etc...
}

def fill_form_universal(data, form_name, grey_out_calculated=True):
    """
    Universal PDF filler for ALL IRS forms using verified mappings
    
    IMPORTANT: This fills PDF with ACTUAL VALUES from JSON, not field names!
    
    Args:
        data (dict): JSON data with structure:
            {
                "taxpayer": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "ssn": "123-45-6789"
                },
                "fields": {
                    "1a": {
                        "value": "75000",           ← ACTUAL VALUE (not "1a")
                        "label": "Wages...",
                        "ftype": "number",
                        "can_be_modified": true
                    },
                    "1z": {
                        "value": "75000",           ← ACTUAL VALUE
                        "can_be_modified": false    ← Greyed out
                    }
                }
            }
        form_name (str): Form identifier (e.g., '1040', 'schedule_a', 'schedule_d')
        grey_out_calculated (bool): If True, grey out fields where can_be_modified=False
    
    Returns:
        bytes: PDF file content (editable PDF with ACTUAL VALUES filled in)
    """
    # Get template filename
    if form_name not in FORM_TEMPLATES:
        raise ValueError(f"Unknown form: {form_name}. Available forms: {list(FORM_TEMPLATES.keys())}")
    
    template_file = FORM_TEMPLATES[form_name]
    template_path = os.path.join(TEMPLATE_DIR, template_file)
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found: {template_path}")
    
    # Get field mappings for this form (JSON field name → PDF field name)
    if form_name not in ALL_FORM_MAPPINGS:
        raise ValueError(f"No mappings found for form: {form_name}")
    
    field_mappings = ALL_FORM_MAPPINGS[form_name]
    
    # Load blank template
    doc = fitz.open(template_path)
    
    # Build field path map (BOTH full and short names → (page, widget))
    # Store page reference to avoid "not bound to page" error
    field_map = {}
    for page_num in range(doc.page_count):
        page = doc[page_num]
        for widget in page.widgets():
            if widget.field_name:
                full_name = widget.field_name
                # Store by full name
                field_map[full_name] = (page, widget)
                # Also store by short name (e.g., "f1_47[0]")
                if '.' in full_name:
                    short_name = full_name.split('.')[-1]
                    field_map[short_name] = (page, widget)
    
    # Track filling stats
    filled_count = 0
    grey_count = 0
    taxpayer_filled = 0
    checkbox_filled = 0
    skipped = []
    
    # Extract data
    taxpayer = data.get('taxpayer', {})
    fields_data = data.get('fields', {})
    
    # ===== 1. FILL LINE ITEMS =====
    for json_field, pdf_field in field_mappings.items():
        # Check if this field has data in the input JSON
        field_info = fields_data.get(json_field)
        
        if not field_info:
            continue
        
        # Get the ACTUAL VALUE to fill (not the field name!)
        value = field_info.get('value')
        can_modify = field_info.get('can_be_modified', True)
        
        if value is None or value == '':
            continue
        
        # Find the PDF field widget (try exact match first)
        if pdf_field in field_map:
            page, widget = field_map[pdf_field]
        else:
            skipped.append(f"{json_field} → {pdf_field}")
            continue
        
        # Fill the field with ACTUAL VALUE
        widget.field_value = str(value)  # e.g., "75000" not "1a"
        widget.update()
        filled_count += 1
        
        # Grey out if calculated field
        if grey_out_calculated and not can_modify:
            widget.field_flags |= fitz.PDF_FIELD_IS_READ_ONLY
            widget.fill_color = (0.9, 0.9, 0.9)
            widget.update()
            grey_count += 1
    
    # ===== 2. FILL TAXPAYER INFO =====
    if form_name in TAXPAYER_MAPPINGS:
        taxpayer_mappings = TAXPAYER_MAPPINGS[form_name]
        
        for json_field, pdf_field in taxpayer_mappings.items():
            # Handle special combined fields
            if json_field == 'full_name':
                value = f"{taxpayer.get('first_name', '')} {taxpayer.get('last_name', '')}".strip()
            elif json_field == 'property_address_1a':
                parts = [taxpayer.get('address', ''), taxpayer.get('city', ''), 
                        taxpayer.get('state', ''), taxpayer.get('zip', '')]
                value = ', '.join([p for p in parts if p])
            elif json_field == 'employer_name':
                value = f"{taxpayer.get('first_name', '')} {taxpayer.get('last_name', '')}".strip()
            else:
                value = taxpayer.get(json_field, '')
            
            if not value:
                continue
            
            # Find and fill the PDF field (check both exact match and if full name contains it)
            if pdf_field in field_map:
                page, widget = field_map[pdf_field]
                widget.field_value = str(value)
                widget.update()
                taxpayer_filled += 1
            else:
                # Try finding by checking if any full field name contains this
                for full_name, (page, widget) in field_map.items():
                    if full_name.endswith(pdf_field) or pdf_field in full_name:
                        widget.field_value = str(value)
                        widget.update()
                        taxpayer_filled += 1
                        break
    
    # ===== 3. FILL CHECKBOXES =====
    if form_name in CHECKBOX_MAPPINGS:
        checkbox_mappings = CHECKBOX_MAPPINGS[form_name]
        
        for json_field, pdf_field in checkbox_mappings.items():
            # Handle filing_status (multi-option)
            if json_field == 'filing_status' and isinstance(pdf_field, dict):
                status_value = taxpayer.get('status_display', '').lower().replace(' ', '_')
                if status_value in pdf_field:
                    target_pdf_field = pdf_field[status_value]
                    checkbox_value = "Yes"
                    
                    # Try exact match first
                    if target_pdf_field in field_map:
                        page, widget = field_map[target_pdf_field]
                        widget.field_value = checkbox_value
                        widget.update()
                        checkbox_filled += 1
                    else:
                        # Try finding by checking if any full field name contains it
                        for full_name, (page, widget) in field_map.items():
                            if full_name.endswith(target_pdf_field) or target_pdf_field in full_name:
                                widget.field_value = checkbox_value
                                widget.update()
                                checkbox_filled += 1
                                break
            elif not isinstance(pdf_field, dict):
                # Simple checkbox
                value = taxpayer.get(json_field)
                if value is None and json_field in fields_data:
                    value = fields_data[json_field].get('value', False)
                
                if value is not None:
                    checkbox_value = "Yes" if value else "Off"
                    
                    # Try exact match first
                    if pdf_field in field_map:
                        page, widget = field_map[pdf_field]
                        widget.field_value = checkbox_value
                        widget.update()
                        checkbox_filled += 1
                    else:
                        # Try finding by checking if any full field name contains it
                        for full_name, (page, widget) in field_map.items():
                            if full_name.endswith(pdf_field) or pdf_field in full_name:
                                widget.field_value = checkbox_value
                                widget.update()
                                checkbox_filled += 1
                                break
    
    
    # Debug info (optional - can be logged)
    print(f"✅ Filled {filled_count} line items in {form_name}")
    if taxpayer_filled > 0:
        print(f"   👤 Filled {taxpayer_filled} taxpayer info fields")
    if checkbox_filled > 0:
        print(f"   ☑️  Filled {checkbox_filled} checkboxes")
    if grey_count > 0:
        print(f"   🔒 Greyed out {grey_count} calculated fields")
    if skipped:
        print(f"   ⚠️  Skipped {len(skipped)} fields (not found in PDF)")
    
    # Return PDF as bytes
    pdf_bytes = doc.tobytes()
    doc.close()
    
    return pdf_bytes


def fill_form_1040(data, grey_out_calculated=True):
    """
    Legacy function - redirects to universal filler
    Kept for backward compatibility
    """
    return fill_form_universal(data, '1040', grey_out_calculated)


def fill_schedule(data, form_name, grey_out_calculated=True):
    """
    Legacy function - redirects to universal filler
    Kept for backward compatibility
    
    Args:
        data: JSON data
        form_name: 'schedule_a', 'schedule_b', etc.
    """
    return fill_form_universal(data, form_name, grey_out_calculated)


def generate_form_pdf(form_instance):
    """
    Main function to generate filled PDF for any form (Django integration)
    
    This is called by the Django view to generate PDFs with ACTUAL VALUES
    
    Args:
        form_instance: Django model instance OR dict with:
            - form_name: Form identifier (e.g., '1040', 'schedule_d')
            - data: JSON field containing taxpayer and fields data with ACTUAL VALUES
    
    Returns:
        bytes: PDF file content (filled with actual values, not field names)
    
    Example input data:
        {
            "taxpayer": {"first_name": "John", "last_name": "Doe", "ssn": "123-45-6789"},
            "fields": {
                "1a": {"value": "75000", "can_be_modified": true},  ← "75000" appears in PDF
                "1z": {"value": "75000", "can_be_modified": false}  ← "75000" appears greyed
            }
        }
    """
    # Handle both Django model instances and plain dicts
    if isinstance(form_instance, dict):
        form_name = form_instance['form_name']
        data = form_instance['data']
    else:
        # Django model instance - get form_name from id mapping
        form_id = form_instance.id
        
        if form_id not in FORM_ID_TO_TEMPLATE:
            raise ValueError(f"Unknown form ID: {form_id}. Please add mapping in FORM_ID_TO_TEMPLATE")
        
        form_name, template_file = FORM_ID_TO_TEMPLATE[form_id]
        data = form_instance.data
    
    # Validate data structure
    if not isinstance(data, dict):
        raise ValueError("form_instance.data must be a dictionary")
    
    if 'taxpayer' not in data:
        raise ValueError("data missing 'taxpayer' key")
    
    if 'fields' not in data:
        raise ValueError("data missing 'fields' key")
    
    # Use universal filler to fill PDF with ACTUAL VALUES
    return fill_form_universal(data, form_name)

