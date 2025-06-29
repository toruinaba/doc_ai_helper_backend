# LLM経由GitHub MCP E2Eテスト実行スクリプト (修正版)
# README改善フローを含む包括的なE2Eテスト

param(
    [switch]$LoadEnv = $false,
    [switch]$TestOnly = $false,
    [string]$Repository = "",
    [switch]$Help = $false
)

if ($Help) {
    Write-Host "🧪 LLM経由GitHub MCP E2Eテスト実行スクリプト" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "使用方法:"
    Write-Host "  .\run_e2e_tests_fixed.ps1 [-LoadEnv] [-TestOnly] [-Repository <repo>] [-Help]"
    Write-Host ""
    Write-Host "オプション:"
    Write-Host "  -LoadEnv      .env.github_test から環境変数を読み込み"
    Write-Host "  -TestOnly     環境確認をスキップしてテストのみ実行"
    Write-Host "  -Repository   テスト対象リポジトリを指定 (owner/repo形式)"
    Write-Host "  -Help         このヘルプを表示"
    Write-Host ""
    Write-Host "例:"
    Write-Host "  .\run_e2e_tests_fixed.ps1 -LoadEnv"
    Write-Host "  .\run_e2e_tests_fixed.ps1 -Repository 'myuser/test-repo'"
    exit 0
}

Write-Host "🧪 LLM経由GitHub MCP E2Eテスト実行スクリプト (修正版)" -ForegroundColor Cyan
Write-Host "=" * 60

# .env.github_test から環境変数を読み込み
if ($LoadEnv -and (Test-Path ".env.github_test")) {
    Write-Host "📄 .env.github_test から環境変数を読み込み中..." -ForegroundColor Yellow
    
    Get-Content ".env.github_test" | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            
            # クォートを除去
            if ($value.StartsWith('"') -and $value.EndsWith('"')) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
            Write-Host "   ✅ $name 設定完了" -ForegroundColor Green
        }
    }
    Write-Host ""
}

# リポジトリ指定があれば設定
if ($Repository -ne "") {
    $env:TEST_GITHUB_REPOSITORY = $Repository
    Write-Host "🎯 テスト対象リポジトリ: $Repository" -ForegroundColor Cyan
    Write-Host ""
}

# 環境変数確認
if (-not $TestOnly) {
    Write-Host "🔧 環境変数確認:" -ForegroundColor Yellow
    
    $requiredVars = @{
        "OPENAI_API_KEY" = $env:OPENAI_API_KEY
        "GITHUB_TOKEN" = $env:GITHUB_TOKEN
        "TEST_GITHUB_REPOSITORY" = $env:TEST_GITHUB_REPOSITORY
    }
    
    $allSet = $true
    foreach ($var in $requiredVars.GetEnumerator()) {
        if ($var.Value) {
            Write-Host "   ✅ $($var.Key): 設定済み" -ForegroundColor Green
        } else {
            Write-Host "   ❌ $($var.Key): 未設定" -ForegroundColor Red
            $allSet = $false
        }
    }
    
    Write-Host ""
    
    if (-not $allSet) {
        Write-Host "❌ 必要な環境変数が設定されていません" -ForegroundColor Red
        Write-Host ""
        Write-Host "設定例:" -ForegroundColor Yellow
        Write-Host '   $env:OPENAI_API_KEY="sk-your-openai-api-key"'
        Write-Host '   $env:GITHUB_TOKEN="ghp-your-github-token"'
        Write-Host '   $env:TEST_GITHUB_REPOSITORY="your-username/your-test-repo"'
        Write-Host ""
        Write-Host "または .env.github_test ファイルを作成して -LoadEnv オプションを使用してください"
        exit 1
    }
}

# Pythonの確認
try {
    $pythonVersion = python --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "🐍 Python: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "❌ Pythonが見つかりません" -ForegroundColor Red
    exit 1
}

# E2Eテストの実行
Write-Host "🚀 README改善フローを含むLLM経由GitHub MCP E2Eテスト開始..." -ForegroundColor Cyan
Write-Host ""

try {
    # 修正版のE2Eテストファイルを実行
    python test_llm_github_e2e_fixed.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "🎉 E2Eテスト実行完了!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📋 実行されたテスト:" -ForegroundColor Cyan
        Write-Host "   1. GitHub権限確認テスト" -ForegroundColor White
        Write-Host "   2. 📖 README改善フローE2Eテスト (NEW!)" -ForegroundColor Yellow
        Write-Host "   3. 基本GitHub Issue作成テスト" -ForegroundColor White
        Write-Host ""
        Write-Host "💡 README改善フローテストでは:" -ForegroundColor Cyan
        Write-Host "   - サンプルREADMEコンテンツの分析" -ForegroundColor White
        Write-Host "   - LLMによる改善点の特定" -ForegroundColor White
        Write-Host "   - 実用的な改善提案のIssue作成" -ForegroundColor White
        Write-Host "   - 新規開発者向けの親切なドキュメント提案" -ForegroundColor White
    } else {
        Write-Host ""
        Write-Host "⚠️ E2Eテスト中にエラーが発生しました" -ForegroundColor Yellow
        Write-Host "詳細はテストログを確認してください" -ForegroundColor White
    }
} catch {
    Write-Host ""
    Write-Host "❌ E2Eテスト実行中にエラー: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📊 テスト完了。結果をご確認ください。" -ForegroundColor Cyan
