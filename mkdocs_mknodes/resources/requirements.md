## Plugin requirements

### Files

All files connected to the node tree:

{{ page_mapping | MkPrettyPrint }}

### Plugins

Plugins used by the tree nodes:

{{ requirements.plugins | MkPrettyPrint }}

### CSS

CSS used by the tree nodes:

{{ requirements.css | MkPrettyPrint }}

### JS

JS used by the tree nodes:

{{ requirements.js | MkPrettyPrint }}

### Markdown extensions

Extensions used by the tree nodes:

{{ requirements.markdown_extensions | dump_yaml |  MkCode(language="yaml") }}
