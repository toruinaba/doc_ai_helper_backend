"""
Markdownドキュメント内のリンクを変換するユーティリティモジュール。
"""

import os
import re
from typing import Match, Optional
from urllib.parse import urljoin, urlparse


class LinkTransformer:
    """Markdownドキュメント内のリンクを変換するユーティリティクラス。"""

    # Markdownリンクパターン [text](url)
    MD_LINK_PATTERN = r"\[([^\]]+)\]\(([^)]+)\)"

    # イメージパターン ![alt](url)
    IMG_LINK_PATTERN = r"!\[([^\]]*)\]\(([^)]+)\)"
    
    # HTMLアンカータグパターン <a href="url">text</a>
    HTML_ANCHOR_PATTERN = r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
    
    # HTMLイメージタグパターン <img src="url" alt="alt">
    HTML_IMG_PATTERN = r'<img\s+[^>]*src=["\']([^"\']+)["\'][^>]*>'
    
    # HTMLリンクタグパターン <link href="url">
    HTML_LINK_PATTERN = r'<link\s+[^>]*href=["\']([^"\']+)["\'][^>]*>'

    # 画像ファイル拡張子
    IMAGE_EXTENSIONS = {
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", 
        ".ico", ".tiff", ".tif", ".avif", ".apng"
    }

    @staticmethod
    def is_external_link(url: str) -> bool:
        """
        URLが外部リンクかどうかを判定する。

        Args:
            url: チェックするURL

        Returns:
            外部リンクの場合True
        """
        return bool(urlparse(url).netloc)

    @staticmethod
    def is_image_link(url: str) -> bool:
        """
        URLが画像ファイルかどうかを判定する。

        Args:
            url: チェックするURL

        Returns:
            画像ファイルの場合True
        """
        if not url:
            return False
        
        # URLの最後のパスセグメントから拡張子を取得
        path = urlparse(url).path.lower()
        return any(path.endswith(ext) for ext in LinkTransformer.IMAGE_EXTENSIONS)

    @staticmethod
    def resolve_relative_path(base_dir: str, rel_path: str) -> str:
        """
        相対パスを解決する。

        Args:
            base_dir: 基準ディレクトリ
            rel_path: 相対パス

        Returns:
            解決された絶対パス
        """
        # 絶対パスの場合はそのまま返す
        if rel_path.startswith("/"):
            return rel_path

        # 相対パスを結合
        abs_path = os.path.normpath(os.path.join(base_dir, rel_path))

        # パス区切り文字をスラッシュに統一
        abs_path = abs_path.replace("\\", "/")

        # 先頭のスラッシュを付与
        if not abs_path.startswith("/"):
            abs_path = "/" + abs_path

        return abs_path

    @classmethod
    def _get_document_base_directory(
        cls,
        path: str,
        repository_root: Optional[str] = None,
        document_root_directory: Optional[str] = None,
        root_path: Optional[str] = None
    ) -> str:
        """
        ドキュメントのベースディレクトリを取得する（新旧両方式対応）。
        
        新しいセマンティクス:
        - repository_root: リポジトリのベースディレクトリ (デフォルト: "/")
        - document_root_directory: リポジトリルートからドキュメントルートディレクトリへの絶対パス (デフォルト: "/")
        
        Args:
            path: ドキュメントのパス
            repository_root: リポジトリベースディレクトリ（新方式）
            document_root_directory: ドキュメントルートディレクトリの絶対パス（新方式）
            root_path: ドキュメントルートディレクトリ（旧方式）
            
        Returns:
            ベースディレクトリパス
        """
        # 新方式優先
        if repository_root is not None and document_root_directory is not None:
            # repository_root と document_root_directory を結合
            repo_root = repository_root.rstrip('/') if repository_root != '/' else ''
            doc_root = document_root_directory.rstrip('/') if document_root_directory != '/' else ''
            
            # document_root_directory が絶対パスの場合
            if doc_root.startswith('/'):
                if doc_root == '':  # document_root_directory が "/" の場合
                    return repo_root if repo_root else '/'
                else:
                    return f"{repo_root}{doc_root}" if repo_root else doc_root
            else:
                # 相対パスの場合（後方互換性のため）
                return f"{repo_root}/{doc_root}" if repo_root else f"/{doc_root}"
        
        # repository_rootのみ指定の場合
        if repository_root is not None:
            return repository_root.rstrip('/') if repository_root != '/' else '/'
        
        # 旧方式フォールバック
        if root_path is not None and root_path.strip():
            return root_path.rstrip('/')
        
        # デフォルト: ファイルのディレクトリ
        return os.path.dirname(path)

    @classmethod
    def transform_links(
        cls, 
        content: str, 
        path: str, 
        base_url: str, 
        service: Optional[str] = None,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        ref: Optional[str] = None,
        root_path: Optional[str] = None,
        repository_root: Optional[str] = None,
        document_root_directory: Optional[str] = None
    ) -> str:
        """
        Markdown内のリンクを変換する（画像・静的リソースのみ）。

        Args:
            content: 生のMarkdownコンテンツ
            path: ドキュメントのパス
            base_url: 変換に使用する基本URL
            service: Gitサービス名 (github, forgejo等)
            owner: リポジトリオーナー
            repo: リポジトリ名
            ref: ブランチ/タグ名
            root_path: DEPRECATED: ドキュメントルートディレクトリ（リンク解決の基準）
            repository_root: リポジトリベースディレクトリ
            document_root_directory: ドキュメントルートディレクトリ

        Returns:
            画像・静的リソースのみCDN変換済みのコンテンツ
        """
        transformed_content = content

        # ドキュメントのベースディレクトリを取得（デュアル対応）
        base_dir = cls._get_document_base_directory(
            path=path,
            repository_root=repository_root,
            document_root_directory=document_root_directory,
            root_path=root_path
        )

        # 画像リンクのみを変換（通常のドキュメントリンクは変換しない）
        transformed_content = re.sub(
            cls.IMG_LINK_PATTERN,
            lambda m: cls._transform_image_match(m, base_dir, base_url, service, owner, repo, ref),
            transformed_content,
        )

        # HTMLイメージタグを変換
        transformed_content = re.sub(
            cls.HTML_IMG_PATTERN,
            lambda m: cls._transform_html_img_match(m, base_dir, base_url, service, owner, repo, ref),
            transformed_content,
        )

        # HTMLアンカータグ内の画像リンクのみを変換
        transformed_content = re.sub(
            cls.HTML_ANCHOR_PATTERN,
            lambda m: cls._transform_html_anchor_match_images_only(m, base_dir, base_url, service, owner, repo, ref),
            transformed_content,
            flags=re.DOTALL,
        )

        # HTMLリンクタグ（CSS・JS等静的リソース）を変換
        transformed_content = re.sub(
            cls.HTML_LINK_PATTERN,
            lambda m: cls._transform_html_link_match(m, base_dir, base_url, service, owner, repo, ref),
            transformed_content,
        )

        return transformed_content

    @classmethod
    def _transform_link_match(
        cls, 
        match: Match, 
        base_dir: str, 
        base_url: str,
        service: Optional[str] = None,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        ref: Optional[str] = None
    ) -> str:
        """
        リンクマッチを変換する。

        Args:
            match: 正規表現マッチオブジェクト
            base_dir: 基準ディレクトリ
            base_url: 変換に使用する基本URL
            service: Gitサービス名
            owner: リポジトリオーナー
            repo: リポジトリ名
            ref: ブランチ/タグ名

        Returns:
            変換されたリンク文字列
        """
        text, url = match.groups()

        # 外部リンクはそのまま
        if cls.is_external_link(url):
            return f"[{text}]({url})"

        # アンカーリンクはそのまま
        if url.startswith("#"):
            return f"[{text}]({url})"

        # 相対パスを絶対パスに変換
        abs_path = cls.resolve_relative_path(base_dir, url)

        # 画像リンクの場合は外部Raw URLに変換
        if cls.is_image_link(url) and service and owner and repo and ref:
            raw_url = cls._build_raw_url(service, owner, repo, ref, abs_path)
            if raw_url:
                return f"[{text}]({raw_url})"

        # 通常のドキュメントリンクはAPI経由
        # base_urlの末尾にスラッシュがなければ追加
        if not base_url.endswith("/"):
            base_url = base_url + "/"

        transformed_url = base_url + abs_path.lstrip("/")
        
        # refをクエリパラメータとして追加
        if ref:
            transformed_url += f"?ref={ref}"

        return f"[{text}]({transformed_url})"

    @classmethod
    def _transform_image_match(
        cls, 
        match: Match, 
        base_dir: str, 
        base_url: str,
        service: Optional[str] = None,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        ref: Optional[str] = None
    ) -> str:
        """
        画像マッチを変換する。

        Args:
            match: 正規表現マッチオブジェクト
            base_dir: 基準ディレクトリ
            base_url: 変換に使用する基本URL
            service: Gitサービス名
            owner: リポジトリオーナー
            repo: リポジトリ名
            ref: ブランチ/タグ名

        Returns:
            変換された画像リンク文字列
        """
        alt_text, url = match.groups()

        # 外部リンクはそのまま
        if cls.is_external_link(url):
            return f"![{alt_text}]({url})"

        # 相対パスを絶対パスに変換
        abs_path = cls.resolve_relative_path(base_dir, url)

        # 画像は外部Raw URLに変換
        if service and owner and repo and ref:
            raw_url = cls._build_raw_url(service, owner, repo, ref, abs_path)
            if raw_url:
                return f"![{alt_text}]({raw_url})"

        # フォールバック: API経由
        # base_urlの末尾にスラッシュがなければ追加
        if not base_url.endswith("/"):
            base_url = base_url + "/"

        transformed_url = base_url + abs_path.lstrip("/")
        
        # refをクエリパラメータとして追加
        if ref:
            transformed_url += f"?ref={ref}"

        return f"![{alt_text}]({transformed_url})"

    @classmethod
    def _transform_html_anchor_match(
        cls, 
        match: Match, 
        base_dir: str, 
        base_url: str,
        service: Optional[str] = None,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        ref: Optional[str] = None
    ) -> str:
        """
        HTMLアンカータグマッチを変換する。

        Args:
            match: 正規表現マッチオブジェクト
            base_dir: 基準ディレクトリ
            base_url: 変換に使用する基本URL
            service: Gitサービス名
            owner: リポジトリオーナー
            repo: リポジトリ名
            ref: ブランチ/タグ名

        Returns:
            変換されたHTMLアンカータグ文字列
        """
        url, text = match.groups()
        original_tag = match.group(0)

        # 外部リンクはそのまま
        if cls.is_external_link(url):
            return original_tag

        # アンカーリンクはそのまま
        if url.startswith("#"):
            return original_tag

        # 相対パスを絶対パスに変換
        abs_path = cls.resolve_relative_path(base_dir, url)

        # 画像リンクの場合は外部Raw URLに変換
        if cls.is_image_link(url) and service and owner and repo and ref:
            raw_url = cls._build_raw_url(service, owner, repo, ref, abs_path)
            if raw_url:
                return original_tag.replace(url, raw_url)

        # 通常のドキュメントリンクはAPI経由
        if not base_url.endswith("/"):
            base_url = base_url + "/"

        transformed_url = base_url + abs_path.lstrip("/")
        
        # refをクエリパラメータとして追加
        if ref:
            transformed_url += f"?ref={ref}"

        return original_tag.replace(url, transformed_url)

    @classmethod
    def _transform_html_img_match(
        cls, 
        match: Match, 
        base_dir: str, 
        base_url: str,
        service: Optional[str] = None,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        ref: Optional[str] = None
    ) -> str:
        """
        HTMLイメージタグマッチを変換する。

        Args:
            match: 正規表現マッチオブジェクト
            base_dir: 基準ディレクトリ
            base_url: 変換に使用する基本URL
            service: Gitサービス名
            owner: リポジトリオーナー
            repo: リポジトリ名
            ref: ブランチ/タグ名

        Returns:
            変換されたHTMLイメージタグ文字列
        """
        url = match.group(1)
        original_tag = match.group(0)

        # 外部リンクはそのまま
        if cls.is_external_link(url):
            return original_tag

        # 相対パスを絶対パスに変換
        abs_path = cls.resolve_relative_path(base_dir, url)

        # 画像は外部Raw URLに変換
        if service and owner and repo and ref:
            raw_url = cls._build_raw_url(service, owner, repo, ref, abs_path)
            if raw_url:
                return original_tag.replace(url, raw_url)

        # フォールバック: API経由
        if not base_url.endswith("/"):
            base_url = base_url + "/"

        transformed_url = base_url + abs_path.lstrip("/")
        
        # refをクエリパラメータとして追加
        if ref:
            transformed_url += f"?ref={ref}"

        return original_tag.replace(url, transformed_url)

    @classmethod
    def _transform_html_link_match(
        cls, 
        match: Match, 
        base_dir: str, 
        base_url: str,
        service: Optional[str] = None,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        ref: Optional[str] = None
    ) -> str:
        """
        HTMLリンクタグマッチを変換する。

        Args:
            match: 正規表現マッチオブジェクト
            base_dir: 基準ディレクトリ
            base_url: 変換に使用する基本URL
            service: Gitサービス名
            owner: リポジトリオーナー
            repo: リポジトリ名
            ref: ブランチ/タグ名

        Returns:
            変換されたHTMLリンクタグ文字列
        """
        url = match.group(1)
        original_tag = match.group(0)

        # 外部リンクはそのまま
        if cls.is_external_link(url):
            return original_tag

        # 相対パスを絶対パスに変換
        abs_path = cls.resolve_relative_path(base_dir, url)

        # 通常のリソースリンクはAPI経由
        if not base_url.endswith("/"):
            base_url = base_url + "/"

        transformed_url = base_url + abs_path.lstrip("/")
        
        # refをクエリパラメータとして追加
        if ref:
            transformed_url += f"?ref={ref}"

        return original_tag.replace(url, transformed_url)

    @classmethod
    def _transform_html_anchor_match_images_only(
        cls, 
        match: Match, 
        base_dir: str, 
        base_url: str,
        service: Optional[str] = None,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        ref: Optional[str] = None
    ) -> str:
        """
        HTMLアンカータグマッチを変換する（画像リンクのみ）。

        Args:
            match: 正規表現マッチオブジェクト
            base_dir: 基準ディレクトリ
            base_url: 変換に使用する基本URL
            service: Gitサービス名
            owner: リポジトリオーナー
            repo: リポジトリ名
            ref: ブランチ/タグ名

        Returns:
            変換されたHTMLアンカータグ文字列（画像リンクのみ変換）
        """
        url, text = match.groups()
        original_tag = match.group(0)

        # 外部リンクはそのまま
        if cls.is_external_link(url):
            return original_tag

        # アンカーリンクはそのまま
        if url.startswith("#"):
            return original_tag

        # 画像リンクでない場合はそのまま（一般ドキュメントリンクは変換しない）
        if not cls.is_image_link(url):
            return original_tag

        # 相対パスを絶対パスに変換
        abs_path = cls.resolve_relative_path(base_dir, url)

        # 画像リンクの場合は外部Raw URLに変換
        if service and owner and repo and ref:
            raw_url = cls._build_raw_url(service, owner, repo, ref, abs_path)
            if raw_url:
                return original_tag.replace(url, raw_url)

        # 変換できない場合はそのまま
        return original_tag

    @staticmethod
    def _build_raw_url(service: str, owner: str, repo: str, ref: str, path: str, service_base_url: Optional[str] = None) -> Optional[str]:
        """
        外部Raw URLを構築する。

        Args:
            service: Gitサービス名
            owner: リポジトリオーナー
            repo: リポジトリ名
            ref: ブランチ/タグ名
            path: ファイルパス
            service_base_url: サービスのベースURL（Forgejo等で必要）

        Returns:
            構築されたRaw URL（失敗時はNone）
        """
        # パスの先頭スラッシュを削除
        clean_path = path.lstrip("/")
        
        if service.lower() == "github":
            return f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{clean_path}"
        elif service.lower() == "forgejo":
            if service_base_url:
                # Forgejo/Giteaのraw URLパターン: {base_url}/{owner}/{repo}/raw/{ref}/{path}
                base_url = service_base_url.rstrip("/")
                return f"{base_url}/{owner}/{repo}/raw/{ref}/{clean_path}"
            else:
                # ベースURLが不明な場合は設定から取得を試みる
                from doc_ai_helper_backend.core.config import settings
                if settings.forgejo_base_url:
                    base_url = settings.forgejo_base_url.rstrip("/")
                    return f"{base_url}/{owner}/{repo}/raw/{ref}/{clean_path}"
                return None
        else:
            # その他のサービスは未対応
            return None
