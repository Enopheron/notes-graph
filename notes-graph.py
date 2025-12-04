#!/usr/bin/env python3

from pathlib import Path
import re
import json

# ========== Configuration ==========
DIRECTORY = Path("notes")
OUTPUT_HTML = Path("graph.html")

TAG_COLORS = {
    "group": "#993366",
    "info": "#333333",
    "not-use": "#999999",
    "skript": "#339966",
    "soft": "#996633",
}
DEFAULT_COLOR = "#89CFF0"
# ==================================

MD_EXTS = {".md", ".qmd"}

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Notes graph</title>
  <script type="text/javascript" src="https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.js"></script>
  <link href="https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.css" rel="stylesheet" />
  <style>
    :root{
      --bg: #252627;
      --panel: #2b2c2d;
      --text: #999999;
      --muted: #b0b0b0;
      --border: #3a3a3a;
      --control-bg: #2b2c2d;
      --edge-color: #666666;
    }
    html,body { height:100%; margin: 0; font-family: Arial, Helvetica, sans-serif; background: var(--bg); color: var(--text); }
    #topbar { display:flex; gap:10px; padding:8px; align-items:center; border-bottom:1px solid var(--border); background: var(--panel); }
    #controls { width: 320px; height: calc(100vh - 50px); overflow:auto; border-right:1px solid var(--border); padding:10px; box-sizing:border-box; background: var(--panel); }
    #network { width: calc(100% - 320px); height: calc(100vh - 50px); background: var(--bg); }
    #layout { display:flex; height: calc(100vh - 50px); }
    .tag-row { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
    label.tag-label { flex:1; word-break:break-all; display:flex; align-items:center; gap:8px; color:var(--text); }
    .tag-swatch { width:14px; height:14px; border-radius:3px; display:inline-block; border:1px solid rgba(0,0,0,0.15); }
    .small { font-size: 12px; color:var(--muted); }
    input[type="text"] { padding:6px; width:600px; background:var(--control-bg); color:var(--text); border:1px solid var(--border); }
    button { padding:6px 10px; background:var(--control-bg); color:var(--text); border:1px solid var(--border); cursor:pointer; }
    .section { margin-bottom:12px; }
    .backlinks-list { padding-left: 12px; }
    .backlink-item { margin:6px 0; cursor: pointer; color: var(--text); }
    .backlink-item:hover { text-decoration: underline; color: #ffffff; }
  </style>
</head>
<body>
<div id="topbar">
  <input id="searchInput" type="text" placeholder="Search: exact name (example: python). Enter = find, Esc = reset" autocomplete="off" />
</div>
<div id="layout">
  <div id="controls">
    <div class="section">
      <h3>Tags</h3>
      <div id="tagsContainer"></div>
      <div style="margin-top:8px;">
        <button id="selectAllTags">Select all</button>
        <button id="deselectAllTags">Deselect all</button>
      </div>
    </div>

    <div class="section">
      <h3>Backlinks</h3>
      <div id="backlinksContainer" class="backlinks-list small">Click a node to see incoming links.</div>
    </div>

    <div class="section">
      <h4>Info</h4>
      <div id="info" class="small"></div>
    </div>
  </div>

  <div id="network"></div>
</div>

<script>
var rawNodes = __NODES_JSON__;
var rawEdges = __EDGES_JSON__;
var nameToIds = __NAME_TO_IDS_JSON__;
var incomingMap = __INCOMING_JSON__;

var allTags = Array.from(new Set(rawNodes.flatMap(n => n.tags || []))).sort();

var nodesDS = new vis.DataSet(rawNodes.map(function(n){
  return {
    id: n.id, label: n.title || n.file, title: n.title || n.file,
    tags: n.tags || [], url: n.url, color: n.color, hidden: false, file: n.file
  };
}));

var edgesDS = new vis.DataSet(rawEdges.map(function(e){
  return { id: e.id, from: e.from, to: e.to, hidden: false, color: { color: "#666666" } };
}));

var neighbors = {};
rawNodes.forEach(function(n){ neighbors[n.id] = new Set(); });
rawEdges.forEach(function(e){
  if (neighbors[e.from]) neighbors[e.from].add(e.to);
  if (neighbors[e.to]) neighbors[e.to].add(e.from);
});

var container = document.getElementById('network');
var data = { nodes: nodesDS, edges: edgesDS };
var options = {
  nodes: { shape: 'dot', size: 18, font: { color: '#999999' } },
  edges: { smooth: true, color: { color: "#666666" }, arrows: { to: { enabled: false } } },
  physics: { stabilization: true },
  interaction: { hover: true, multiselect: true, tooltipDelay: 100 }
};
var network = new vis.Network(container, data, options);

network.on("doubleClick", function (params) {
    if (params.nodes && params.nodes.length > 0) {
        var node = nodesDS.get(params.nodes[0]);
        if (node && node.url) window.open(node.url);
    }
});

network.on("click", function(params) {
  var backlinksContainer = document.getElementById('backlinksContainer');
  backlinksContainer.innerHTML = "";
  if (params.nodes && params.nodes.length > 0) {
    var nodeId = params.nodes[0];
    var title = nodesDS.get(nodeId).title || nodesDS.get(nodeId).label || "";
    var header = document.createElement('div');
    header.innerHTML = "<b>" + escapeHtml(title) + "</b>";
    backlinksContainer.appendChild(header);

    var incoming = incomingMap[nodeId] || incomingMap[String(nodeId)] || [];
    if (!incoming || incoming.length === 0) {
      var none = document.createElement('div'); none.className = "small"; none.textContent = "No incoming links.";
      backlinksContainer.appendChild(none);
    } else {
      incoming.forEach(function(srcId){
        var srcNode = nodesDS.get(srcId);
        if (!srcNode) return;
        var item = document.createElement('div');
        item.className = "backlink-item";
        item.textContent = (srcNode.title || srcNode.label);
        item.addEventListener('click', function(){ if (srcNode.url) window.open(srcNode.url); });
        backlinksContainer.appendChild(item);
      });
    }
  } else {
    backlinksContainer.innerHTML = "Click a node to see incoming links.";
  }
});

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, function (s) {
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[s];
  });
}

var tagsContainer = document.getElementById('tagsContainer');
var activeTagFilter = new Set(allTags);

function buildTagsUI() {
  tagsContainer.innerHTML = "";
  if (allTags.length === 0) {
    tagsContainer.innerHTML = "<div class='small'>No tags found.</div>";
    return;
  }
  allTags.forEach(function(tag){
    var row = document.createElement('div'); row.className = "tag-row";
    var cb = document.createElement('input'); cb.type = "checkbox"; cb.checked = true; cb.dataset.tag = tag;
    cb.addEventListener('change', onTagChange);
    var lbl = document.createElement('label'); lbl.className = "tag-label";
    var sw = document.createElement('span'); sw.className = "tag-swatch";
    var swcolor = "#89CFF0";
    for (var i=0;i<rawNodes.length;i++){ var nn = rawNodes[i]; if (nn.tags && nn.tags.length>0 && nn.tags[0]===tag){ swcolor = nn.color; break; } }
    sw.style.background = swcolor;
    var tspan = document.createElement('span'); tspan.textContent = tag;
    lbl.appendChild(sw); lbl.appendChild(tspan);
    row.appendChild(cb); row.appendChild(lbl);
    tagsContainer.appendChild(row);
  });
}

function onTagChange(e) {
  var tag = e.target.dataset.tag;
  if (e.target.checked) activeTagFilter.add(tag); else activeTagFilter.delete(tag);
}

document.getElementById('selectAllTags').addEventListener('click', function(){
  activeTagFilter = new Set(allTags);
  Array.from(tagsContainer.querySelectorAll('input[type="checkbox"]')).forEach(cb=>cb.checked=true);
});
document.getElementById('deselectAllTags').addEventListener('click', function(){
  activeTagFilter = new Set();
  Array.from(tagsContainer.querySelectorAll('input[type="checkbox"]')).forEach(cb=>cb.checked=false);
});

var searchInput = document.getElementById('searchInput');
var lastSearch = "";

searchInput.addEventListener('keydown', function(e){
  if (e.key === 'Enter') { e.preventDefault(); lastSearch = searchInput.value.trim(); applyFilters(); }
  else if (e.key === 'Escape') { e.preventDefault(); searchInput.value = ""; lastSearch = ""; applyFilters(); }
});

function applyFilters() {
  var s = lastSearch.trim().toLowerCase();
  var nodesToShowBySearch = null;

  if (s.length) {
    if (nameToIds.hasOwnProperty(s)) {
      nodesToShowBySearch = new Set();
      nameToIds[s].forEach(function(id){
        nodesToShowBySearch.add(id);
        var incoming = incomingMap[id] || incomingMap[String(id)] || [];
        if (incoming && incoming.length) incoming.forEach(src=>nodesToShowBySearch.add(src));
      });
    } else {
      var matched = new Set();
      nodesDS.forEach(function(n){ var txt = ((n.title||"")+" "+(n.label||"")).toLowerCase(); if (txt.indexOf(s)!==-1) matched.add(n.id); });
      if (matched.size) {
        nodesToShowBySearch = new Set();
        matched.forEach(function(mid){ nodesToShowBySearch.add(mid); if (neighbors[mid]) neighbors[mid].forEach(nb=>nodesToShowBySearch.add(nb)); });
      } else { nodesToShowBySearch = new Set(); }
    }
  }

  nodesDS.forEach(function(n){
    var passTag = !activeTagFilter.size || (n.tags && n.tags.some(t=>activeTagFilter.has(t)));
    // important: if node is part of search result, show it regardless of tag filter
    if (nodesToShowBySearch && nodesToShowBySearch.has(n.id)) passTag = true;
    var passSearch = nodesToShowBySearch === null || nodesToShowBySearch.has(n.id);
    nodesDS.update({id: n.id, hidden: !(passTag && passSearch)});
  });

  edgesDS.forEach(function(e){
    var fromNode = nodesDS.get(e.from);
    var toNode = nodesDS.get(e.to);
    edgesDS.update({id: e.id, hidden: (fromNode && fromNode.hidden) || (toNode && toNode.hidden)});
  });

  // If the user provided an exact search term that matches nameToIds, auto-show backlinks panel
  var backlinksContainer = document.getElementById('backlinksContainer');
  if (s.length && nameToIds.hasOwnProperty(s)) {
    backlinksContainer.innerHTML = "";
    var ids = nameToIds[s];
    ids.forEach(function(id){
      var node = nodesDS.get(id);
      if (!node) return;
      var header = document.createElement('div');
      header.innerHTML = "<b>" + escapeHtml(node.title || node.label) + "</b>";
      backlinksContainer.appendChild(header);
      var incoming = incomingMap[id] || incomingMap[String(id)] || [];
      if (!incoming || incoming.length === 0) {
        var none = document.createElement('div'); none.className = "small"; none.textContent = "No incoming links.";
        backlinksContainer.appendChild(none);
      } else {
        incoming.forEach(function(srcId){
          var srcNode = nodesDS.get(srcId);
          if (!srcNode) return;
          var item = document.createElement('div');
          item.className = "backlink-item";
          item.textContent = (srcNode.title || srcNode.label);
          item.addEventListener('click', function(){ if (srcNode.url) window.open(srcNode.url); });
          backlinksContainer.appendChild(item);
        });
      }
    });
  }

  updateInfo();
}

function updateInfo() {
  var shown = nodesDS.get({filter: n => !n.hidden});
  document.getElementById('info').innerText = "Visible nodes: " + shown.length + " of " + nodesDS.length + ".";
}

buildTagsUI();
applyFilters();
</script>
</body>
</html>
"""

_link_pattern = re.compile(r'\[.*?\]\(([^)]+)\)')

def find_md_files(root: Path):
    if not root.is_dir(): return []
    return [p for p in sorted(root.iterdir()) if p.is_file() and p.suffix in MD_EXTS]

def extract_links(path: Path):
    """
    Возвращает список ссылок (targets) из markdown-файла без фрагментов (#...) и без query (?...).
    Отфильтровывает внешние URL (http://...) и возвращает только те targets, у которых расширение в MD_EXTS.
    """
    try: txt = path.read_text(encoding="utf-8")
    except Exception: return []
    results = []
    for m in _link_pattern.findall(txt):
        target = m.split('#', 1)[0].split('?', 1)[0].strip()
        if not target:
            continue
        # skip external urls (http, https, mailto, etc.)
        if re.match(r'^[a-zA-Z]+://', target):
            continue
        # normalize ./ and other simple bits
        target_path = Path(target)
        if target_path.suffix in MD_EXTS:
            results.append(target)
        else:
            # попытка: если ссылка без расширения, добавить возможные расширения
            for ext in MD_EXTS:
                cand = str(target) + ext
                if Path(cand).suffix in MD_EXTS:
                    results.append(cand)
                    break
    # уникальность + порядок
    seen = set()
    out = []
    for r in results:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out

def parse_frontmatter(path: Path):
    try: txt = path.read_text(encoding="utf-8")
    except Exception: return path.stem, []
    title, tags = None, []
    if txt.startswith("---"):
        parts = txt.split("---", 2)
        if len(parts) >= 3:
            yaml = parts[1]
            m = re.search(r'^\s*title\s*:\s*(.+)\s*$', yaml, flags=re.MULTILINE)
            if m: title = m.group(1).strip().strip('"').strip("'")
            m_tags = re.search(r'^\s*tags\s*:\s*(\n(?:\s*-\s*.+\n?)*)', yaml, flags=re.MULTILINE)
            if m_tags:
                tags = [it.strip().strip('"').strip("'") for it in re.findall(r'-\s*(.+)', m_tags.group(1)) if it.strip()]
            else:
                m_inline = re.search(r'^\s*tags\s*:\s*\[(.*?)\]', yaml, flags=re.MULTILINE)
                if m_inline:
                    tags = [x.strip().strip('"').strip("'") for x in m_inline.group(1).split(',') if x.strip()]
    if not title: title = path.stem
    return title, tags

def build_graph(root: Path):
    files = find_md_files(root)
    abs_files = [p.resolve() for p in files]
    index = {p: i for i, p in enumerate(abs_files)}

    nodes = []
    for p, i in index.items():
        title, tags = parse_frontmatter(p)
        color = TAG_COLORS.get(tags[0], DEFAULT_COLOR) if tags else DEFAULT_COLOR
        nodes.append({"id": i, "file": p.name, "title": title, "tags": tags, "url": f"file://{p}", "color": color})

    # Build edges, avoiding duplicates:
    edges = []
    seen_dir = set()        # directed pairs we've already seen (a,b)
    undirected_seen = set() # unordered pair keys to ensure single visual edge per pair

    for p in abs_files:
        a = index[p]
        for link in extract_links(p):
            # link already has fragments removed in extract_links
            cand1 = (p.parent / link).resolve()
            cand2 = (root / link).resolve()
            resolved = cand1 if cand1 in index else (cand2 if cand2 in index else None)
            if resolved is None:
                continue
            b = index[resolved]
            # --- ADDED: skip self-links (link to the same file or its heading) ---
            if a == b:
                continue
            if (a, b) in seen_dir:
                continue
            seen_dir.add((a, b))
            pair = tuple(sorted((a, b)))
            if pair in undirected_seen:
                continue
            undirected_seen.add(pair)
            edges.append({"id": f"e_{len(edges)}", "from": pair[0], "to": pair[1]})

    # name -> ids mapping (by file stem, file name, and title) for exact search
    name_to_ids = {}
    for n in nodes:
        stem = Path(n["file"]).stem.lower()
        name_to_ids.setdefault(stem, []).append(n["id"])
        name_to_ids.setdefault(n["file"].lower(), []).append(n["id"])
        if n.get("title"):
            name_to_ids.setdefault(n["title"].lower(), []).append(n["id"])
    # uniquify lists
    for k, v in list(name_to_ids.items()):
        name_to_ids[k] = sorted(list(dict.fromkeys(v)))

    # incoming: build from directed set so backlinks remain accurate (unique)
    incoming = {}
    for src, dst in seen_dir:
        incoming.setdefault(dst, set()).add(src)
    # convert sets to lists for JSON
    incoming = {k: sorted(list(v)) for k, v in incoming.items()}

    return nodes, edges, name_to_ids, incoming

def main():
  nodes, edges, name_to_ids, incoming = build_graph(DIRECTORY)
  
  nodes_json = json.dumps(nodes, ensure_ascii=False)
  edges_json = json.dumps(edges, ensure_ascii=False)
  name_json = json.dumps(name_to_ids, ensure_ascii=False)
  incoming_json = json.dumps(incoming, ensure_ascii=False)
  
  html = HTML_TEMPLATE.replace("__NODES_JSON__", nodes_json)\
                      .replace("__EDGES_JSON__", edges_json)\
                      .replace("__NAME_TO_IDS_JSON__", name_json)\
                      .replace("__INCOMING_JSON__", incoming_json)
  
  OUTPUT_HTML.write_text(html, encoding="utf-8")
  print(f"Wrote {OUTPUT_HTML} from {DIRECTORY}")

if __name__ == "__main__":
    main()
