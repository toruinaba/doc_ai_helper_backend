"""
Quartoプロセッサーのテストモジュール。
"""

import pytest
from doc_ai_helper_backend.services.document.processors.quarto import QuartoProcessor
from doc_ai_helper_backend.models.document import DocumentContent
from doc_ai_helper_backend.models.frontmatter import ExtendedDocumentMetadata
from doc_ai_helper_backend.models.link_info import LinkInfo


class TestQuartoProcessor:
    """QuartoProcessorクラスのテスト"""

    def setup_method(self):
        """テストメソッドの前処理"""
        self.processor = QuartoProcessor()

    def test_process_content_with_frontmatter(self):
        """フロントマター付きQuartoコンテンツの処理をテスト"""
        content = """---
title: "Test Document"
author: "Test Author"
format: html
execute:
  echo: false
---

# Test Document

This is a test Quarto document.

```{python}
#| label: fig-plot
#| fig-cap: "Test Plot"

import matplotlib.pyplot as plt
plt.plot([1, 2, 3])
```

::: {.callout-note}
This is a note callout.
:::
"""
        
        result = self.processor.process_content(content, "test.qmd")
        
        assert isinstance(result, DocumentContent)
        assert result.encoding == "utf-8"
        # フロントマターが除去されていることを確認
        assert not result.content.startswith("---")
        assert "# Test Document" in result.content
        # Quarto機能が拡張処理されていることを確認
        assert "```python" in result.content  # コードブロックが処理されている
        assert "📝 Note" in result.content  # Calloutが処理されている

    def test_process_content_without_frontmatter(self):
        """フロントマターなしQuartoコンテンツの処理をテスト"""
        content = """# Simple Quarto Document

![Figure caption](image.png){#fig-test}

This is simple content.
"""
        
        result = self.processor.process_content(content, "simple.qmd")
        
        assert isinstance(result, DocumentContent)
        assert "# Simple Quarto Document" in result.content
        assert "Figure test:" in result.content

    def test_extract_metadata_basic(self):
        """基本的なメタデータ抽出をテスト"""
        content = """---
title: "Research Paper"
author: "John Doe"
date: "2024-01-15"
format: html
execute:
  echo: false
bibliography: references.bib
---

# Research Paper

Content here.
"""
        
        metadata = self.processor.extract_metadata(content, "research.qmd")
        
        assert isinstance(metadata, ExtendedDocumentMetadata)
        assert metadata.title == "Research Paper"
        assert metadata.author == "John Doe"
        assert metadata.date == "2024-01-15"
        assert metadata.filename == "research.qmd"
        assert metadata.extension == "qmd"
        
        # Quarto固有のメタデータをチェック
        assert "quarto" in metadata.extra
        quarto_meta = metadata.extra["quarto"]
        assert quarto_meta["format"] == "html"
        assert quarto_meta["execute"]["echo"] == False
        assert quarto_meta["bibliography"] == "references.bib"

    def test_extract_metadata_with_title_from_content(self):
        """コンテンツからタイトルを抽出するテスト"""
        content = """---
author: "Test Author"
---

# Extracted Title

Some content here.
"""
        
        metadata = self.processor.extract_metadata(content, "test.qmd")
        
        assert metadata.title == "Extracted Title"
        assert metadata.author == "Test Author"

    def test_extract_links_basic(self):
        """基本的なリンク抽出をテスト"""
        content = """# Test Document

This is a [regular link](https://example.com) and an ![image](image.png).

Also a [relative link](../other/file.qmd).
"""
        
        links = self.processor.extract_links(content, "test.qmd")
        
        assert len(links) == 3
        
        # 通常のリンク
        regular_link = next(link for link in links if link.text == "regular link")
        assert regular_link.url == "https://example.com"
        assert not regular_link.is_image
        assert regular_link.is_external
        
        # 画像リンク
        image_link = next(link for link in links if link.is_image)
        assert image_link.url == "image.png"
        assert image_link.text == "image"
        
        # 相対リンク
        relative_link = next(link for link in links if link.text == "relative link")
        assert relative_link.url == "../other/file.qmd"
        assert not relative_link.is_external

    def test_extract_links_quarto_figures(self):
        """Quarto図表キャプション付きリンク抽出をテスト"""
        content = """# Test Document

![Test plot](plot.png){#fig-test}

![Another figure with caption](chart.svg){#fig-chart .custom-class width="80%"}

Regular ![image](normal.jpg) without Quarto syntax.
"""
        
        links = self.processor.extract_links(content, "test.qmd")
        
        # Quarto図表として認識されるもの
        quarto_figs = [link for link in links if link.text.startswith("Figure:")]
        assert len(quarto_figs) == 2
        
        # 通常の画像として認識されるもの
        normal_images = [link for link in links if link.is_image and not link.text.startswith("Figure:")]
        assert len(normal_images) == 1
        assert normal_images[0].text == "image"

    def test_transform_links(self):
        """リンク変換をテスト"""
        content = """# Test Document

[Link to file](../other/file.qmd)
![Image](image.png)
[External](https://example.com)
"""
        
        transformed = self.processor.transform_links(
            content, 
            "docs/test.qmd", 
            "https://api.example.com/docs",
            service="github",
            owner="user",
            repo="repo",
            ref="main"
        )
        
        # リンクが変換されていることを確認
        assert "https://api.example.com" in transformed
        assert "https://example.com" in transformed  # 外部リンクは変更されない

    def test_enhance_figure_captions(self):
        """図表キャプション拡張をテスト"""
        content = "![Test figure](image.png){#fig-test}"
        
        result = self.processor._enhance_figure_captions(content)
        
        assert "Figure test: Test figure" in result

    def test_enhance_code_blocks(self):
        """コードブロック拡張をテスト"""
        content = """```{python}
#| label: fig-plot
#| fig-cap: "Test Plot"

print("Hello")
```"""
        
        result = self.processor._enhance_code_blocks(content)
        
        assert "```python (fig-plot)" in result or "python" in result

    def test_enhance_callouts(self):
        """Callout拡張をテスト"""
        content = """::: {.callout-note}
This is a note.
:::

::: {.callout-warning}
This is a warning.
:::"""
        
        result = self.processor._enhance_callouts(content)
        
        assert "📝 Note" in result
        assert "⚠️ Warning" in result
        assert "This is a note." in result
        assert "This is a warning." in result

    def test_enhance_table_captions(self):
        """表キャプション拡張をテスト"""
        content = ": Sample table {#tbl-sample}"
        
        result = self.processor._enhance_table_captions(content)
        
        assert "**Table sample**: Sample table" in result

    def test_analyze_quarto_content(self):
        """Quartoコンテンツ分析をテスト"""
        content = """
![Figure 1](fig1.png){#fig-one}
![Figure 2](fig2.png){#fig-two}

```{python}
print("code")
```

::: {.callout-note}
Note here
:::

$$E = mc^2$$

: Table caption {#tbl-data}
"""
        
        stats = self.processor._analyze_quarto_content(content)
        
        assert stats["figure_count"] == 2
        assert stats["code_block_count"] == 1
        assert stats["callout_count"] == 1
        assert stats["math_count"] == 1
        assert stats["table_count"] == 1

    def test_extract_quarto_metadata(self):
        """Quarto固有メタデータ抽出をテスト"""
        frontmatter = {
            "title": "Test",
            "format": {"html": {"theme": "default"}},
            "execute": {"echo": False},
            "bibliography": "refs.bib"
        }
        content = "![Test](test.png){#fig-test}"
        
        result = self.processor._extract_quarto_metadata(frontmatter, content)
        
        assert "quarto" in result
        quarto_meta = result["quarto"]
        assert "format" in quarto_meta
        assert "execute" in quarto_meta
        assert "bibliography" in quarto_meta
        assert quarto_meta["figure_count"] == 1

    def test_is_quarto_figure(self):
        """Quarto図表判定をテスト"""
        line = "![Test figure](image.png){#fig-test}"
        
        # 画像部分の範囲
        img_span = (0, 25)  # ![Test figure](image.png) の範囲
        
        result = self.processor._is_quarto_figure(line, img_span)
        
        assert result == True

    def test_extract_title_from_content(self):
        """コンテンツからタイトル抽出をテスト"""
        content = """---
author: "Test"
---

# Main Title

Some content.

## Subtitle
"""
        
        title = self.processor._extract_title_from_content(content)
        
        assert title == "Main Title"

    def test_extract_title_from_content_no_heading(self):
        """見出しがない場合のタイトル抽出をテスト"""
        content = """---
author: "Test"
---

Just some content without headings.
"""
        
        title = self.processor._extract_title_from_content(content)
        
        assert title == ""