import base64
import re
import zlib

from marko.block import BlockElement


class RenderableMermaidBlock(BlockElement):

    priority = 6  # Try before the html block parser

    START_TOKEN = re.compile(r"<!-- gfmd-start -->")
    END_TOKEN = "<!-- gfmd-end -->"
    CODE_START_TOKEN = "```"
    CODE_END_TOKEN = "```"

    SUPPORTED_TYPES = (
        "mermaid",
        "plantuml"
    )

    def __init__(self, match):
        markup_language, mermaid_src = match
        self.markup_language = markup_language
        self.mermaid_src = mermaid_src

    @classmethod
    def match(cls, source):
        m = source.expect_re(cls.START_TOKEN)
        if not m:
            return None
        return m

    @classmethod
    def parse(cls, source):
        source.next_line()
        source.consume()

        mermaid_lines = []

        while not source.exhausted:
            line = source.next_line()
            if line is None:
                break
            source.consume()

            # Parse the inner mermaid fenced block
            if cls.CODE_START_TOKEN in line:

                # Check if this is a supported language
                markup_language = None
                for language in cls.SUPPORTED_TYPES:
                    if language in line:
                        markup_language = language

                if not markup_language:
                    continue # Skip this code block

                # Consume the code block
                while not source.exhausted:
                    line = source.next_line()
                    if line is None:
                        break
                    source.consume()
                    if cls.CODE_END_TOKEN in line:
                        break
                    else:
                        mermaid_lines.append(line)

            if cls.END_TOKEN in line:
                break

        # Return just the mermaid diagram source
        return markup_language, "".join(mermaid_lines).strip()


class RenderableMermaidBlockRendererMixin(object):

    template = """<!-- gfmd-start -->
![{language} diagram]({image_link})

<details>
<summary><sup><sub>Diagram source code</sub></sup></summary>

```{language}
{input_mermaid}
```
</details>
<!-- gfmd-end -->
"""

    def render_renderable_mermaid_block(self, element):
        """Markdown render!"""
        link = self.make_kroki_image_link(element.markup_language, element.mermaid_src)
        return self.template.format(input_mermaid=element.mermaid_src, image_link=link, language=element.markup_language)

    def make_kroki_image_link(self, language, src):
        """See https://kroki.io/#how."""
        diagram = base64.urlsafe_b64encode(
            zlib.compress(src.encode("utf-8"), 9)
        ).decode("utf-8")
        return f"https://kroki.io/{language}/svg/{diagram}"


class RenderableMermaid:
    elements = [RenderableMermaidBlock]
    renderer_mixins = [RenderableMermaidBlockRendererMixin]
