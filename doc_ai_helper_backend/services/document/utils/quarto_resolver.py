"""
Quarto HTML→QMD パス解決ユーティリティ。

QuartoプロジェクトのHTML出力ファイルから対応するソース.qmdファイルのパスを
解決するためのユーティリティ機能を提供します。
"""

import logging
import re
import yaml
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup

from .html_analyzer import HTMLAnalyzer

logger = logging.getLogger("doc_ai_helper")


class QuartoPathResolver:
    """Quarto HTML→QMD パス解決ユーティリティクラス"""

    # Quarto標準出力パターン（Quarto公式仕様ベース）
    QUARTO_OUTPUT_PATTERNS = [
        # 標準パターン (output-dir: "_site")
        (r"^_site/(.+)\.html$", r"\1.qmd"),
        
        # GitHub Pages (output-dir: "docs") 
        (r"^docs/(.+)\.html$", r"\1.qmd"),
        
        # カスタムパターン
        (r"^public/(.+)\.html$", r"src/\1.qmd"),
        (r"^build/(.+)\.html$", r"\1.qmd"),
        (r"^dist/(.+)\.html$", r"\1.qmd"),
        
        # 同一ディレクトリ (シンプルサイト)
        (r"^(.+)\.html$", r"\1.qmd"),
    ]

    @staticmethod
    def extract_source_from_html(html_content: str) -> Optional[str]:
        """
        HTMLコンテンツからソース.qmdファイルのパスを抽出する。
        
        Args:
            html_content: HTMLコンテンツ文字列
            
        Returns:
            ソース.qmdファイルのパス（見つかった場合）
        """
        try:
            soup = HTMLAnalyzer.parse_html_safely(html_content)
            return HTMLAnalyzer.find_source_file_references(soup)
        except Exception as e:
            logger.warning(f"Failed to extract source from HTML: {e}")
            return None

    @staticmethod
    def resolve_from_quarto_config(html_path: str, config_content: str) -> Optional[str]:
        """
        _quarto.yml設定ファイルからHTML→QMDパス変換を解決する。
        
        Args:
            html_path: HTMLファイルのパス
            config_content: _quarto.yml設定ファイルの内容
            
        Returns:
            対応するソース.qmdファイルのパス（見つかった場合）
        """
        try:
            config = yaml.safe_load(config_content)
            if not config:
                return None
            
            # output-dir設定取得 (デフォルト: "_site")
            project_config = config.get("project", {})
            output_dir = project_config.get("output-dir", "_site")
            
            # パス変換: output-dir/path.html → path.qmd
            if html_path.startswith(f"{output_dir}/"):
                relative_path = html_path[len(f"{output_dir}/"):]
                source_path = re.sub(r'\.html$', '.qmd', relative_path)
                return source_path
            
            # output-dirがカスタムの場合の特別処理
            if output_dir != "_site" and html_path.endswith('.html'):
                # パターンマッチングでより柔軟に対応
                for pattern, replacement in QuartoPathResolver.QUARTO_OUTPUT_PATTERNS:
                    # output-dirを含む動的パターンを作成
                    dynamic_pattern = pattern.replace("_site", output_dir)
                    if re.match(dynamic_pattern, html_path):
                        return re.sub(dynamic_pattern, replacement, html_path)
                
        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse _quarto.yml: {e}")
        except Exception as e:
            logger.warning(f"Failed to resolve from Quarto config: {e}")
            
        return None

    @staticmethod
    def apply_standard_patterns(html_path: str) -> Optional[str]:
        """
        標準Quartoパターンを適用してHTML→QMDパス変換を試行する。
        
        Args:
            html_path: HTMLファイルのパス
            
        Returns:
            変換されたソース.qmdファイルのパス（マッチした場合）
        """
        if not html_path.endswith('.html'):
            return None
            
        for pattern, replacement in QuartoPathResolver.QUARTO_OUTPUT_PATTERNS:
            if re.match(pattern, html_path):
                qmd_path = re.sub(pattern, replacement, html_path)
                logger.debug(f"Pattern matched: {html_path} -> {qmd_path}")
                return qmd_path
                
        return None

    @staticmethod
    def is_quarto_html(html_content: str) -> bool:
        """
        HTMLコンテンツがQuartoによって生成されたかを判定する。
        
        Args:
            html_content: HTMLコンテンツ文字列
            
        Returns:
            Quartoによって生成された場合True
        """
        try:
            soup = HTMLAnalyzer.parse_html_safely(html_content)
            
            # Generator メタタグをチェック
            generator = HTMLAnalyzer.detect_generator_tool(soup)
            if generator and "quarto" in generator.lower():
                return True
            
            # Quarto特有の属性やクラスをチェック
            quarto_metadata = HTMLAnalyzer.extract_quarto_metadata(soup)
            if quarto_metadata:
                return True
                
            return False
            
        except Exception as e:
            logger.warning(f"Failed to check if Quarto HTML: {e}")
            return False

    @staticmethod
    def extract_quarto_version(html_content: str) -> Optional[str]:
        """
        HTMLコンテンツからQuartoバージョンを抽出する。
        
        Args:
            html_content: HTMLコンテンツ文字列
            
        Returns:
            Quartoバージョン（見つかった場合）
        """
        try:
            soup = HTMLAnalyzer.parse_html_safely(html_content)
            meta_tags = HTMLAnalyzer.extract_meta_tags(soup)
            
            # generatorメタタグからバージョン抽出
            generator = meta_tags.get("generator", "")
            if "quarto" in generator.lower():
                version_match = re.search(r"quarto[^\d]*(\d+\.\d+\.\d+)", generator, re.IGNORECASE)
                if version_match:
                    return version_match.group(1)
            
            # data-quarto-version属性をチェック
            html_tag = soup.find("html")
            if html_tag and html_tag.get("data-quarto-version"):
                return html_tag.get("data-quarto-version")
                
            return None
            
        except Exception as e:
            logger.warning(f"Failed to extract Quarto version: {e}")
            return None