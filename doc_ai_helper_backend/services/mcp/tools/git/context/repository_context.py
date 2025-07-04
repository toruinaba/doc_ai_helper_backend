"""
強化されたリポジトリコンテキストモデル。

このモジュールは、フロントエンドから提供されるリポジトリ情報を
基にGitサービスを自動決定するためのコンテキストモデルを提供します。
"""

from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from urllib.parse import urlparse


class GitServiceType(str, Enum):
    """Git サービスタイプの列挙型"""

    GITHUB = "github"
    FORGEJO = "forgejo"


class RepositoryContext(BaseModel):
    """強化されたリポジトリコンテキスト"""

    # 基本情報（フロントエンドから提供）
    owner: str = Field(..., description="リポジトリオーナー")
    repo: str = Field(..., description="リポジトリ名")
    service_type: GitServiceType = Field(..., description="Gitサービス種別")
    ref: str = Field(default="main", description="ブランチ/タグ参照")
    path: str = Field(default="", description="ファイルパス")

    # サービス固有情報
    base_url: Optional[str] = Field(
        None, description="ForgejoのベースURL（GitHub以外）"
    )
    api_version: Optional[str] = Field(None, description="API バージョン")

    # メタデータ
    last_updated: Optional[str] = Field(None, description="最終更新時刻")
    permissions: Optional[Dict[str, bool]] = Field(
        None, description="権限情報キャッシュ"
    )

    @property
    def repository_full_name(self) -> str:
        """完全なリポジトリ名（owner/repo形式）"""
        return f"{self.owner}/{self.repo}"

    @property
    def full_name(self) -> str:
        """repository_full_nameのエイリアス"""
        return self.repository_full_name

    def model_post_init(self, __context: Any) -> None:
        """モデル初期化後の処理"""
        # GitHubの場合は base_url を自動設定
        if self.service_type == GitServiceType.GITHUB and not self.base_url:
            object.__setattr__(self, "base_url", "https://github.com")

        # Forgejoの場合は base_url が必須
        if self.service_type == GitServiceType.FORGEJO and not self.base_url:
            raise ValueError("Forgejo service requires base_url to be specified")

    @property
    def service_identifier(self) -> str:
        """サービス識別子（認証情報キー用）"""
        if self.service_type == GitServiceType.GITHUB:
            return "github"
        elif self.service_type == GitServiceType.FORGEJO and self.base_url:
            # URLからドメインを抽出してキーとする
            domain = urlparse(self.base_url).netloc
            return f"forgejo_{domain.replace('.', '_').replace('-', '_')}"
        return self.service_type.value

    @property
    def display_name(self) -> str:
        """表示用のリポジトリ名"""
        if self.service_type == GitServiceType.GITHUB:
            return f"GitHub: {self.repository_full_name}"
        elif self.service_type == GitServiceType.FORGEJO:
            domain = urlparse(self.base_url).netloc if self.base_url else "unknown"
            return f"Forgejo ({domain}): {self.repository_full_name}"
        return f"{self.service_type.value}: {self.repository_full_name}"

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換（API応答用）"""
        return self.dict(exclude_none=True)

    def is_valid_for_operation(self, operation_type: str = "general") -> bool:
        """指定された操作に対してコンテキストが有効かチェック"""
        # 基本的な必須フィールドの確認
        if not self.owner or not self.repo or not self.service_type:
            return False

        # サービス固有の検証
        if self.service_type == GitServiceType.FORGEJO and not self.base_url:
            return False

        # 操作固有の検証（将来拡張）
        if operation_type == "write" and not self.ref:
            return False

        return True


class ContextValidationError(Exception):
    """コンテキスト検証エラー"""

    pass


class UnsupportedServiceError(Exception):
    """サポートされていないサービスエラー"""

    pass


class AuthenticationError(Exception):
    """認証エラー"""

    pass


class InvalidContextError(Exception):
    """無効なコンテキストエラー"""

    pass
