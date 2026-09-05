# Codeblock Styling

The Obsidian Vault makes use of codeblocks to display code snippets. Jekyll makes use of a tool called
[Rouge](https://github.com/rouge-ruby/rouge) to highlight these codeblocks. Rouge is a Ruby gem that supports many
languages, but not all of them — for example, it does not support the `mermaid` language for diagrams.

Rouge reuses Pygments' token naming convention when annotating Jekyll-generated HTML. Each lexical element in a
codeblock gets wrapped in a `<span>` with one of the abbreviations below, which our syntax-highlighting CSS then colors:

| Abbreviation | Meaning                                  |
|--------------|------------------------------------------|
| `o`          | Operator (`\|`, `-`, `/`)                |
| `n`          | Name (identifiers, plain words)          |
| `mi`         | Number, Integer                          |
| `p`          | Punctuation (`.`, `,`)                   |
| `k`          | Keyword                                  |
| `ow`         | Operator, Word (e.g. `and`, `or`, `not`) |
| `s`          | String                                   |
| `c` / `c1`   | Comment                                  |
| `nb`         | Name, Builtin                            |

The docker entrypoint script generates `syntax-highlighting.css` via `rougify` on container start (skipping generation
if the file already exists), so codeblock colors are ready before Jekyll builds the site. The stylesheet still needs to
be linked in the site's `<head>` — see `assets/css/syntax-highlighting.css`.