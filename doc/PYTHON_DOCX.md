# Usage
To install and use `python-docx` with **uv** (Astral's high-speed Python toolchain), follow these streamlined steps:

---

## **Installation**
1. **Install `python-docx` via uv**:  
   ```bash
   uv pip install python-docx
   ```
   - Automatically resolves and installs dependencies like `lxml`[4][6].  
   - Uses uv’s cached package management for faster installation (~10-100x speed vs pip)[8].  

2. **Create a virtual environment**:  
   ```bash
   uv venv
   source .venv/bin/activate
   ```
   - No Python pre-installation required: uv downloads Python automatically if missing[1][2].  

---

## **Basic Usage**  
```python
from docx import Document
from docx.shared import Inches

# Create a document
doc = Document()
doc.add_heading("Example Document", 0)

# Add formatted text
paragraph = doc.add_paragraph("Normal text, ")
paragraph.add_run("bold text").bold = True

# Insert a table
table = doc.add_table(rows=2, cols=3)
row = table.rows[0].cells
row[0].text = "Header 1"
row[1].text = "Header 2"

# Save
doc.save("demo.docx")
```

---

## **Key Workflows**  
| Task                  | Command/Code                              |  
|-----------------------|-------------------------------------------|  
| **Install Python**    | `uv python install 3.12` (if needed)[1] |  
| **Upgrade Package**   | `uv pip install --upgrade python-docx`    |  
| **Run Script**        | `uvx script.py` (auto-Python install)[1] |  

---

**Notes**:  
- For existing projects, use `uv pip sync requirements.txt` to install dependencies[8].  
- To disable automatic Python downloads: `uv pip install --no-python`[1].  
- Works seamlessly with `uvx` for script execution and dependency resolution[1][8].

Citations:
[1] https://docs.astral.sh/uv/guides/install-python/
[2] https://www.andreagrandi.it/posts/using-uv-to-install-python-create-virtualenv/
[3] https://python-docx.readthedocs.io
[4] https://python-docx.readthedocs.io/en/latest/user/install.html
[5] https://python-docx.readthedocs.io/en/latest/user/quickstart.html
[6] https://pypi.org/project/python-docx/
[7] https://python-docx.readthedocs.io/en/latest/user/documents.html
[8] https://docs.astral.sh/uv/
[9] https://github.com/astral-sh/uv/issues/7710
[10] https://github.com/astral-sh/uv/issues/6067
[11] https://sarahglasmacher.com/how-to-build-python-package-uv/
[12] https://www.youtube.com/watch?v=i57uYpW5Ng8
[13] https://docs.openwebui.com
[14] https://stackoverflow.com/questions/65634041/writing-into-table-in-word-doc-using-python-docx
[15] https://www.reddit.com/r/learnpython/comments/155itf1/python_docx_messes_up_formatting/
[16] https://docs.astral.sh/uv/guides/projects/
[17] https://www.datacamp.com/tutorial/python-uv
[18] https://flocode.substack.com/p/044-python-environments-again-uv
[19] https://docs.astral.sh/uv/getting-started/installation/
[20] https://pypi.org/project/uv/
[21] https://stackoverflow.com/q/29309202
[22] https://www.reddit.com/r/learnpython/comments/ogt24w/find_replace_in_a_docx_file_using_the_python_docx/

---
Answer from Perplexity: pplx.ai/share

# Rich-Text Formatting

When working with rich-text formatting and document elements in Python-DOCX, the library provides granular control over text styling, image placement, and document structure. Here's a technical breakdown of key features:

---

## **Rich-Text Formatting**  
### **Run-Level Formatting**  
Character formatting is applied at the `Run` level through the `Font` object[1][6]:  
```python
from docx import Document
from docx.shared import Pt

doc = Document()
paragraph = doc.add_paragraph()
run = paragraph.add_run('Formatted text')

# Access font properties
font = run.font
font.name = 'Calibri'
font.size = Pt(12)
```

**Tri-State Properties** (True/False/None):  
```python
font.bold = True     # Force bold
font.italic = False  # Explicitly disable
font.underline = None  # Inherit from style
```

**Advanced Underline Types**:  
```python
from docx.enum.text import WD_UNDERLINE
font.underline = WD_UNDERLINE.DOT_DASH
```

### **Paragraph Formatting**  
Apply styles to entire paragraphs[5][6]:  
```python
paragraph = doc.add_paragraph('Styled text', style='Heading1')
paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
```

---

## **Image Handling**  
### **Basic Image Insertion**  
```python
from docx.shared import Inches

doc.add_picture('image.png', width=Inches(3.5))
```

### **Image Grid Layout**  
Create structured layouts using tables[3]:  
```python
table = doc.add_table(rows=0, cols=3, style="Table Grid")
image_row = table.add_row()

for img_file in image_files:
    cell = image_row.cells[0]
    cell.paragraphs[0].add_run().add_picture(
        img_file, 
        width=Inches(1.46), 
        height=Inches(1.45)
    )
```

**Image Alignment**:  
```python
img_paragraph = doc.paragraphs[-1]
img_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
```

---

## **Document Structure**  
### **Hierarchical Elements**  
| Component      | Method                            | Key Parameters              |
|----------------|-----------------------------------|-----------------------------|
| **Heading**    | `add_heading()`                   | Level (0-9)                 |
| **Page Break** | `add_page_break()`                | None                        |
| **Table**      | `add_table(rows, cols, style)`    | Style names from Word       |

### **Table Population**  
```python
data = [('Qty', 'ID', 'Desc'), (3, '101', 'Spam')]
table = doc.add_table(rows=1, cols=3)

for row in data:
    cells = table.add_row().cells
    for idx, value in enumerate(row):
        cells[idx].text = str(value)
```

---

## **Advanced Features**  
**Mixed-Format Paragraphs**:  
```python
p = doc.add_paragraph()
p.add_run('Normal text, ')
p.add_run('bold text').bold = True
p.add_run(' with ')
p.add_run('color').font.color.rgb = RGBColor(0xFF, 0x00, 0x00)
```

**Style Inheritance**[1][6]:  
- Document styles form hierarchy (Normal -> Heading -> etc.)
- Explicit formatting overrides inherited styles
- Use `None` to revert to style defaults

**XML-Level Access** (For Edge Cases):  
```python
document._element.xml  # Access raw XML tree
```

---

The library's strength lies in its hierarchical document model, where formatting cascades from document styles to individual runs. For image-heavy documents, combining table layouts with precise dimension control (using `Inches` or `Cm`) enables professional formatting while maintaining aspect ratios[3][5]. The tri-state formatting system allows both explicit styling and style inheritance management[1][6].

Citations:
[1] https://python-docx.readthedocs.io/en/latest/user/text.html
[2] https://gist.github.com/documentprocessing/cf556694ddfc86f175439ca46183dbe4
[3] https://mlhive.com/2022/07/working-with-images-in-python-docx
[4] https://python-docx.readthedocs.io/en/latest/api/document.html
[5] https://python-docx.readthedocs.io/en/latest/user/quickstart.html
[6] https://python-docx.readthedocs.io
[7] https://python-docx.readthedocs.io/en/latest/user/styles-understanding.html
[8] https://www.ghostwriter.wiki/features/reporting/templating-and-rich-text-fields
[9] https://www.reddit.com/r/learnpython/comments/155itf1/python_docx_messes_up_formatting/
[10] https://python-docx.readthedocs.io/en/latest/dev/analysis/features/shapes/picture.html
[11] https://github.com/python-openxml/python-docx/issues/981
[12] https://community.safe.com/transformers-9/add-pictures-to-table-in-word-doc-using-python-docx-in-pythoncaller-19543
[13] https://github.com/python-openxml/python-docx/issues/216
[14] https://docxtpl.readthedocs.io
[15] https://stackoverflow.com/questions/42143575/how-to-apply-word-styles-to-richtext-object-docxtpl-library
[16] https://stackoverflow.com/questions/69124345/how-to-parse-and-preserve-text-formatting-python-docx
[17] https://python-docx.readthedocs.io/en/latest/dev/analysis/features/text/font.html
[18] https://github.com/elapouya/python-docx-template/issues/42
[19] https://github.com/python-openxml/python-docx/issues/692
[20] https://stackoverflow.com/questions/32932230/add-an-image-in-a-specific-position-in-the-document-docx
[21] https://www.e-iceblue.com/Tutorials/Python/Spire.Doc-for-Python/Program-Guide/Image-and-Shape/Python-Insert-Images-in-Word.html

---
Answer from Perplexity: pplx.ai/share
