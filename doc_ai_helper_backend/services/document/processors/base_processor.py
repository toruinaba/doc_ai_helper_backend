"""
ドキュメントプロセッサーの基底クラスを定義するモジュール。
さまざまなドキュメントタイプに対応するプロセッサーの共通インターフェースを提供する。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple

# 将来的に定義される可能性のあるクラスをインポート
# 現時点ではまだモデルが定義されていない可能性があるため、型ヒントだけを使用
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from doc_ai_helper_backend.models.document import DocumentContent, DocumentMetadata, LinkInfo


class DocumentProcessorBase(ABC):
    """
    ドキュメントプロセッサーの基底クラス。
    
    このクラスは、さまざまなドキュメントタイプを処理するためのインターフェースを定義します。
    Markdown, Quarto, HTML など、各ドキュメントタイプごとに具体的な実装が提供されます。
    """

    @abstractmethod
    def process_content(self, content: str, path: str) -> "DocumentContent":
        """
        ドキュメントコンテンツを処理する。
        
        Args:
            content: 生のドキュメントコンテンツ
            path: ドキュメントのパス
            
        Returns:
            処理済みのドキュメントコンテンツ
        """
        pass
    
    @abstractmethod
    def extract_metadata(self, content: str, path: str) -> "DocumentMetadata":
        """
        ドキュメントからメタデータを抽出する。
        
        Args:
            content: 生のドキュメントコンテンツ
            path: ドキュメントのパス
            
        Returns:
            抽出されたメタデータ
        """
        pass
    
    @abstractmethod
    def extract_links(self, content: str, path: str) -> List["LinkInfo"]:
        """
        ドキュメントからリンク情報を抽出する。
        
        Args:
            content: 生のドキュメントコンテンツ
            path: ドキュメントのパス
            
        Returns:
            抽出されたリンク情報のリスト
        """
        pass
    
    @abstractmethod
    def transform_links(self, content: str, path: str, base_url: str) -> str:
        """
        ドキュメント内のリンクを変換する。
        
        Args:
            content: 生のドキュメントコンテンツ
            path: ドキュメントのパス
            base_url: 変換に使用する基本URL
            
        Returns:
            リンク変換済みのコンテンツ
        """
        pass
    
    def determine_document_type(self, filename: str) -> str:
        """
        ファイル名からドキュメントタイプを判定する。
        
        Args:
            filename: ファイル名
            
        Returns:
            ドキュメントタイプの文字列
        """
        extension = filename.split('.')[-1].lower() if '.' in filename else ''
        
        if extension in ['md', 'markdown']:
            return "markdown"
        elif extension in ['qmd']:
            return "quarto"
        elif extension in ['html', 'htm']:
            return "html"
        else:
            return "other"
