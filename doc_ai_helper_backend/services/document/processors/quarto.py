"""
Quartoドキュメント専用プロセッサー。

QuartoはMarkdownの拡張版で、科学的文書作成に特化した機能を提供します。
このプロセッサーはQuarto固有の機能（図表キャプション、コードブロック、
ダイアグラム、数式、引用等）の処理とメタデータ抽出を行います。
"""

import os
import re
from typing import Dict, List, Optional, Any, Tuple

from doc_ai_helper_backend.models.document import DocumentContent, DocumentType
from doc_ai_helper_backend.models.link_info import LinkInfo
from doc_ai_helper_backend.models.frontmatter import ExtendedDocumentMetadata
from doc_ai_helper_backend.services.document.processors.base import (
    DocumentProcessorBase,
)
from doc_ai_helper_backend.services.document.utils.frontmatter import (
    parse_frontmatter,
)
from doc_ai_helper_backend.services.document.utils.links import (
    LinkTransformer,
)


class QuartoProcessor(DocumentProcessorBase):
    """Quarto文書専用ドキュメントプロセッサー"""

    # Markdownリンクパターン [text](url)
    MD_LINK_PATTERN = r"\[([^\]]+)\]\(([^)]+)\)"

    # イメージパターン ![alt](url)
    IMG_LINK_PATTERN = r"!\[([^\]]*)\]\(([^)]+)\)"

    # Quartoの図表キャプション付きイメージパターン
    QUARTO_FIG_PATTERN = r"!\[([^\]]*)\]\(([^)]+)\)\s*\{[^}]*#fig-[^}]*\}"
    
    # Quartoのコードブロックパターン
    QUARTO_CODE_BLOCK_PATTERN = r"```\{([^}]+)\}\s*\n(.*?)\n```"
    
    # Quartoのcalloutパターン  
    QUARTO_CALLOUT_PATTERN = r"::: \{\.callout-([^}]+)\}(.*?):::"
    
    # Quartoの数式パターン
    QUARTO_MATH_PATTERN = r"\$\$.*?\$\$"
    
    # Quartoの表キャプションパターン
    QUARTO_TABLE_CAPTION_PATTERN = r": (.+) \{#tbl-[^}]+\}"

    def process_content(self, content: str, path: str) -> DocumentContent:
        """
        Quartoコンテンツを処理する。

        Args:
            content: 生のQuartoコンテンツ
            path: ドキュメントのパス

        Returns:
            処理済みのドキュメントコンテンツ
        """
        # フロントマターを取得
        frontmatter, cleaned_content = parse_frontmatter(content)

        # Quarto固有の処理
        enhanced_content = self._enhance_quarto_content(cleaned_content)

        return DocumentContent(content=enhanced_content, encoding="utf-8")

    def extract_metadata(self, content: str, path: str) -> ExtendedDocumentMetadata:
        """
        Quartoからメタデータを抽出する。

        Args:
            content: 生のQuartoコンテンツ
            path: ドキュメントのパス

        Returns:
            抽出されたメタデータ
        """
        # フロントマターを取得
        frontmatter_dict, _ = parse_frontmatter(content)

        # ファイル名と拡張子を取得
        filename = os.path.basename(path)
        extension = os.path.splitext(filename)[1].lstrip(".")

        # タイトルを取得（フロントマターまたは最初の見出し）
        title = frontmatter_dict.get("title", self._extract_title_from_content(content))

        # 日付を文字列として扱う
        date_value = frontmatter_dict.get("date", "")
        if date_value and not isinstance(date_value, str):
            date_value = str(date_value)

        # Quarto固有のメタデータを抽出
        quarto_metadata = self._extract_quarto_metadata(frontmatter_dict, content)

        return ExtendedDocumentMetadata(
            filename=filename,
            extension=extension,
            title=title,
            description=frontmatter_dict.get("description", ""),
            author=frontmatter_dict.get("author", ""),
            date=date_value,
            tags=frontmatter_dict.get("tags", []),
            frontmatter=frontmatter_dict,
            extra=quarto_metadata,
        )

    def extract_links(self, content: str, path: str) -> List[LinkInfo]:
        """
        Quartoからリンク情報を抽出する（Quarto固有の参照も含む）。

        Args:
            content: 生のQuartoコンテンツ
            path: ドキュメントのパス

        Returns:
            抽出されたリンク情報のリスト
        """
        links = []

        # コンテンツを行ごとに処理
        for line_num, line in enumerate(content.splitlines()):
            # Quarto図表キャプション付きイメージを抽出
            for match in re.finditer(self.QUARTO_FIG_PATTERN, line):
                alt_text, url = match.groups()[:2]
                links.append(
                    LinkInfo(
                        text=f"Figure: {alt_text}" if alt_text else "Figure",
                        url=url,
                        is_image=True,
                        position=match.span(),
                        is_external=LinkTransformer.is_external_link(url),
                    )
                )

            # 通常の画像リンクを抽出（Quarto図表でないもの）
            for match in re.finditer(self.IMG_LINK_PATTERN, line):
                # Quarto図表パターンと重複しないかチェック
                if not self._is_quarto_figure(line, match.span()):
                    alt_text, url = match.groups()
                    links.append(
                        LinkInfo(
                            text=alt_text,
                            url=url,
                            is_image=True,
                            position=match.span(),
                            is_external=LinkTransformer.is_external_link(url),
                        )
                    )

            # 通常のリンクを抽出（画像でないもの）
            for match in re.finditer(self.MD_LINK_PATTERN, line):
                # 画像リンクとして既に抽出されたものはスキップ
                if not line[: match.start()].strip().endswith("!"):
                    text, url = match.groups()
                    links.append(
                        LinkInfo(
                            text=text,
                            url=url,
                            is_image=False,
                            position=match.span(),
                            is_external=LinkTransformer.is_external_link(url),
                        )
                    )

        return links

    def transform_links(
        self, 
        content: str, 
        path: str, 
        base_url: str, 
        service: Optional[str] = None,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        ref: Optional[str] = None
    ) -> str:
        """
        Quarto内のリンクを変換する（画像・静的リソースのみ）。

        Args:
            content: 生のQuartoコンテンツ
            path: ドキュメントのパス
            base_url: 変換に使用する基本URL
            service: Gitサービス名
            owner: リポジトリオーナー
            repo: リポジトリ名
            ref: ブランチ/タグ名

        Returns:
            画像・静的リソースのみCDN変換済みのコンテンツ
        """
        return LinkTransformer.transform_links(content, path, base_url, service, owner, repo, ref)

    def _enhance_quarto_content(self, content: str) -> str:
        """
        Quartoコンテンツを拡張処理する。

        Args:
            content: クリーンアップされたQuartoコンテンツ

        Returns:
            拡張処理されたコンテンツ
        """
        enhanced = content

        # 図表キャプションの改善
        enhanced = self._enhance_figure_captions(enhanced)
        
        # コードブロックの改善
        enhanced = self._enhance_code_blocks(enhanced)
        
        # Calloutの改善
        enhanced = self._enhance_callouts(enhanced)
        
        # 表キャプションの改善
        enhanced = self._enhance_table_captions(enhanced)

        return enhanced

    def _enhance_figure_captions(self, content: str) -> str:
        """
        図表キャプションを改善する。

        Args:
            content: Quartoコンテンツ

        Returns:
            図表キャプション改善済みコンテンツ
        """
        def replace_figure(match):
            alt_text = match.group(1)
            url = match.group(2)
            # Quartoの図表IDを抽出
            fig_id_match = re.search(r"#fig-([^}]+)", match.group(0))
            fig_id = fig_id_match.group(1) if fig_id_match else "unknown"
            
            if alt_text:
                return f"![Figure {fig_id}: {alt_text}]({url})"
            else:
                return f"![Figure {fig_id}]({url})"

        return re.sub(self.QUARTO_FIG_PATTERN, replace_figure, content, flags=re.DOTALL)

    def _enhance_code_blocks(self, content: str) -> str:
        """
        コードブロックを改善する。

        Args:
            content: Quartoコンテンツ

        Returns:
            コードブロック改善済みコンテンツ
        """
        def replace_code_block(match):
            block_options = match.group(1)
            block_content = match.group(2)
            
            # 言語を抽出
            lang_match = re.search(r"(\w+)", block_options)
            language = lang_match.group(1) if lang_match else "text"
            
            # ラベルを抽出（#| label: または #| fig-cap: の後の部分から）
            label_match = re.search(r"#\| label:\s*([^\n]+)", block_content)
            if not label_match:
                # block_optionsから直接ラベルを抽出
                label_match = re.search(r"label:\s*([^,}\s]+)", block_options)
            
            label = label_match.group(1).strip() if label_match else None
            
            header = f"```{language}"
            if label:
                header += f" ({label})"
                
            return f"{header}\n{block_content}\n```"

        return re.sub(self.QUARTO_CODE_BLOCK_PATTERN, replace_code_block, content, flags=re.DOTALL)

    def _enhance_callouts(self, content: str) -> str:
        """
        Quartoのcalloutを改善する。

        Args:
            content: Quartoコンテンツ

        Returns:
            callout改善済みコンテンツ
        """
        def replace_callout(match):
            callout_type = match.group(1)
            callout_content = match.group(2).strip()
            
            type_map = {
                "note": "📝 Note",
                "tip": "💡 Tip", 
                "warning": "⚠️ Warning",
                "caution": "⚠️ Caution",
                "important": "❗ Important"
            }
            
            header = type_map.get(callout_type, f"📋 {callout_type.title()}")
            
            return f"\n> **{header}**\n> \n> {callout_content.replace(chr(10), chr(10) + '> ')}\n"

        return re.sub(self.QUARTO_CALLOUT_PATTERN, replace_callout, content, flags=re.DOTALL)

    def _enhance_table_captions(self, content: str) -> str:
        """
        表キャプションを改善する。

        Args:
            content: Quartoコンテンツ

        Returns:
            表キャプション改善済みコンテンツ
        """
        def replace_table_caption(match):
            caption = match.group(1)
            table_id_match = re.search(r"#tbl-([^}]+)", match.group(0))
            table_id = table_id_match.group(1) if table_id_match else "unknown"
            
            return f": **Table {table_id}**: {caption}"

        return re.sub(self.QUARTO_TABLE_CAPTION_PATTERN, replace_table_caption, content)

    def _extract_quarto_metadata(self, frontmatter: Dict[str, Any], content: str) -> Dict[str, Any]:
        """
        Quarto固有のメタデータを抽出する。

        Args:
            frontmatter: フロントマターの辞書
            content: ドキュメントコンテンツ

        Returns:
            Quarto固有のメタデータ
        """
        quarto_meta = {}

        # Quarto固有のフロントマター項目
        if "format" in frontmatter:
            quarto_meta["format"] = frontmatter["format"]
        
        if "execute" in frontmatter:
            quarto_meta["execute"] = frontmatter["execute"]
            
        if "bibliography" in frontmatter:
            quarto_meta["bibliography"] = frontmatter["bibliography"]
            
        if "citation" in frontmatter:
            quarto_meta["citation"] = frontmatter["citation"]

        # コンテンツから統計情報を抽出
        stats = self._analyze_quarto_content(content)
        quarto_meta.update(stats)

        return {"quarto": quarto_meta}

    def _analyze_quarto_content(self, content: str) -> Dict[str, Any]:
        """
        Quartoコンテンツの統計情報を分析する。

        Args:
            content: Quartoコンテンツ

        Returns:
            統計情報の辞書
        """
        stats = {}

        # 図表の数をカウント
        fig_count = len(re.findall(self.QUARTO_FIG_PATTERN, content))
        stats["figure_count"] = fig_count

        # コードブロックの数をカウント
        code_block_count = len(re.findall(self.QUARTO_CODE_BLOCK_PATTERN, content, re.DOTALL))
        stats["code_block_count"] = code_block_count

        # calloutの数をカウント
        callout_count = len(re.findall(self.QUARTO_CALLOUT_PATTERN, content, re.DOTALL))
        stats["callout_count"] = callout_count

        # 数式の数をカウント
        math_count = len(re.findall(self.QUARTO_MATH_PATTERN, content, re.DOTALL))
        stats["math_count"] = math_count

        # 表キャプションの数をカウント
        table_count = len(re.findall(self.QUARTO_TABLE_CAPTION_PATTERN, content))
        stats["table_count"] = table_count

        return stats

    def _is_quarto_figure(self, line: str, span: Tuple[int, int]) -> bool:
        """
        指定された位置がQuarto図表パターンの一部かどうかを判定する。

        Args:
            line: テキスト行
            span: チェックする位置の範囲

        Returns:
            Quarto図表の一部である場合True
        """
        # Quarto図表パターンが同じ位置にあるかチェック
        for match in re.finditer(self.QUARTO_FIG_PATTERN, line):
            if span[0] >= match.span()[0] and span[1] <= match.span()[1]:
                return True
        return False

    def _extract_title_from_content(self, content: str) -> str:
        """
        コンテンツから最初の見出しを抽出してタイトルとして返す。

        Args:
            content: Quartoコンテンツ

        Returns:
            抽出されたタイトル
        """
        # フロントマターを除去
        _, cleaned_content = parse_frontmatter(content)

        # 最初の見出しを検索
        heading_match = re.search(r"^#\s+(.+)$", cleaned_content, re.MULTILINE)
        if heading_match:
            return heading_match.group(1).strip()

        # 見出しが見つからない場合は空文字を返す
        return ""