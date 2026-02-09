# 📦 INSTALLATION GUIDE

## 🎯 What This Package Does

Replaces HTML form rendering (with formatting issues) with editable PDF generation using PyMuPDF.

---

## 📋 Files Included

1. **`pdf_filler.py`** - PDF generation utility (your Stage 3 logic)
2. **`views.py`** - Modified Django views
3. **`FILE_PLACEMENT.md`** - ⚠️ **READ THIS FIRST!** Shows exactly where to place each file
4. **PDF Templates** (5 blank PDFs):
   - `f1040.pdf` (Form 1040)
   - `f1040sa.pdf` (Schedule A)
   - `f1040sb.pdf` (Schedule B)
   - `f1040sc.pdf` (Schedule C)
   - `f1040sd.pdf` (Schedule D)

---

## 🚀 INSTALLATION STEPS

### **⚠️ FIRST: Read FILE_PLACEMENT.md**

**Before you start, read `FILE_PLACEMENT.md` to understand where each file goes!**

This is CRITICAL - files must be in exact locations for imports to work.

---

### **Step 1: Install PyMuPDF**

```bash
# On the server, activate your Python environment
source /path/to/venv/bin/activate  # Or your environment activation

# Install PyMuPDF
pip install PyMuPDF

# Verify installation
python -c "import fitz; print('PyMuPDF version:', fitz.version)"
```

---

### **Step 2: Create Directory Structure**

```bash
# Navigate to your Django app directory (where views.py is)
cd /path/to/your/django/project/tax_app/

# Verify you're in the right place
ls views.py  # Should exist

# Create PDF templates directory
mkdir -p templates/pdf_blanks
```

**Directory structure should be:**
```
tax_app/                    ← You are here
├── views.py               ← Existing file
├── templates/
│   ├── forms/             ← Existing HTML templates
│   └── pdf_blanks/        ← NEW directory (created above)
└── ...
```

---

### **Step 3: Upload Files**

#### **A. Upload pdf_filler.py**

⚠️ **CRITICAL:** Place in SAME directory as views.py

```bash
# You should be in the directory with views.py
pwd  # Verify: /path/to/tax_app/

# Copy pdf_filler.py to THIS directory (next to views.py)
cp pdf_filler.py .

# Verify both files are together
ls -la views.py pdf_filler.py
# Both should exist in SAME directory!
```

**Why same directory?**
Because `views.py` imports with: `from .pdf_filler import generate_form_pdf`
The dot (`.`) means "same directory"

#### **B. Upload PDF Templates**

**Upload 5 blank PDF files to `templates/pdf_blanks/`:**

```bash
# From the tax_app directory
cd templates/pdf_blanks/

# Copy all 5 PDFs here
cp /path/to/downloaded/f1040.pdf .
cp /path/to/downloaded/f1040sa.pdf .
cp /path/to/downloaded/f1040sb.pdf .
cp /path/to/downloaded/f1040sc.pdf .
cp /path/to/downloaded/f1040sd.pdf .

# Verify all 5 files are present
ls -la
# Should show:
# f1040.pdf
# f1040sa.pdf
# f1040sb.pdf
# f1040sc.pdf
# f1040sd.pdf
```

**Full path should be:**
```
/path/to/tax_app/templates/pdf_blanks/f1040.pdf
/path/to/tax_app/templates/pdf_blanks/f1040sa.pdf
... etc
```

---

### **Step 4: Modify views.py**

**OPTION A: Replace Entire File**

```bash
# Backup your existing views.py
cp views.py views.py.backup

# Replace with new views.py
cp new_views.py views.py
```

**OPTION B: Merge Manually**

Add these two classes to your existing `views.py`:
- `TaxpayerFormPDFView`
- `TaxpayerFormRenderView` (replace existing one)

And add this import at the top:
```python
from .pdf_filler import generate_form_pdf
```

---

### **Step 5: Update Form ID Mapping**

**Edit `pdf_filler.py`** - Update `FORM_ID_TO_TEMPLATE` dictionary:

```python
# Around line 24 in pdf_filler.py
FORM_ID_TO_TEMPLATE = {
    16026: ('form_1040', 'f1040.pdf'),      # Form 1040
    16027: ('schedule_a', 'f1040sa.pdf'),   # Schedule A
    16028: ('schedule_b', 'f1040sb.pdf'),   # Schedule B
    16029: ('schedule_c', 'f1040sc.pdf'),   # Schedule C
    16030: ('schedule_d', 'f1040sd.pdf'),   # Schedule D
}
```

**Replace with YOUR actual form IDs from the database!**

To find your form IDs:
```sql
SELECT id, name FROM forms WHERE year=2025;
```

---

### **Step 6: Implement get_form() Method**

**Edit `views.py`** - Implement the `get_form()` method in `TaxpayerFormPDFView`:

```python
def get_form(self, request, taxpayer_id, year, pk):
    """Get form instance from database"""
    from .models import Form  # Or your actual model name
    
    return Form.objects.get(
        id=pk,
        year=year,
        taxpayer_id=taxpayer_id
    )
```

**The returned object MUST have:**
- `id` - Form ID (integer)
- `name` - Form name (string)
- `data` - JSON field with structure:
  ```json
  {
    "taxpayer": {"first_name": "...", "last_name": "...", "ssn": "..."},
    "fields": {"1a": {"value": "...", "can_be_modified": true}, ...}
  }
  ```

---

### **Step 7: Verify URLs**

**Check `urls.py`** - Make sure these endpoints exist:

```python
from .views import TaxpayerFormRenderView, TaxpayerFormPDFView

urlpatterns = [
    # ... existing patterns ...
    
    # HTML form view (now redirects to PDF)
    path('api/v1/taxpayer/<int:taxpayer_id>/render/form/<int:year>/<int:pk>/',
         TaxpayerFormRenderView.as_view(),
         name='render_form'),
    
    # PDF generation (new editable PDF)
    path('api/v1/taxpayer/<int:taxpayer_id>/render/pdf/<int:year>/<int:pk>/',
         TaxpayerFormPDFView.as_view(),
         name='render_pdf'),
]
```

---

### **Step 8: Restart Server**

```bash
# Restart your Django server
sudo systemctl restart gunicorn  # Or your server command
# OR
python manage.py runserver
```

---

## ✅ TESTING

### **Test 1: Check PDF Generation**

```bash
# OPTION A: Test via browser (easiest - no token needed)
# 1. Log in to your web app
# 2. Visit: https://lowercoststaxes.com/api/v1/taxpayer/40/render/pdf/2025/16026/
# 3. Should see PDF in browser

# OPTION B: Test via curl (if API requires token authentication)
curl -H "Authorization: Token YOUR_TOKEN" \
  "https://lowercoststaxes.com/api/v1/taxpayer/40/render/pdf/2025/16026/" \
  > test.pdf

# Verify PDF has form fields
python3 -c "
import fitz
doc = fitz.open('test.pdf')
print(f'Form fields: {len(list(doc[0].widgets()))}')
"
```

**Expected:** Should show number > 0 (editable PDF)

**Note:** The backend uses Django session authentication (request.user), not tokens.
Tokens are only needed if testing the API endpoint directly without browser login.

---

### **Test 2: Test HTML Redirect**

```bash
# OPTION A: Test in browser (recommended)
# 1. Log in
# 2. Visit: https://lowercoststaxes.com/api/v1/taxpayer/40/render/form/2025/16026/
# 3. Should automatically redirect to /render/pdf/ URL

# OPTION B: Test with curl
curl -I "https://lowercoststaxes.com/api/v1/taxpayer/40/render/form/2025/16026/"
```

**Expected:** Should return `302 Found` redirect to `/render/pdf/`

---

### **Test 3: Test in Browser**

1. Log in to web app
2. Go to Review section
3. Click on any form (e.g., Form 1040)
4. **Expected:** See PDF viewer (not HTML form)
5. **Verify:** Can edit form fields in PDF
6. Click "Download PDF"
7. **Expected:** Downloads editable PDF

---

## 🔧 TROUBLESHOOTING

### **Error: "Template not found"**

**Cause:** PDF templates not uploaded or wrong path

**Fix:**
```bash
# Check if files exist
ls -la /path/to/django/templates/pdf_blanks/

# Should show:
# f1040.pdf
# f1040sa.pdf
# ... etc
```

---

### **Error: "Unknown form ID"**

**Cause:** `FORM_ID_TO_TEMPLATE` mapping not updated

**Fix:** Edit `utils/pdf_filler.py` and add your form IDs

---

### **Error: "Form fields: 0" (PDF not editable)**

**Cause:** Blank PDF templates are flat (no form fields)

**Fix:** Make sure you uploaded the CORRECT blank PDFs with form fields

---

### **Error: "No module named 'pdf_filler'"**

**Cause:** `pdf_filler.py` not in same directory as `views.py`

**Fix:**
```bash
# Find where views.py is
find /var/www -name "views.py" -path "*/tax_app/*"

# Put pdf_filler.py in SAME directory
cp pdf_filler.py /path/to/same/directory/
```

---

## 📊 DATA STRUCTURE REQUIREMENTS

Your database form data MUST have this structure:

```python
form_instance.data = {
    "form": {
        "id": 16026,
        "name": "FORM 1040",
        "year": "2025"
    },
    "taxpayer": {
        "first_name": "John",
        "last_name": "Doe",
        "ssn": "123-45-6789",
        "email": "john@example.com",
        "state": "CA"
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
            "can_be_modified": false  # Greyed out
        }
        # ... more fields
    }
}
```

---

## 🎯 WHAT CHANGED

| Before | After |
|--------|-------|
| HTML form with CSS positioning | Editable PDF viewer |
| Formatting issues | Perfect formatting |
| Flat PDF download | Editable PDF download |
| Can't edit PDF | Can edit PDF directly |
| `/render/form/` shows HTML | `/render/form/` redirects to PDF |
| `/render/pdf/` returns flat PDF | `/render/pdf/` returns editable PDF |

---

## 📞 SUPPORT

If you encounter issues:

1. Check server logs: `tail -f /var/log/django/error.log`
2. Check PyMuPDF installation: `pip show PyMuPDF`
3. Verify file paths in `pdf_filler.py` line 13
4. Test with curl commands above

---

## ✅ CHECKLIST

- [ ] PyMuPDF installed (`pip install PyMuPDF`)
- [ ] `templates/pdf_blanks/` directory created
- [ ] `pdf_filler.py` uploaded to SAME directory as `views.py`
- [ ] 5 PDF templates uploaded to `templates/pdf_blanks/`
- [ ] `FORM_ID_TO_TEMPLATE` updated with actual form IDs
- [ ] `views.py` modified (or replaced)
- [ ] `get_form()` method implemented
- [ ] `urls.py` verified
- [ ] Server restarted
- [ ] Tested with curl
- [ ] Tested in browser

---

**Installation complete! Users should now see editable PDFs instead of HTML forms.**
