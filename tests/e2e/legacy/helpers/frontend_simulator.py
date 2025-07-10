"""
フロントエンドシミュレーター for E2E Tests

このモジュールは、フロントエンドアプリケーションの動作をシミュレートし、
実際のユーザー体験を再現するヘルパークラスを提供します。
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .api_client import BackendAPIClient

logger = logging.getLogger(__name__)


@dataclass
class UserSession:
    """ユーザーセッション情報"""

    persona_id: str
    session_start: float
    interactions: List[Dict[str, Any]]
    context: Dict[str, Any]


@dataclass
class InteractionResult:
    """ユーザーインタラクション結果"""

    action: str
    duration: float
    success: bool
    data: Dict[str, Any]
    user_satisfaction: float = 0.0


class FrontendSimulator:
    """
    フロントエンドアプリケーションの動作をシミュレート

    このクラスは、実際のフロントエンドユーザーが行う操作を
    バックエンドAPI呼び出しの組み合わせとして再現します。
    """

    def __init__(self, backend_api_client: BackendAPIClient):
        """
        Initialize the frontend simulator.

        Args:
            backend_api_client: バックエンドAPIクライアント
        """
        self.api_client = backend_api_client
        self.current_session: Optional[UserSession] = None
        self.interaction_history: List[InteractionResult] = []

    def start_session(
        self, persona_id: str, context: Dict[str, Any] = None
    ) -> UserSession:
        """
        ユーザーセッションを開始する

        Args:
            persona_id: ユーザーペルソナID
            context: セッションコンテキスト

        Returns:
            開始されたユーザーセッション
        """
        self.current_session = UserSession(
            persona_id=persona_id,
            session_start=time.time(),
            interactions=[],
            context=context or {},
        )

        logger.info(f"🚀 Started user session for persona: {persona_id}")
        return self.current_session

    async def connect_to_repository(
        self, service: str, owner: str, repo: str, user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        フロントエンドからのリポジトリ接続をシミュレート

        Args:
            service: Gitサービス名
            owner: リポジトリオーナー
            repo: リポジトリ名
            user_context: ユーザーコンテキスト

        Returns:
            接続結果とフロントエンド用拡張情報
        """
        start_time = time.time()

        try:
            # Step 1: リポジトリ構造取得
            logger.info(f"📡 Connecting to repository: {service}/{owner}/{repo}")

            structure = await self.api_client.get_repository_structure(
                service=service, owner=owner, repo=repo
            )

            # Step 2: フロントエンド用の拡張情報を付与
            enhanced_structure = self._enhance_for_frontend(structure, user_context)

            # Step 3: ユーザーコンテキストに基づく初期推奨の生成
            initial_recommendations = await self._generate_initial_recommendations(
                enhanced_structure, user_context
            )

            connection_time = time.time() - start_time
            self._record_interaction(
                "repository_connection",
                connection_time,
                True,
                {
                    "service": service,
                    "owner": owner,
                    "repo": repo,
                    "structure_items": len(structure.get("tree", [])),
                    "recommendations": len(initial_recommendations),
                },
            )

            return {
                "status": "connected",
                "repository_info": enhanced_structure,
                "welcome_guidance": self._generate_welcome_message(user_context),
                "recommended_first_steps": initial_recommendations,
                "connection_time": connection_time,
                "user_hints": self._generate_user_hints(user_context),
            }

        except Exception as e:
            connection_time = time.time() - start_time
            self._record_interaction(
                "repository_connection", connection_time, False, {"error": str(e)}
            )
            raise

    async def get_beginner_guidance(
        self, repository_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        初心者向けガイダンスの取得

        Args:
            repository_info: リポジトリ情報

        Returns:
            初心者向けガイダンス情報
        """
        start_time = time.time()

        guidance_prompt = """
        このプロジェクトに新しく参加した初心者開発者に対して、
        どのドキュメントから読み始めるべきか推奨してください。
        読む順序と各文書の重要度、推定読解時間も含めてください。
        
        レスポンス形式:
        {
          "recommended_documents": [
            {
              "path": "ファイルパス",
              "title": "タイトル", 
              "priority": "high/medium/low",
              "difficulty": "beginner/intermediate/advanced",
              "estimated_reading_time": 分,
              "description": "なぜこの文書が重要か"
            }
          ],
          "learning_sequence": "推奨する学習順序の説明",
          "key_concepts": ["重要な概念1", "重要な概念2"]
        }
        """

        ai_response = await self.api_client.query_llm(
            prompt=guidance_prompt,
            context={"repository": repository_info},
            provider="openai",
        )

        guidance_time = time.time() - start_time
        parsed_guidance = self._parse_guidance_response(ai_response)

        self._record_interaction(
            "beginner_guidance",
            guidance_time,
            True,
            {
                "documents_recommended": len(
                    parsed_guidance.get("recommended_documents", [])
                ),
                "guidance_quality": self._assess_guidance_quality(parsed_guidance),
            },
        )

        return parsed_guidance

    async def get_document_with_assistance(
        self,
        path: str,
        reading_level: str = "beginner",
        service: str = "forgejo",
        owner: str = None,
        repo: str = None,
    ) -> Dict[str, Any]:
        """
        読解支援付きでドキュメントを取得

        Args:
            path: ドキュメントパス
            reading_level: 読解レベル
            service: Gitサービス
            owner: オーナー
            repo: リポジトリ

        Returns:
            読解支援情報付きドキュメント
        """
        start_time = time.time()

        # セッションコンテキストから情報を取得
        if self.current_session and not owner:
            owner = self.current_session.context.get("owner")
            repo = self.current_session.context.get("repo")

        # ドキュメント取得
        document = await self.api_client.get_document(
            service=service, owner=owner, repo=repo, path=path
        )

        # 読解支援情報を追加
        enhanced_document = self._add_reading_assistance(document, reading_level)

        document_time = time.time() - start_time
        self._record_interaction(
            "document_retrieval",
            document_time,
            True,
            {
                "path": path,
                "content_length": len(document.get("content", {}).get("content", "")),
                "reading_level": reading_level,
            },
        )

        return enhanced_document

    async def get_ai_explanation(
        self, document: Dict[str, Any], question: str
    ) -> Dict[str, Any]:
        """
        ドキュメントに対するAI説明の取得

        Args:
            document: ドキュメント情報
            question: 質問内容

        Returns:
            AI説明結果
        """
        start_time = time.time()

        explanation_prompt = f"""
        以下のドキュメントについて質問に答えてください。
        
        ドキュメント: {document.get('path', 'Unknown')}
        内容: {document.get('content', {}).get('content', '')[:1000]}
        
        質問: {question}
        
        回答は以下の形式でお願いします:
        {{
          "explanation": "わかりやすい説明",
          "key_points": ["重要なポイント1", "重要なポイント2"],
          "suggested_questions": ["関連する質問1", "関連する質問2"],
          "clarity_score": 0.0-1.0,
          "comprehension_boost": 0.0-1.0
        }}
        """

        ai_response = await self.api_client.query_llm(
            prompt=explanation_prompt, context={"document": document}, provider="openai"
        )

        explanation_time = time.time() - start_time
        parsed_explanation = self._parse_explanation_response(ai_response)

        self._record_interaction(
            "ai_explanation",
            explanation_time,
            True,
            {
                "question_type": self._classify_question(question),
                "explanation_quality": parsed_explanation.get("clarity_score", 0),
                "learning_boost": parsed_explanation.get("comprehension_boost", 0),
            },
        )

        return parsed_explanation

    async def analyze_document_quality(
        self, document: Dict[str, Any], analysis_focus: List[str] = None
    ) -> Dict[str, Any]:
        """
        ドキュメント品質分析

        Args:
            document: 分析対象ドキュメント
            analysis_focus: 分析焦点リスト

        Returns:
            品質分析結果
        """
        start_time = time.time()

        focus_areas = analysis_focus or ["clarity", "completeness", "usability"]

        analysis_prompt = f"""
        以下のドキュメントの品質を分析してください。
        
        ドキュメント: {document.get('path', 'Unknown')}
        内容: {document.get('content', {}).get('content', '')[:1500]}
        
        分析観点: {', '.join(focus_areas)}
        
        以下の形式で分析結果を返してください:
        {{
          "quality_score": 0.0-1.0,
          "specific_issues": [
            {{
              "category": "問題カテゴリ",
              "description": "具体的な問題", 
              "severity": "high/medium/low",
              "location": "問題箇所"
            }}
          ],
          "strengths": ["良い点1", "良い点2"],
          "improvement_areas": ["改善点1", "改善点2"]
        }}
        """

        ai_response = await self.api_client.query_llm(
            prompt=analysis_prompt,
            context={"document": document, "focus": focus_areas},
            provider="openai",
        )

        analysis_time = time.time() - start_time
        parsed_analysis = self._parse_analysis_response(ai_response)

        self._record_interaction(
            "quality_analysis",
            analysis_time,
            True,
            {
                "focus_areas": focus_areas,
                "issues_found": len(parsed_analysis.get("specific_issues", [])),
                "quality_score": parsed_analysis.get("quality_score", 0),
            },
        )

        return parsed_analysis

    async def create_team_issue(
        self,
        analysis: Dict[str, Any],
        priority: str = "medium",
        assign_reviewers: bool = True,
    ) -> Dict[str, Any]:
        """
        チーム向けIssue作成

        Args:
            analysis: 分析結果
            priority: 優先度
            assign_reviewers: レビュアー自動アサイン

        Returns:
            Issue作成結果
        """
        start_time = time.time()

        if not self.current_session:
            raise ValueError("Active session required for issue creation")

        # Issue作成用のプロンプト構築
        issue_prompt = f"""
        以下の分析結果に基づいてGitHubのIssueを作成してください。
        必ずcreate_git_issue関数を使用してください。
        
        分析結果: {json.dumps(analysis, ensure_ascii=False, indent=2)}
        優先度: {priority}
        
        Issueの要件:
        - タイトル: "[AI分析] ドキュメント改善提案"
        - 説明: 分析結果と具体的な改善提案
        - ラベル: ["documentation", "improvement", "ai-generated"]
        - 優先度ラベル: ["priority-{priority}"]
        
        create_git_issue関数を呼び出して実際にIssueを作成してください。
        """

        # MCPツールを有効にしてIssue作成
        mcp_response = await self.api_client.query_llm(
            prompt=issue_prompt,
            context={
                "analysis": analysis,
                "repository_context": self.current_session.context,
            },
            provider="openai",
            tools_enabled=True,
            repository_context=self.current_session.context,
        )

        issue_time = time.time() - start_time
        issue_result = self._extract_issue_creation_result(mcp_response)

        self._record_interaction(
            "issue_creation",
            issue_time,
            issue_result.get("created_successfully", False),
            {
                "priority": priority,
                "analysis_quality": analysis.get("quality_score", 0),
                "issue_id": issue_result.get("issue_id"),
            },
        )

        return issue_result

    def get_session_summary(self) -> Dict[str, Any]:
        """
        セッションサマリーの取得

        Returns:
            セッション実行結果のサマリー
        """
        if not self.current_session:
            return {"error": "No active session"}

        total_time = time.time() - self.current_session.session_start
        successful_interactions = [i for i in self.interaction_history if i.success]

        return {
            "persona_id": self.current_session.persona_id,
            "total_time": total_time,
            "total_interactions": len(self.interaction_history),
            "successful_interactions": len(successful_interactions),
            "success_rate": (
                len(successful_interactions) / len(self.interaction_history)
                if self.interaction_history
                else 0
            ),
            "average_satisfaction": (
                sum(i.user_satisfaction for i in self.interaction_history)
                / len(self.interaction_history)
                if self.interaction_history
                else 0
            ),
            "interactions": [
                {
                    "action": i.action,
                    "duration": i.duration,
                    "success": i.success,
                    "satisfaction": i.user_satisfaction,
                }
                for i in self.interaction_history
            ],
        }

    # Private helper methods

    def _enhance_for_frontend(
        self, raw_structure: Dict, user_context: Dict
    ) -> Dict[str, Any]:
        """バックエンドレスポンスをフロントエンド表示用に拡張"""
        enhanced = raw_structure.copy()

        # フロントエンドナビゲーション用の情報を追加
        enhanced["navigation_tree"] = self._build_navigation_tree(
            raw_structure.get("tree", [])
        )
        enhanced["document_count"] = len(
            [f for f in raw_structure.get("tree", []) if f.get("type") == "file"]
        )
        enhanced["estimated_reading_time"] = self._estimate_total_reading_time(
            raw_structure.get("tree", [])
        )

        # ユーザーコンテキストに基づくパーソナライゼーション
        if user_context.get("experience_level") == "beginner":
            enhanced["beginner_mode"] = True
            enhanced["complexity_warnings"] = self._identify_complex_documents(
                raw_structure.get("tree", [])
            )

        return enhanced

    def _generate_welcome_message(self, user_context: Dict) -> str:
        """ユーザーコンテキストに基づくウェルカムメッセージ生成"""
        experience = user_context.get("experience_level", "intermediate")

        messages = {
            "beginner": "プロジェクトへようこそ！初心者向けのガイダンスを用意しています。",
            "intermediate": "プロジェクトへようこそ！効率的に情報を見つけるお手伝いをします。",
            "senior": "プロジェクトへようこそ！必要な情報への迅速なアクセスをサポートします。",
        }

        return messages.get(experience, messages["intermediate"])

    def _record_interaction(
        self, action: str, duration: float, success: bool, data: Dict[str, Any]
    ):
        """インタラクション結果を記録"""
        if self.current_session:
            interaction = InteractionResult(
                action=action,
                duration=duration,
                success=success,
                data=data,
                user_satisfaction=self._calculate_satisfaction(
                    action, duration, success
                ),
            )

            self.interaction_history.append(interaction)
            self.current_session.interactions.append(
                {
                    "action": action,
                    "timestamp": time.time(),
                    "duration": duration,
                    "success": success,
                    "data": data,
                }
            )

    def _calculate_satisfaction(
        self, action: str, duration: float, success: bool
    ) -> float:
        """ユーザー満足度の計算"""
        if not success:
            return 0.0

        # アクション別の期待時間
        expected_times = {
            "repository_connection": 5.0,
            "beginner_guidance": 10.0,
            "document_retrieval": 3.0,
            "ai_explanation": 15.0,
            "quality_analysis": 20.0,
            "issue_creation": 10.0,
        }

        expected = expected_times.get(action, 10.0)
        time_ratio = min(duration / expected, 2.0)  # 期待時間の2倍まで

        # 時間効率による満足度 (期待時間以内なら1.0、超過すると減少)
        if time_ratio <= 1.0:
            return 1.0
        else:
            return max(0.3, 1.0 - (time_ratio - 1.0) * 0.5)

    # Response parsing methods

    def _parse_guidance_response(self, ai_response: Dict) -> Dict[str, Any]:
        """AI ガイダンスレスポンスの解析"""
        try:
            content = ai_response.get("content", "")
            # JSONの抽出を試行
            if "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
                return json.loads(json_str)
        except:
            pass

        # デフォルトガイダンス
        return {
            "recommended_documents": [
                {
                    "path": "README.md",
                    "priority": "high",
                    "difficulty": "beginner",
                    "estimated_reading_time": 10,
                }
            ],
            "learning_sequence": "README.mdから始めることをお勧めします",
            "key_concepts": ["プロジェクト概要", "セットアップ"],
        }

    def _parse_explanation_response(self, ai_response: Dict) -> Dict[str, Any]:
        """AI 説明レスポンスの解析"""
        try:
            content = ai_response.get("content", "")
            if "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
                return json.loads(json_str)
        except:
            pass

        return {
            "explanation": ai_response.get("content", "説明を生成できませんでした"),
            "key_points": [],
            "suggested_questions": [],
            "clarity_score": 0.7,
            "comprehension_boost": 0.5,
        }

    def _parse_analysis_response(self, ai_response: Dict) -> Dict[str, Any]:
        """AI 分析レスポンスの解析"""
        try:
            content = ai_response.get("content", "")
            if "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
                return json.loads(json_str)
        except:
            pass

        return {
            "quality_score": 0.6,
            "specific_issues": [
                {
                    "category": "一般",
                    "description": "分析が不完全です",
                    "severity": "medium",
                    "location": "全体",
                }
            ],
            "strengths": [],
            "improvement_areas": ["分析精度の向上"],
        }

    def _extract_issue_creation_result(self, mcp_response: Dict) -> Dict[str, Any]:
        """MCP レスポンスからIssue作成結果を抽出"""
        if "tool_execution_results" in mcp_response:
            for result in mcp_response["tool_execution_results"]:
                if result.get("function_name") == "create_git_issue":
                    if result.get("result", {}).get("success"):
                        return {
                            "created_successfully": True,
                            "issue_id": result.get("result", {})
                            .get("result", {})
                            .get("data", {})
                            .get("issue_number"),
                            "issue_url": result.get("result", {})
                            .get("result", {})
                            .get("data", {})
                            .get("issue_url"),
                            "team_notifications_sent": True,
                        }

        return {
            "created_successfully": False,
            "error": "Issue creation failed or not attempted",
        }

    # Utility methods

    def _build_navigation_tree(self, tree_items: List[Dict]) -> Dict[str, Any]:
        """ナビゲーションツリーの構築"""
        return {
            "files": [item for item in tree_items if item.get("type") == "file"],
            "directories": [
                item for item in tree_items if item.get("type") == "directory"
            ],
            "total_items": len(tree_items),
        }

    def _estimate_total_reading_time(self, tree_items: List[Dict]) -> int:
        """総読解時間の推定（分）"""
        markdown_files = [
            item
            for item in tree_items
            if item.get("name", "").endswith((".md", ".markdown"))
        ]
        return len(markdown_files) * 5  # ファイルあたり5分の推定

    def _identify_complex_documents(self, tree_items: List[Dict]) -> List[str]:
        """複雑なドキュメントの特定"""
        complex_patterns = ["advanced", "architecture", "design", "internals"]
        complex_docs = []

        for item in tree_items:
            name = item.get("name", "").lower()
            if any(pattern in name for pattern in complex_patterns):
                complex_docs.append(item.get("name", ""))

        return complex_docs

    def _classify_question(self, question: str) -> str:
        """質問タイプの分類"""
        question_lower = question.lower()
        if any(word in question_lower for word in ["なぜ", "理由", "why"]):
            return "conceptual"
        elif any(word in question_lower for word in ["どのように", "how", "方法"]):
            return "procedural"
        elif any(word in question_lower for word in ["何", "what", "どれ"]):
            return "factual"
        else:
            return "general"

    def _assess_guidance_quality(self, guidance: Dict) -> float:
        """ガイダンス品質の評価"""
        score = 0.0

        # 推奨ドキュメント数
        docs = guidance.get("recommended_documents", [])
        if len(docs) >= 2:
            score += 0.3

        # 学習順序の提供
        if guidance.get("learning_sequence"):
            score += 0.3

        # 重要概念の提供
        concepts = guidance.get("key_concepts", [])
        if len(concepts) >= 2:
            score += 0.4

        return score

    def _add_reading_assistance(
        self, document: Dict, reading_level: str
    ) -> Dict[str, Any]:
        """読解支援情報の追加"""
        enhanced = document.copy()

        content_length = len(document.get("content", {}).get("content", ""))

        enhanced["reading_assistance"] = {
            "reading_time_estimate": max(2, content_length // 300),  # 分
            "complexity_level": self._assess_complexity(document, reading_level),
            "key_concepts": self._extract_key_concepts(document),
            "reading_level": reading_level,
        }

        return enhanced

    def _assess_complexity(self, document: Dict, reading_level: str) -> str:
        """ドキュメント複雑度の評価"""
        content = document.get("content", {}).get("content", "")

        # 複雑度指標
        technical_terms = len(
            [word for word in content.split() if word.isupper() and len(word) > 2]
        )
        code_blocks = content.count("```")

        if reading_level == "beginner":
            if technical_terms > 10 or code_blocks > 3:
                return "challenging"
            return "appropriate"

        return "appropriate"

    def _extract_key_concepts(self, document: Dict) -> List[str]:
        """重要概念の抽出（簡易版）"""
        content = document.get("content", {}).get("content", "")

        # ヘッダーから概念を抽出
        concepts = []
        for line in content.split("\n"):
            if line.startswith("#"):
                concept = line.strip("#").strip()
                if concept and len(concept) < 50:
                    concepts.append(concept)

        return concepts[:5]  # 最大5つ

    async def _generate_initial_recommendations(
        self, repository_info: Dict, user_context: Dict
    ) -> List[Dict[str, Any]]:
        """初期推奨の生成"""
        # 簡易的な推奨ロジック
        tree_items = repository_info.get("tree", [])
        markdown_files = [
            item
            for item in tree_items
            if item.get("name", "").endswith((".md", ".markdown"))
        ]

        recommendations = []

        # README.mdを最優先
        readme_files = [
            f for f in markdown_files if "readme" in f.get("name", "").lower()
        ]
        if readme_files:
            recommendations.append(
                {
                    "action": "read_document",
                    "path": readme_files[0].get("name"),
                    "reason": "プロジェクトの概要を理解するため",
                    "priority": "high",
                }
            )

        # 設定ファイルを次に推奨
        setup_files = [
            f
            for f in markdown_files
            if any(
                word in f.get("name", "").lower()
                for word in ["setup", "install", "getting", "start"]
            )
        ]
        if setup_files:
            recommendations.append(
                {
                    "action": "read_document",
                    "path": setup_files[0].get("name"),
                    "reason": "開発環境をセットアップするため",
                    "priority": "high",
                }
            )

        return recommendations
