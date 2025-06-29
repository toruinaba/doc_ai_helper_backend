# LLM経由GitHub MCP E2Eテスト用環境変数設定
# PowerShellで実行する例:

# OpenAI設定（既存の.envから）
$env:OPENAI_API_KEY="sk-12345"  # 実際のキーに変更
$env:OPENAI_BASE_URL="http://internal-internalalb-1876842487.ap-northeast-1.elb.amazonaws.com:4000/"

# GitHub設定（実際のトークンとリポジトリに変更）
$env:GITHUB_TOKEN="ghp_your_actual_github_token_here"
$env:TEST_GITHUB_REPOSITORY="your-username/your-test-repo"

# テスト実行
python test_simple_llm_github.py

# 完全E2Eテスト実行（準備できていれば）
# python test_llm_github_e2e.py
