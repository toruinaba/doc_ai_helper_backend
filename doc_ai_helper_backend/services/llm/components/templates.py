"""
テンプレート管理サービス (Template Management Service)

プロンプトテンプレートの管理とフォーマット機能を提供します。
元ファイル: utils/templating.py

このコンポーネントは純粋な委譲パターンで使用され、mixin継承は使用しません。
"""

import os
import json
from typing import Dict, Any, List, Optional
import re
from pathlib import Path

from doc_ai_helper_backend.models.llm import PromptTemplate, TemplateVariable
from doc_ai_helper_backend.core.exceptions import (
    TemplateNotFoundError,
    TemplateSyntaxError,
)


class PromptTemplateManager:
    """
    プロンプトテンプレートマネージャー

    プロンプトテンプレートの読み込み、保存、フォーマット機能を提供します。
    """

    def __init__(self, templates_dir: Optional[str] = None):
        """
        テンプレートマネージャーの初期化

        Args:
            templates_dir: テンプレートファイルのディレクトリ（デフォルト: '../templates'）
        """
        if templates_dir is None:
            # デフォルトで親ディレクトリの'templates'ディレクトリを使用
            current_dir = os.path.dirname(__file__)
            self.templates_dir = os.path.join(os.path.dirname(current_dir), "templates")
        else:
            self.templates_dir = templates_dir

        # テンプレートディレクトリが存在しない場合は作成
        os.makedirs(self.templates_dir, exist_ok=True)

        # 読み込み済みテンプレートのキャッシュ
        self._templates: Dict[str, PromptTemplate] = {}

        # テンプレートの読み込み
        self._load_templates()

    def _load_templates(self) -> None:
        """
        テンプレートディレクトリからテンプレートを読み込み
        """
        if not os.path.exists(self.templates_dir):
            return

        for file_path in Path(self.templates_dir).glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    template_data = json.load(f)

                # PromptTemplateモデルに変換
                template = PromptTemplate(
                    id=template_data.get("id", file_path.stem),
                    name=template_data.get("name", file_path.stem),
                    description=template_data.get("description", ""),
                    template=template_data.get("template", ""),
                    variables=(
                        [
                            TemplateVariable(**var)
                            for var in template_data.get("variables", [])
                        ]
                        if "variables" in template_data
                        else []
                    ),
                )

                self._templates[template.id] = template

            except Exception as e:
                # エラーをログに出力するが、他のテンプレートの読み込みは継続
                print(f"Error loading template {file_path}: {str(e)}")

    def get_template(self, template_id: str) -> PromptTemplate:
        """
        IDでテンプレートを取得

        Args:
            template_id: テンプレートのID

        Returns:
            PromptTemplate: 要求されたテンプレート

        Raises:
            TemplateNotFoundError: テンプレートが見つからない場合
        """
        if template_id not in self._templates:
            raise TemplateNotFoundError(f"Template '{template_id}' not found")

        return self._templates[template_id]

    def list_templates(self) -> List[str]:
        """
        利用可能なテンプレートIDのリストを取得

        Returns:
            List[str]: テンプレートIDのリスト
        """
        return list(self._templates.keys())

    def format_template(self, template_id: str, variables: Dict[str, Any]) -> str:
        """
        提供された変数でテンプレートをフォーマット

        Args:
            template_id: テンプレートのID
            variables: テンプレートに置換する変数

        Returns:
            str: フォーマット済みプロンプト

        Raises:
            TemplateNotFoundError: テンプレートが見つからない場合
            TemplateSyntaxError: テンプレートのフォーマットエラーが発生した場合
        """
        template = self.get_template(template_id)

        # 必須変数のチェック
        for var in template.variables:
            if var.required and var.name not in variables and var.default is None:
                raise TemplateSyntaxError(
                    f"Required variable '{var.name}' not provided"
                )

        # 不足している変数にデフォルト値を適用
        for var in template.variables:
            if var.name not in variables and var.default is not None:
                variables[var.name] = var.default

        # テンプレートのフォーマット
        formatted = template.template

        # {{variable}} プレースホルダーの置換
        var_pattern = r"{{([^{}]+)}}"

        def replace_var(match):
            var_name = match.group(1).strip()
            if var_name not in variables:
                raise TemplateSyntaxError(
                    f"Variable '{var_name}' used in template but not provided"
                )
            return str(variables[var_name])

        try:
            formatted = re.sub(var_pattern, replace_var, formatted)
            return formatted
        except Exception as e:
            raise TemplateSyntaxError(f"Error formatting template: {str(e)}")

    def save_template(self, template: PromptTemplate) -> None:
        """
        テンプレートをテンプレートディレクトリに保存

        Args:
            template: 保存するテンプレート
        """
        file_path = os.path.join(self.templates_dir, f"{template.id}.json")

        # 辞書に変換
        template_dict = template.model_dump()

        # ファイルに保存
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(template_dict, f, indent=2, ensure_ascii=False)

        # キャッシュを更新
        self._templates[template.id] = template

    def add_template(self, template_data: Dict[str, Any]) -> PromptTemplate:
        """
        新しいテンプレートを追加

        Args:
            template_data: テンプレートデータ

        Returns:
            PromptTemplate: 追加されたテンプレート
        """
        template = PromptTemplate(**template_data)
        self.save_template(template)
        return template

    def delete_template(self, template_id: str) -> bool:
        """
        テンプレートを削除

        Args:
            template_id: 削除するテンプレートのID

        Returns:
            bool: 削除が成功した場合True
        """
        if template_id not in self._templates:
            return False

        # ファイルを削除
        file_path = os.path.join(self.templates_dir, f"{template_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)

        # キャッシュから削除
        del self._templates[template_id]
        return True

    def reload_templates(self) -> None:
        """
        テンプレートを再読み込み
        """
        self._templates.clear()
        self._load_templates()

    def validate_template(self, template_data: Dict[str, Any]) -> List[str]:
        """
        テンプレートデータの検証

        Args:
            template_data: 検証するテンプレートデータ

        Returns:
            List[str]: エラーメッセージのリスト（空の場合は有効）
        """
        errors = []

        # 必須フィールドのチェック
        required_fields = ["id", "template"]
        for field in required_fields:
            if field not in template_data or not template_data[field]:
                errors.append(f"Required field '{field}' is missing")

        # テンプレート構文のチェック
        if "template" in template_data:
            template_text = template_data["template"]
            var_pattern = r"{{([^{}]+)}}"
            used_vars = set(re.findall(var_pattern, template_text))

            defined_vars = set()
            if "variables" in template_data:
                defined_vars = set(var["name"] for var in template_data["variables"])

            # 未定義変数のチェック
            undefined_vars = used_vars - defined_vars
            if undefined_vars:
                errors.append(
                    f"Undefined variables in template: {', '.join(undefined_vars)}"
                )

        return errors
