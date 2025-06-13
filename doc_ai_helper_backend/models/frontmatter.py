"""
フロントマター関連のモデル定義。

Markdownファイルのフロントマター情報を格納するためのモデル。
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class FrontMatterBase(BaseModel):
    """フロントマターの基本モデル。"""

    title: Optional[str] = Field(None, description="ドキュメントのタイトル")
    description: Optional[str] = Field(None, description="ドキュメントの説明")
    author: Optional[str] = Field(None, description="著者")
    date: Optional[str] = Field(None, description="日付")
    tags: Optional[List[str]] = Field(default=[], description="タグ")
    extra: Dict[str, Any] = Field(
        default_factory=dict, description="その他のフロントマターデータ"
    )


class ExtendedDocumentMetadata(BaseModel):
    """拡張ドキュメントメタデータモデル。

    既存のDocumentMetadataモデルに加えて、フロントマターから抽出された情報を含む。
    """

    filename: str = Field(..., description="ファイル名")
    extension: str = Field(..., description="ファイル拡張子")
    title: Optional[str] = Field(None, description="ドキュメントタイトル")
    description: Optional[str] = Field(None, description="ドキュメント説明")
    author: Optional[str] = Field(None, description="著者")
    date: Optional[str] = Field(None, description="日付")
    tags: List[str] = Field(default_factory=list, description="タグ")
    frontmatter: Dict[str, Any] = Field(
        default_factory=dict, description="フロントマター全体"
    )
