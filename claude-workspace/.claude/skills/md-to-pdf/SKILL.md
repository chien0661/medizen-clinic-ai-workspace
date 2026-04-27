# /md-to-pdf - Convert Markdown to PDF

## Usage

```bash
/md-to-pdf docs/specs/my-doc.md
/md-to-pdf docs/specs/my-doc.md docs/output/my-doc.pdf
```

**Parameters:**
- `INPUT` - Path to markdown file (relative to workspace root) - REQUIRED
- `OUTPUT` - Path to output PDF file - OPTIONAL (default: same path as input, `.pdf` extension)

## What It Does

Converts a markdown file to a styled PDF with:
- PlantUML code blocks rendered as **images** (fetched from plantuml.com)
- Tables, code blocks, headings styled cleanly
- No header/footer chrome artifacts
- Embedded images (base64) — PDF is self-contained

## Steps

### Step 1: Resolve paths

- `INPUT_PATH` = argument 1 (e.g. `docs/specs/my-doc.md`)
- `OUTPUT_PATH` = argument 2 if provided, else replace `.md` with `.pdf` in INPUT_PATH
- Verify INPUT_PATH exists. If not → print error and stop.

### Step 2: Run export script

```bash
node scripts/export-pdf.js "<INPUT_PATH>" "<OUTPUT_PATH>"
```

The script will:
1. Normalize line endings (CRLF → LF)
2. Extract PlantUML blocks → fetch PNG from plantuml.com → embed as base64
3. Convert markdown to styled HTML
4. Spin up a local HTTP server
5. Print to PDF via headless Chrome (`--no-pdf-header-footer`)
6. Shut down the server

### Step 3: Report result

On success, print:
```
PDF exported: <OUTPUT_PATH>
```

On error, print the error message and suggest fixes:
- `Chrome not found` → install Google Chrome
- `plantuml.com unreachable` → check network; diagram will use URL fallback
- `File not found` → verify the input path is correct

## Requirements

- Google Chrome installed at default path
- Internet access for PlantUML rendering (or diagram falls back to URL)
- Node.js available

## Examples

```bash
# Export with auto output path
/md-to-pdf docs/specs/openapi-integration-guide.md
# → outputs: docs/specs/openapi-integration-guide.pdf

# Export to custom path
/md-to-pdf docs/specs/my-spec.md docs/deliveries/my-spec.pdf
```
