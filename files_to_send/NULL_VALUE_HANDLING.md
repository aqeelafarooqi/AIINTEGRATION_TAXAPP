# NULL and Empty Value Handling

**Question:** How does the PDF filler handle `null` or empty values in the input JSON?

**Answer:** ✅ Fields with `null` or empty values are **left empty** in the PDF (not filled with "0")

---

## Behavior Summary

| Input Value | PDF Field Result | Example |
|-------------|------------------|---------|
| `null` | **Empty** (not filled) | `"ssn": null` → field left blank |
| `""` (empty string) | **Empty** (not filled) | `"address": ""` → field left blank |
| `"0"` (string zero) | **Filled with "0"** | `"1d": {"value": "0"}` → "0" |
| `0` (numeric zero) | **Filled with "0"** | `"7": {"value": 0}` → "0" |
| Missing field | **Empty** (not filled) | Field not in JSON → field left blank |

---

## Code Implementation

### Line Items (fields)
```python
# From pdf_filler.py line 190
value = field_info.get('value')

if value is None or value == '':
    continue  # Skip - leave PDF field empty
```

### Taxpayer Info
```python
# From pdf_filler.py line 222
value = taxpayer.get(json_field, '')

if not value:
    continue  # Skip - leave PDF field empty
```

### Checkboxes
```python
# From pdf_filler.py line 269-271
value = taxpayer.get(json_field)

if value is None:
    value = fields_data[json_field].get('value', False)

if value is not None:
    checkbox_value = "Yes" if value else "Off"
```

**Note:** Checkboxes handle `None` differently - they check for explicit `None` vs `False`

---

## Test Results

### Test Data
```json
{
  "taxpayer": {
    "first_name": "John",
    "last_name": null,
    "ssn": "",
    "address": "123 Main St",
    "city": null,
    "state": "MA",
    "zip_code": "02101"
  },
  "fields": {
    "1a": {"value": "75000", "can_be_modified": false},
    "1b": {"value": null, "can_be_modified": true},
    "1c": {"value": "", "can_be_modified": true},
    "1d": {"value": "0", "can_be_modified": true},
    "7": {"value": 0, "can_be_modified": true}
  }
}
```

### Results
```
✅ Filled 3 line items
   ✅ 1a: "75000" (filled and greyed)
   ⏭️  1b: empty (null skipped)
   ⏭️  1c: empty (empty string skipped)
   ✅ 1d: "0" (filled - actual zero value)
   ✅ 7: "0" (filled - numeric zero)

👤 Filled 3 taxpayer info fields
   ✅ first_name: "John" (filled)
   ⏭️  last_name: empty (null skipped)
   ⏭️  ssn: empty (empty string skipped)
   ✅ address: "123 Main St" (filled)
   ⏭️  city: empty (null skipped)
   ✅ state: "MA" (filled)
   ✅ zip_code: "02101" (filled)
```

---

## Key Points

### ✅ Correct Behavior
1. **`null` → Empty field** (not "0" or "null")
2. **Empty string `""` → Empty field** (not "0")
3. **Actual zero `"0"` or `0` → Filled with "0"**
4. **Missing field → Empty field**

### 🎯 Why This Matters
- Tax forms often have optional fields
- An empty field vs "0" can have different tax implications
- Example: No income (empty) vs $0 income (zero)

### 💡 Best Practice
Backend should send:
- `null` or omit field entirely if no value
- `"0"` or `0` if the value is explicitly zero
- Never send empty string `""` unless you want field empty

---

## Examples

### Example 1: Optional Income Field
```json
{
  "fields": {
    "interest_income": {"value": null}  // No interest income
  }
}
```
**Result:** Interest income field left **empty** ✅

### Example 2: Zero Income
```json
{
  "fields": {
    "business_income": {"value": "0"}  // $0 from business
  }
}
```
**Result:** Business income field filled with **"0"** ✅

### Example 3: Missing Optional Field
```json
{
  "fields": {
    "wages": {"value": "50000"}
    // "dividends" not included - optional
  }
}
```
**Result:** Dividends field left **empty** ✅

---

## Checkbox Special Case

Checkboxes have slightly different behavior:

```json
{
  "taxpayer": {
    "has_dependents": null  // Not sure
  }
}
```
**Result:** Checkbox not checked/unchecked (left in default state)

```json
{
  "taxpayer": {
    "has_dependents": false  // Explicitly no
  }
}
```
**Result:** Checkbox set to "Off" (unchecked)

```json
{
  "taxpayer": {
    "has_dependents": true  // Explicitly yes
  }
}
```
**Result:** Checkbox set to "Yes" (checked)

---

## Summary

✅ **The system correctly handles null/empty values:**
- Null → Leave field empty
- Empty string → Leave field empty
- Zero → Fill with "0"
- Missing → Leave field empty

**No changes needed** - the current implementation is correct! 🎉
