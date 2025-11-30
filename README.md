# Notes Graph Generator

A Python tool to visualize your Markdown (and Quarto `.qmd`) notes as an interactive network graph with backlinks and tag-based filtering. The output is a standalone HTML file you can open in any browser.

---

## Features

- Parses a directory of Markdown / Quarto files and extracts:
  - Titles
  - Tags
  - Links between notes
- Generates an interactive HTML graph with:
  - Clickable nodes
  - Backlinks panel
  - Tag-based filtering
  - Live search
- Customizable tag colors

---

## Installation

Requires Python 3.8+.

```bash
git clone https://github.com/enopheron/notes-graph.git
cd notes-graph
````

> This script currently uses only the standard library (`pathlib`, `re`, `json`).

---

## Configuration

The main variables to configure are:

### `DIRECTORY`

Path to your notes folder.

```python
DIRECTORY = Path("/path/to/your/notes")
```

The script will recursively scan this directory for `.md` and `.qmd` files.

---

### `OUTPUT_HTML`

Path to the generated HTML file.

```python
OUTPUT_HTML = Path("path/to/output/graph.html")
```

> Make sure the parent folder exists, or Python will raise an error.

---

### `TAG_COLORS`

Dictionary mapping tags to colors for the graph nodes.
Any tag not listed here will use `DEFAULT_COLOR`.

```python
TAG_COLORS = {
    "project": "#993366",
    "reference": "#333333",
}
DEFAULT_COLOR = "#89CFF0"
```

---

## Usage

Simply run:

```bash
python3 notes_graph.py
```

The script will:

1. Scan `DIRECTORY` for Markdown / Quarto files.
2. Parse titles, tags, and links.
3. Generate `OUTPUT_HTML` with an interactive visualization.

Open the resulting HTML in your browser to explore your notes network.

---

## How It Works

* Each note is represented as a **node**.
* Links between notes create **edges**.
* Tags can be filtered on the side panel.
* Double-click a node to open the file in your system.
* The search box supports:

  * **Exact name search** (press Enter)
  * **Reset search** (press Escape)

---

## Example

If your directory structure is:

```
notes/
├─ python.md
├─ javascript.md
├─ projects/
│  ├─ project1.md
│  └─ project2.md
```

The generated graph will show nodes for each file, edges for links, and colored tags based on your `TAG_COLORS` mapping.

---

## Customization

* Change colors for specific tags via `TAG_COLORS`.
* Change default node color with `DEFAULT_COLOR`.
* The HTML template can be edited in `HTML_TEMPLATE` to adjust styles, layout, or JS behavior.

---

## License

MIT License.
