# API経由でMCPツールを使用する方法

このドキュメントでは、フロントエンドからAPI経由でMCPツールを使用する方法を説明します。

## 基本的なLLMクエリ（ツール無効）

まず、通常のLLMクエリからテストします：

```bash
curl -X POST "http://localhost:8000/api/v1/llm/query" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello, how are you?",
    "provider": "openai",
    "enable_tools": false
  }'
```

## MCPツールを有効にしたLLMクエリ

### 1. ドキュメント分析ツールの使用

```bash
curl -X POST "http://localhost:8000/api/v1/llm/query" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "この文書の構造を分析してください:\n\n# プロジェクト概要\n\nこれはサンプルプロジェクトです。\n\n## 機能\n\n- 機能A\n- 機能B\n\n## 使用方法\n\n1. インストール\n2. 設定\n3. 実行",
    "provider": "openai",
    "enable_tools": true,
    "tool_choice": "auto"
  }'
```

### 2. 計算ツールの使用

```bash
curl -X POST "http://localhost:8000/api/v1/llm/query" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "100 × 25 + 75を計算してください",
    "provider": "openai",
    "enable_tools": true,
    "tool_choice": "auto"
  }'
```

### 3. フィードバック生成ツールの使用

```bash
curl -X POST "http://localhost:8000/api/v1/llm/query" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "この会話からフィードバックを生成してください",
    "provider": "openai",
    "enable_tools": true,
    "tool_choice": "auto",
    "conversation_history": [
      {
        "role": "user",
        "content": "ドキュメントが分かりにくいです",
        "timestamp": "2024-01-01T00:00:00Z"
      },
      {
        "role": "assistant", 
        "content": "どの部分が分かりにくいですか？",
        "timestamp": "2024-01-01T00:01:00Z"
      },
      {
        "role": "user",
        "content": "構造が複雑すぎます",
        "timestamp": "2024-01-01T00:02:00Z"
      }
    ]
  }'
```

### 4. 特定のツールを強制実行

```bash
curl -X POST "http://localhost:8000/api/v1/llm/query" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "このテキストをタイトルケースにフォーマットしてください: hello world",
    "provider": "openai",
    "enable_tools": true,
    "tool_choice": "format_text"
  }'
```

## ストリーミングレスポンス（SSE）でのツール使用

```bash
curl -X POST "http://localhost:8000/api/v1/llm/stream" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "prompt": "1から10まで足した値を計算してください",
    "provider": "openai",
    "enable_tools": true,
    "tool_choice": "auto"
  }'
```

## レスポンス例

### 通常のクエリレスポンス

```json
{
  "content": "こんにちは！元気です。何かお手伝いできることはありますか？",
  "model": "gpt-3.5-turbo",
  "provider": "openai",
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 25,
    "total_tokens": 37
  },
  "raw_response": {...},
  "tool_calls": null,
  "tool_execution_results": null
}
```

### ツール実行を含むレスポンス

```json
{
  "content": "計算結果は2575です。",
  "model": "gpt-3.5-turbo",
  "provider": "openai",
  "usage": {
    "prompt_tokens": 45,
    "completion_tokens": 15,
    "total_tokens": 60
  },
  "tool_calls": [
    {
      "id": "call_123456",
      "type": "function",
      "function": {
        "name": "calculate",
        "arguments": "{\"expression\": \"100 * 25 + 75\"}"
      }
    }
  ],
  "tool_execution_results": [
    {
      "tool_call_id": "call_123456",
      "function_name": "calculate",
      "result": "{\"success\": true, \"result\": 2575}"
    }
  ]
}
```

## 利用可能なMCPツール

### ドキュメントツール
- `analyze_document_structure`: ドキュメントの構造を分析
- `extract_document_context`: ドキュメントからコンテキストを抽出
- `optimize_document_content`: ドキュメントコンテンツを最適化

### ユーティリティツール
- `calculate`: 数式の計算
- `format_text`: テキストフォーマット（uppercase, lowercase, title, capitalize）

### フィードバックツール
- `generate_feedback_from_conversation`: 会話からフィードバックを生成
- `analyze_conversation_quality`: 会話品質を分析

### 分析ツール
- `analyze_text_sentiment`: テキストの感情分析
- `extract_key_topics`: テキストから主要トピックを抽出

## JavaScript/TypeScriptでの使用例

```typescript
// 基本的なLLMクエリ
async function queryLLM(prompt: string, enableTools: boolean = false) {
  const response = await fetch('http://localhost:8000/api/v1/llm/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      prompt,
      provider: 'openai',
      enable_tools: enableTools,
      tool_choice: 'auto'
    })
  });
  
  return await response.json();
}

// ツールを使用した計算
const result = await queryLLM('100 × 25を計算してください', true);
console.log(result);

// ストリーミングレスポンス
async function streamQuery(prompt: string) {
  const response = await fetch('http://localhost:8000/api/v1/llm/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream'
    },
    body: JSON.stringify({
      prompt,
      provider: 'openai',
      enable_tools: true,
      tool_choice: 'auto'
    })
  });

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader!.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        if (data.text) {
          console.log(data.text);
        } else if (data.done) {
          console.log('Stream completed');
        } else if (data.error) {
          console.error('Stream error:', data.error);
        }
      }
    }
  }
}
```

## React フックの例

```tsx
import { useState, useCallback } from 'react';

interface LLMResponse {
  content: string;
  model: string;
  provider: string;
  tool_calls?: any[];
  tool_execution_results?: any[];
}

export function useLLMQuery() {
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<LLMResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const queryWithTools = useCallback(async (
    prompt: string, 
    enableTools: boolean = true,
    toolChoice: string = 'auto'
  ) => {
    setLoading(true);
    setError(null);
    
    try {
      const res = await fetch('/api/v1/llm/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt,
          provider: 'openai',
          enable_tools: enableTools,
          tool_choice: toolChoice
        })
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data = await res.json();
      setResponse(data);
      return data;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { queryWithTools, loading, response, error };
}

// 使用例
function LLMQueryComponent() {
  const { queryWithTools, loading, response, error } = useLLMQuery();

  const handleCalculation = async () => {
    await queryWithTools('100 + 200を計算してください', true);
  };

  const handleDocumentAnalysis = async () => {
    await queryWithTools(
      'このドキュメントの構造を分析してください:\n\n# タイトル\n\n内容...',
      true
    );
  };

  return (
    <div>
      <button onClick={handleCalculation} disabled={loading}>
        計算実行
      </button>
      <button onClick={handleDocumentAnalysis} disabled={loading}>
        文書分析
      </button>
      
      {loading && <p>処理中...</p>}
      {error && <p>エラー: {error}</p>}
      {response && (
        <div>
          <h3>レスポンス:</h3>
          <p>{response.content}</p>
          {response.tool_execution_results && (
            <div>
              <h4>ツール実行結果:</h4>
              <pre>{JSON.stringify(response.tool_execution_results, null, 2)}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

## 注意事項

1. **環境変数**: OpenAI APIキーやベースURLが適切に設定されている必要があります
2. **ツール有効化**: `enable_tools: true` を設定しないとMCPツールは使用されません
3. **プロバイダー**: 現在は `openai` と `mock` がサポートされています
4. **レート制限**: OpenAI APIのレート制限に注意してください
5. **エラーハンドリング**: ツール実行エラーは `tool_execution_results` の `error` フィールドに含まれます

## トラブルシューティング

### よくある問題

1. **ツールが実行されない**
   - `enable_tools: true` が設定されているか確認
   - `tool_choice` が適切に設定されているか確認

2. **認証エラー**
   - `OPENAI_API_KEY` 環境変数が設定されているか確認
   - `OPENAI_BASE_URL` が正しく設定されているか確認

3. **レスポンスが遅い**
   - 複雑なツール実行は時間がかかる場合があります
   - ストリーミングAPIの使用を検討してください
