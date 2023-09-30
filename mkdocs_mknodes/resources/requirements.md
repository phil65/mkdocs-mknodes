## Plugin resources

### Files

All files connected to the node tree:

{{ page_mapping | MkPrettyPrint }}

### Plugins

Plugins used by the tree nodes:

{{ resources.plugins | MkPrettyPrint }}

### CSS

CSS used by the tree nodes:

{{ resources.css | MkPrettyPrint }}

### JS

JS used by the tree nodes:

{{ resources.js | MkPrettyPrint }}

### Markdown extensions

Extensions used by the tree nodes:

{{ resources.markdown_extensions | dump_yaml |  MkCode(language="yaml") }}
