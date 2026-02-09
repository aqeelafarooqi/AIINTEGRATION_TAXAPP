# 📁 CRITICAL: FILE PLACEMENT GUIDE

## 🎯 WHERE TO PUT EACH FILE

### **Current Structure (What App Owner Has):**

```
django_project/
├── manage.py
├── tax_app/                    ← Main app directory
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── views.py               ← EXISTING FILE (modify this)
│   ├── models.py
│   ├── templates/
│   │   ├── forms/
│   │   │   ├── form_1040.html
│   │   │   ├── schedule_a.html
│   │   │   └── ...
│   │   └── ...
│   └── static/
│       ├── css/
│       └── ...
└── ...
```

---

## ✅ WHERE TO PLACE NEW FILES

### **1. pdf_filler.py**

**Location:** SAME directory as `views.py`

```
django_project/
└── tax_app/
    ├── views.py               ← Existing file
    ├── pdf_filler.py          ← NEW FILE (place here!)
    └── ...
```

**Why here?**
- So `views.py` can import: `from .pdf_filler import generate_form_pdf`
- The dot (`.`) means "same directory"

**Full path example:**
```
/var/www/django_project/tax_app/pdf_filler.py
```

---

### **2. views.py (Modified)**

**Location:** REPLACE existing `views.py` OR merge changes

```
django_project/
└── tax_app/
    ├── views.py               ← MODIFY this file
    └── ...
```

**What to do:**
- **Option A:** Backup existing `views.py` then replace with new one
- **Option B:** Copy the new classes into existing `views.py`

**Changes needed:**
```python
# ADD this import at the top:
from .pdf_filler import generate_form_pdf

# ADD new class:
class TaxpayerFormPDFView(views.APIView):
    ...

# MODIFY existing class:
class TaxpayerFormRenderView(views.APIView):
    # Change get() method to redirect to PDF
    ...
```

---

### **3. PDF Templates (5 files)**

**Location:** Create new directory `templates/pdf_blanks/`

```
django_project/
└── tax_app/
    └── templates/
        ├── forms/              ← Existing HTML templates
        │   ├── form_1040.html
        │   └── ...
        └── pdf_blanks/         ← NEW DIRECTORY (create this!)
            ├── f1040.pdf       ← NEW FILE
            ├── f1040sa.pdf     ← NEW FILE
            ├── f1040sb.pdf     ← NEW FILE
            ├── f1040sc.pdf     ← NEW FILE
            └── f1040sd.pdf     ← NEW FILE
```

**Full path example:**
```
/var/www/django_project/tax_app/templates/pdf_blanks/f1040.pdf
```

**Create directory:**
```bash
mkdir -p /path/to/django_project/tax_app/templates/pdf_blanks
```

**Upload files:**
```bash
# Copy all 5 PDFs to this directory
cp f1040.pdf /path/to/django_project/tax_app/templates/pdf_blanks/
cp f1040sa.pdf /path/to/django_project/tax_app/templates/pdf_blanks/
# ... etc for all 5 PDFs
```

---

## 🔍 HOW IMPORTS WORK

### **In views.py:**

```python
from .pdf_filler import generate_form_pdf
#    ^
#    This dot means "same directory as views.py"
```

**Means:** Look for `pdf_filler.py` in the SAME directory as `views.py`

```
tax_app/
├── views.py          ← File that imports
└── pdf_filler.py     ← File being imported
```

---

### **In pdf_filler.py:**

```python
TEMPLATE_DIR = os.path.join(settings.BASE_DIR, 'templates', 'pdf_blanks')
#                             ^^^^^^^^^^^^^^^^   ^^^^^^^^^^   ^^^^^^^^^^
#                             Project root       Folder       Subfolder
```

**Result:** `/path/to/django_project/tax_app/templates/pdf_blanks/`

---

## ⚠️ COMMON MISTAKES

### **❌ WRONG: Putting pdf_filler.py in utils/**

```
tax_app/
├── views.py
└── utils/
    └── pdf_filler.py    ← WRONG!
```

**Problem:** `from .pdf_filler import ...` won't work!

**Would need:** `from .utils.pdf_filler import ...`

---

### **❌ WRONG: PDFs in wrong directory**

```
templates/
└── pdfs/              ← WRONG name!
    └── f1040.pdf
```

**Problem:** Code looks for `templates/pdf_blanks/`

**Fix:** Must be named exactly `pdf_blanks`

---

### **❌ WRONG: PDFs in root**

```
tax_app/
├── f1040.pdf          ← WRONG location!
└── templates/
```

**Problem:** Code looks in `templates/pdf_blanks/` not root

---

## ✅ VERIFICATION COMMANDS

### **After placing files, verify:**

```bash
# 1. Check pdf_filler.py exists next to views.py
ls -la /path/to/tax_app/views.py
ls -la /path/to/tax_app/pdf_filler.py
# Both should exist in SAME directory

# 2. Check PDF templates exist
ls -la /path/to/tax_app/templates/pdf_blanks/
# Should show:
# f1040.pdf
# f1040sa.pdf
# f1040sb.pdf
# f1040sc.pdf
# f1040sd.pdf

# 3. Test import (from Django shell)
python manage.py shell
>>> from tax_app.pdf_filler import generate_form_pdf
>>> # If no error, import works!
```

---

## 📋 INSTALLATION CHECKLIST

- [ ] **Step 1:** Create `templates/pdf_blanks/` directory
  ```bash
  mkdir -p /path/to/tax_app/templates/pdf_blanks
  ```

- [ ] **Step 2:** Upload 5 PDF files to `templates/pdf_blanks/`
  ```bash
  ls /path/to/tax_app/templates/pdf_blanks/
  # Should show all 5 PDFs
  ```

- [ ] **Step 3:** Upload `pdf_filler.py` to same directory as `views.py`
  ```bash
  ls /path/to/tax_app/pdf_filler.py
  # Should exist
  ```

- [ ] **Step 4:** Modify `views.py`
  - Add import: `from .pdf_filler import generate_form_pdf`
  - Add `TaxpayerFormPDFView` class
  - Modify `TaxpayerFormRenderView` class

- [ ] **Step 5:** Test import
  ```bash
  python manage.py shell
  >>> from .pdf_filler import generate_form_pdf
  ```

---

## 🎯 SUMMARY

**Three things to remember:**

1. **pdf_filler.py** → SAME directory as views.py
2. **PDF templates** → templates/pdf_blanks/ (create this directory)
3. **views.py** → Modify existing file (add import + new class)

**That's it!**

---

## 📞 IF IMPORTS DON'T WORK

### **Error: "No module named pdf_filler"**

**Cause:** pdf_filler.py not in same directory as views.py

**Fix:**
```bash
# Find where views.py is
find /var/www -name "views.py" -path "*/tax_app/*"

# Put pdf_filler.py in SAME directory
cp pdf_filler.py /path/to/same/directory/
```

---

### **Error: "Template not found"**

**Cause:** PDFs not in `templates/pdf_blanks/`

**Fix:**
```bash
# Check Django's BASE_DIR
python manage.py shell
>>> from django.conf import settings
>>> print(settings.BASE_DIR)
# Output: /var/www/django_project/tax_app

# PDFs should be at:
# /var/www/django_project/tax_app/templates/pdf_blanks/*.pdf
```

---

**Follow this guide EXACTLY and imports will work!**
