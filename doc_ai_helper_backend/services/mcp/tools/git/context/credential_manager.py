"""
統一認証情報管理。

このモジュールは、リポジトリコンテキストに基づいて
適切な認証情報を自動的に取得する機能を提供します。
"""

import os
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from .repository_context import RepositoryContext, AuthenticationError, GitServiceType

logger = logging.getLogger(__name__)


class CredentialManager:
    """統一認証情報管理クラス"""
    
    @classmethod
    def get_credentials(cls, context: RepositoryContext) -> Dict[str, Any]:
        """
        コンテキストに基づいて認証情報を取得
        
        Args:
            context: リポジトリコンテキスト
            
        Returns:
            認証情報の辞書
            
        Raises:
            AuthenticationError: 認証情報が見つからない場合
        """
        logger.info(f"認証情報を取得中: {context.service_identifier}")
        
        if context.service_type == GitServiceType.GITHUB:
            return cls._get_github_credentials()
        elif context.service_type == GitServiceType.FORGEJO:
            return cls._get_forgejo_credentials(context.base_url)
        else:
            raise AuthenticationError(f"サポートされていないサービス: {context.service_type.value}")
    
    @classmethod
    def _get_github_credentials(cls) -> Dict[str, Any]:
        """
        GitHub認証情報を取得
        
        Returns:
            GitHub認証情報
            
        Raises:
            AuthenticationError: トークンが見つからない場合
        """
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise AuthenticationError(
                "GITHUB_TOKEN環境変数が設定されていません。"
                "GitHubの個人アクセストークンを設定してください。"
            )
        
        logger.debug("GitHub認証情報を取得しました")
        return {
            "access_token": token,
            "service_type": "github"
        }
    
    @classmethod 
    def _get_forgejo_credentials(cls, base_url: str) -> Dict[str, Any]:
        """
        Forgejo認証情報を取得（URL固有対応）
        
        Args:
            base_url: ForgejoインスタンスのベースURL
            
        Returns:
            Forgejo認証情報
            
        Raises:
            AuthenticationError: 認証情報が見つからない場合
        """
        if not base_url:
            raise AuthenticationError("ForgejoのベースURLが指定されていません")
        
        domain = urlparse(base_url).netloc.replace('.', '_').replace('-', '_').upper()
        
        # 1. URL固有トークンを優先
        token = os.getenv(f"FORGEJO_TOKEN_{domain}")
        if token:
            logger.debug(f"Forgejo URL固有認証情報を取得: {domain}")
            return {
                "access_token": token,
                "base_url": base_url,
                "service_type": "forgejo"
            }
        
        # 2. デフォルトトークン
        token = os.getenv("FORGEJO_TOKEN")
        if token:
            logger.debug("Forgejoデフォルト認証情報を取得")
            return {
                "access_token": token,
                "base_url": base_url,
                "service_type": "forgejo"
            }
        
        # 3. URL固有ユーザー名/パスワード認証
        username = os.getenv(f"FORGEJO_USERNAME_{domain}")
        password = os.getenv(f"FORGEJO_PASSWORD_{domain}")
        if username and password:
            logger.debug(f"Forgejo URL固有ユーザー認証情報を取得: {domain}")
            return {
                "username": username,
                "password": password,
                "base_url": base_url,
                "service_type": "forgejo"
            }
        
        # 4. デフォルトユーザー名/パスワード認証
        username = os.getenv("FORGEJO_USERNAME")
        password = os.getenv("FORGEJO_PASSWORD")
        if username and password:
            logger.debug("Forgejoデフォルトユーザー認証情報を取得")
            return {
                "username": username,
                "password": password,
                "base_url": base_url,
                "service_type": "forgejo"
            }
        
        # 認証情報が見つからない
        raise AuthenticationError(
            f"Forgejo認証情報が見つかりません: {base_url}\n"
            f"以下の環境変数のいずれかを設定してください:\n"
            f"- FORGEJO_TOKEN_{domain}\n"
            f"- FORGEJO_TOKEN\n"
            f"- FORGEJO_USERNAME_{domain} + FORGEJO_PASSWORD_{domain}\n"
            f"- FORGEJO_USERNAME + FORGEJO_PASSWORD"
        )
    
    @classmethod
    def has_credentials(cls, context: RepositoryContext) -> bool:
        """
        認証情報が利用可能かチェック
        
        Args:
            context: リポジトリコンテキスト
            
        Returns:
            認証情報が利用可能な場合True
        """
        try:
            cls.get_credentials(context)
            return True
        except AuthenticationError:
            return False
    
    @classmethod
    def get_supported_services(cls) -> Dict[str, Dict[str, Any]]:
        """
        サポートされているサービスと必要な環境変数の情報を取得
        
        Returns:
            サービス情報の辞書
        """
        return {
            "github": {
                "name": "GitHub",
                "description": "GitHub.comまたはGitHub Enterprise",
                "required_env_vars": ["GITHUB_TOKEN"],
                "optional_env_vars": [],
                "example_env_vars": {
                    "GITHUB_TOKEN": "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                }
            },
            "forgejo": {
                "name": "Forgejo",
                "description": "セルフホスト型Gitサービス",
                "required_env_vars": ["FORGEJO_TOKEN または FORGEJO_USERNAME + FORGEJO_PASSWORD"],
                "optional_env_vars": ["FORGEJO_TOKEN_<DOMAIN>", "FORGEJO_USERNAME_<DOMAIN>", "FORGEJO_PASSWORD_<DOMAIN>"],
                "example_env_vars": {
                    "FORGEJO_TOKEN": "forgejo_token_here",
                    "FORGEJO_TOKEN_GIT_COMPANY_COM": "company_specific_token",
                    "FORGEJO_USERNAME": "username",
                    "FORGEJO_PASSWORD": "password"
                }
            }
        }
    
    @classmethod
    def validate_environment(cls) -> Dict[str, bool]:
        """
        環境変数の設定状況を検証
        
        Returns:
            サービス毎の設定状況
        """
        result = {}
        
        # GitHub
        result["github"] = bool(os.getenv("GITHUB_TOKEN"))
        
        # Forgejo
        forgejo_configured = bool(
            os.getenv("FORGEJO_TOKEN") or 
            (os.getenv("FORGEJO_USERNAME") and os.getenv("FORGEJO_PASSWORD"))
        )
        result["forgejo"] = forgejo_configured
        
        return result
