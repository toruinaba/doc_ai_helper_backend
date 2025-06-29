# README改善確認フロー付きテスト実行スクリプト
#
# 使用方法:
#   .\run_confirmation_test.ps1              # 自動モード
#   .\run_confirmation_test.ps1 -Interactive # インタラクティブモード

param(
    [switch]$Interactive,
    [string]$Repository = $env:TEST_GITHUB_REPOSITORY
)

Write-Host "🔄 README改善確認フロー付きテスト" -ForegroundColor Cyan
Write-Host "=" * 50

# 環境変数チェック
$missingVars = @()

if (-not $env:OPENAI_API_KEY) {
    $missingVars += "OPENAI_API_KEY"
}

if (-not $env:GITHUB_TOKEN) {
    $missingVars += "GITHUB_TOKEN"
}

if ($missingVars.Count -gt 0) {
    Write-Host "❌ 以下の環境変数が設定されていません:" -ForegroundColor Red
    foreach ($var in $missingVars) {
        Write-Host "   - $var" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "📝 環境変数設定例:" -ForegroundColor Yellow
    Write-Host "   `$env:OPENAI_API_KEY='sk-your-key-here'" -ForegroundColor Yellow
    Write-Host "   `$env:GITHUB_TOKEN='ghp-your-token-here'" -ForegroundColor Yellow
    Write-Host "   `$env:TEST_GITHUB_REPOSITORY='your-username/your-test-repo'" -ForegroundColor Yellow
    exit 1
}

# リポジトリ指定
if ($Repository) {
    $env:TEST_GITHUB_REPOSITORY = $Repository
    Write-Host "📂 対象リポジトリ: $Repository" -ForegroundColor Green
}

# Python実行
try {
    if ($Interactive) {
        Write-Host "🎮 インタラクティブモード（ユーザー入力あり）" -ForegroundColor Green
        python run_confirmation_test.py --interactive
    } else {
        Write-Host "🤖 自動モード（テスト用）" -ForegroundColor Green
        python run_confirmation_test.py
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ テスト成功！" -ForegroundColor Green
    } else {
        Write-Host "❌ テスト失敗" -ForegroundColor Red
        exit $LASTEXITCODE
    }
} catch {
    Write-Host "❌ テスト実行エラー: $_" -ForegroundColor Red
    exit 1
}
