# 📄 PDF Rendering Solution for Tax Forms

## 🎯 Purpose

Replace HTML/CSS form rendering with editable PDF generation to eliminate formatting issues.

---

## 📦 Package Contents

### **1. Python Files**
- `pdf_filler.py` - PDF generation utility (PyMuPDF-based)
- `views.py` - Modified Django views

### **2. PDF Templates** (Upload separately)
**Location:** Send via separate archive or file transfer

5 blank PDF forms with editable fields:
- `f1040.pdf` - Form 1040
- `f1040sa.pdf` - Schedule A  
- `f1040sb.pdf` - Schedule B
- `f1040sc.pdf` - Schedule C
- `f1040sd.pdf` - Schedule D

**Size:** ~583 KB total

### **3. Documentation**
- `INSTALLATION.md` - Complete installation guide
- `README.md` - This file

---

## 🔄 How It Works

### **Current Flow (HTML):**
```
User clicks Form 1040
  ↓
/render/form/2025/16026/
  ↓
Returns HTML with CSS positioning
  ↓
Formatting issues ❌
```

### **New Flow (PDF):**
```
User clicks Form 1040 (already logged in to web app)
  ↓
/render/form/2025/16026/ → Redirects to /render/pdf/
  ↓
Backend (views.py):
  1. Gets taxpayer_id from URL (already authenticated via Django session)
  2. Queries database: Form.objects.get(id=16026, taxpayer_id=40, year=2025)
  3. Gets JSON data from database (taxpayer info + field values)
  4. Loads blank f1040.pdf template
  5. Fills fields with PyMuPDF
  6. Greys out calculated fields (can_be_modified=false)
  ↓
Returns editable PDF
  ↓
Perfect formatting ✅
User can edit fields ✅
```

---

## 🗄️ Data Structure

### **Database JSON Format:**

Each user's form data is stored as JSON:

```json
{
  "form": {
    "id": 16026,
    "name": "FORM 1040",
    "year": "2025"
  },
  "taxpayer": {
    "first_name": "John",
    "last_name": "Doe",
    "ssn": "123-45-6789"
  },
  "fields": {
    "1a": {
      "value": "50000",
      "can_be_modified": true   ← User can edit
    },
    "1z": {
      "value": "50000",
      "can_be_modified": false  ← Calculated, greyed out
    }
  }
}
```

### **Per-User Data:**

| User ID | Form ID | Data |
|---------|---------|------|
| 40 | 16026 | User 40's data for Form 1040 |
| 41 | 16026 | User 41's data for Form 1040 |
| 42 | 16026 | User 42's data for Form 1040 |

**Same form template, different data for each user!**

---

## 🔧 Technical Details

### **Technology:**
- **PyMuPDF (fitz)** - PDF manipulation library
- **Django REST Framework** - API backend
- **IRS Official PDFs** - Blank form templates with editable fields

### **Field Mapping:**

Form 1040 uses manual field mapping:
```python
'1a': 'topmostSubform[0].Page1[0].f1_47[0]'  # W-2 wages
'1z': 'topmostSubform[0].Page1[0].f1_73[0]'  # Total (calculated)
```

Schedules use sequential mapping:
```python
f1_3[0] → First data field
f1_4[0] → Second data field
... etc
```

### **Grey-Out Logic:**

Fields with `can_be_modified: false` are:
- Made read-only
- Given grey background (RGB: 0.9, 0.9, 0.9)
- Still visible but not editable

---

## 📋 Requirements

### **Server Requirements:**
- Python 3.7+
- Django 3.0+
- Django REST Framework
- PyMuPDF (`pip install PyMuPDF`)

### **Storage:**
- ~5 MB for PDF templates
- Existing database with JSON field for form data

---

## 🚀 Quick Start

### **For App Owner:**

1. Read `INSTALLATION.md`
2. Install PyMuPDF
3. Upload files to correct locations
4. Update form ID mapping
5. Restart server
6. Test

**Estimated time:** 30 minutes

---

## 🎯 Benefits

| Before (HTML) | After (PDF) |
|--------------|-------------|
| CSS alignment issues | Perfect IRS formatting |
| Browser inconsistencies | Consistent PDF rendering |
| Flat PDF downloads | Editable PDF downloads |
| Can't edit downloaded PDF | Can edit and save PDF |
| Complex template maintenance | Simple template updates |

---

## 🔍 What Gets Modified

### **Modified Files:**
- `views.py` - Add TaxpayerFormPDFView, modify TaxpayerFormRenderView

### **New Files:**
- `utils/pdf_filler.py` - PDF generation logic
- `templates/pdf_blanks/*.pdf` - Blank form templates

### **Not Modified:**
- Database schema
- URL routing (optional update)
- Frontend code
- API authentication

---

## 📊 Form ID Mapping

**You MUST configure these in `pdf_filler.py`:**

```python
FORM_ID_TO_TEMPLATE = {
    16026: ('form_1040', 'f1040.pdf'),
    # ADD YOUR ACTUAL FORM IDs:
    # 16027: ('schedule_a', 'f1040sa.pdf'),
    # 16028: ('schedule_b', 'f1040sb.pdf'),
    # etc.
}
```

To find your form IDs:
```sql
SELECT id, name FROM forms WHERE year=2025 LIMIT 10;
```

---

## ✅ Testing

### **Automated Tests:**
```bash
# Test PDF generation (if API requires authentication)
# Note: If you're testing from browser while logged in, no token needed
curl -H "Authorization: Token YOUR_TOKEN" \
  "https://lowercoststaxes.com/api/v1/taxpayer/40/render/pdf/2025/16026/" \
  > test.pdf

# OR if using session-based auth, test directly in browser:
# Just log in and visit: https://lowercoststaxes.com/api/v1/taxpayer/40/render/pdf/2025/16026/

# Check if PDF has form fields
python3 -c "
import fitz
doc = fitz.open('test.pdf')
widgets = list(doc[0].widgets())
print(f'✅ Editable fields: {len(widgets)}')
"
```

### **Manual Tests:**
1. Log in as test user
2. Navigate to review section
3. Click Form 1040
4. Verify PDF displays (not HTML)
5. Verify can edit fields
6. Download PDF
7. Open in Adobe Reader - verify fields are editable

---

## 🔐 Security & Authentication

### **How Authentication Works:**

**No tokens in the backend code!** Authentication is handled by Django:

1. **User logs in** to web app (Django session authentication)
2. **User clicks form** in review section
3. **Django views.py receives request** with:
   - `taxpayer_id` from URL (e.g., `/taxpayer/40/render/pdf/...`)
   - User session (already authenticated)
4. **Backend queries database:**
   ```python
   # Inside views.py
   def get_form(self, request, taxpayer_id, year, pk):
       # No token needed - Django handles auth via request.user
       form = Form.objects.get(
           id=pk,              # Form ID (16026)
           year=year,          # Tax year (2025)
           taxpayer_id=taxpayer_id  # User ID (40)
       )
       return form
   ```
5. **Security is handled by:**
   - Django's existing authentication middleware
   - Your existing permission checks
   - Database query filters (user can only see their own data)

**Summary:**
- ✅ Uses existing Django session authentication
- ✅ No changes to authentication system
- ✅ PDF generation happens server-side (secure)
- ✅ User can only access their own data (existing security rules apply)

---

## 📞 Support

### **Common Issues:**

**"Template not found"**
→ Upload PDF templates to `templates/pdf_blanks/`

**"Unknown form ID"**
→ Update `FORM_ID_TO_TEMPLATE` in `pdf_filler.py`

**"Import error"**
→ Run `pip install PyMuPDF`

**"PDF not editable"**
→ Check blank PDFs have form fields (not flat)

---

## 📝 Notes

- Blank PDF templates are from official IRS forms
- Templates are reused for all users (same blank form)
- User data is filled into template at runtime
- Original HTML templates remain unchanged (can fallback if needed)
- This solution is based on working Stage 3 pipeline code

---

## 🎉 Result

Users will see:
✅ Professional IRS-formatted PDFs
✅ Editable form fields
✅ Calculated fields greyed out
✅ Download editable PDFs
✅ No formatting issues

---

**Ready to install? Start with `INSTALLATION.md`**
