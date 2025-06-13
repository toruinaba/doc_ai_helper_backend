"""
リンク情報モデル。

ドキュメント内のリンクに関する情報を格納するためのモデル。
"""

from pydantic import BaseModel, Field
from typing import Tuple, List, Optional


class LinkInfo(BaseModel):
    """ドキュメント内のリンク情報モデル。"""

    text: str = Field(..., description="リンクテキスト")
    url: str = Field(..., description="リンクURL")
    is_image: bool = Field(False, description="画像リンクかどうか")
    position: Tuple[int, int] = Field(..., description="リンクの位置（開始,終了）")
    is_external: bool = Field(False, description="外部リンクかどうか")
