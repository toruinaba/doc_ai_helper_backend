# Forgejo サービス API ドキュメント

このドキュメントでは、フロントエンドから `doc_ai_helper_backend` の Forgejo サービスにアクセスするための API について説明します。

## API エンドポイント

### ベース URL
```
http://localhost:8000/api/v1/documents
```

### 1. ドキュメント取得

#### エンドポイント
```
GET /contents/{service}/{owner}/{repo}/{path:path}
```

#### パラメータ
- `service`: Git サービス (`forgejo`)
- `owner`: リポジトリオーナー
- `repo`: リポジトリ名
- `path`: ドキュメントパス

#### クエリパラメータ（オプション）
- `ref`: ブランチまたはタグ名（デフォルト: `main`）
- `transform_links`: リンク変換を行うか（デフォルト: `true`）
- `base_url`: リンク変換用のベースURL

#### 例
```bash
curl -X GET "http://localhost:8000/api/v1/documents/contents/forgejo/myuser/myrepo/README.md?ref=main&transform_links=true"
```

#### レスポンス
```json
{
  "path": "README.md",
  "name": "README.md",
  "type": "markdown",
  "content": {
    "content": "# My Project\n\nThis is my awesome project.",
    "encoding": "utf-8"
  },
  "metadata": {
    "size": 42,
    "last_modified": "2024-01-01T12:00:00Z",
    "content_type": "text/markdown",
    "sha": "abc123def456",
    "download_url": "https://git.example.com/myuser/myrepo/raw/main/README.md",
    "html_url": "https://git.example.com/myuser/myrepo/blob/main/README.md",
    "raw_url": "https://git.example.com/myuser/myrepo/raw/main/README.md",
    "extra": {}
  },
  "repository": "myrepo",
  "owner": "myuser",
  "service": "forgejo",
  "ref": "main",
  "links": [
    {
      "text": "Documentation",
      "url": "https://git.example.com/myuser/myrepo/blob/main/docs/",
      "is_image": false,
      "position": [10, 30],
      "is_external": false
    }
  ],
  "transformed_content": "# My Project\n\nThis is my awesome project."
}
```

### 2. リポジトリ構造取得

#### エンドポイント
```
GET /structure/{service}/{owner}/{repo}
```

#### パラメータ
- `service`: Git サービス (`forgejo`)
- `owner`: リポジトリオーナー
- `repo`: リポジトリ名

#### クエリパラメータ（オプション）
- `ref`: ブランチまたはタグ名（デフォルト: `main`）
- `path`: パス フィルター（デフォルト: 空文字）

#### 例
```bash
curl -X GET "http://localhost:8000/api/v1/documents/structure/forgejo/myuser/myrepo?ref=main&path=docs/"
```

#### レスポンス
```json
{
  "service": "forgejo",
  "owner": "myuser",
  "repo": "myrepo",
  "ref": "main",
  "tree": [
    {
      "path": "README.md",
      "name": "README.md",
      "type": "file",
      "size": 1024,
      "sha": "abc123def456",
      "download_url": "https://git.example.com/myuser/myrepo/raw/main/README.md",
      "html_url": "https://git.example.com/myuser/myrepo/blob/main/README.md",
      "git_url": "https://git.example.com/myuser/myrepo/git/blobs/abc123def456"
    },
    {
      "path": "docs/",
      "name": "docs",
      "type": "directory",
      "size": null,
      "sha": null,
      "download_url": null,
      "html_url": "https://git.example.com/myuser/myrepo/tree/main/docs",
      "git_url": null
    }
  ],
  "last_updated": "2024-01-01T12:00:00Z"
}
```

## エラーレスポンス

### 404 Not Found
```json
{
  "message": "Unsupported Git service: invalid-service"
}
```

### 500 Internal Server Error
```json
{
  "message": "Git service error",
  "detail": "Connection failed"
}
```

## JavaScript/TypeScript での使用例

### Fetch API を使用
```javascript
// ドキュメント取得
async function getDocument(owner, repo, path, ref = 'main') {
  const url = `http://localhost:8000/api/v1/documents/contents/forgejo/${owner}/${repo}/${path}?ref=${ref}`;
  
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const document = await response.json();
    return document;
  } catch (error) {
    console.error('Error fetching document:', error);
    throw error;
  }
}

// リポジトリ構造取得
async function getRepositoryStructure(owner, repo, ref = 'main', path = '') {
  const url = `http://localhost:8000/api/v1/documents/structure/forgejo/${owner}/${repo}?ref=${ref}&path=${path}`;
  
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const structure = await response.json();
    return structure;
  } catch (error) {
    console.error('Error fetching structure:', error);
    throw error;
  }
}

// 使用例
getDocument('myuser', 'myrepo', 'README.md')
  .then(doc => {
    console.log('Document content:', doc.content.content);
    console.log('Links found:', doc.links.length);
  })
  .catch(error => console.error('Failed to get document:', error));
```

### axios を使用
```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1/documents',
  timeout: 30000,
});

// ドキュメント取得
export const getDocument = async (owner, repo, path, options = {}) => {
  const { ref = 'main', transform_links = true, base_url } = options;
  
  const params = { ref, transform_links };
  if (base_url) params.base_url = base_url;
  
  const response = await api.get(`/contents/forgejo/${owner}/${repo}/${path}`, { params });
  return response.data;
};

// リポジトリ構造取得
export const getRepositoryStructure = async (owner, repo, options = {}) => {
  const { ref = 'main', path = '' } = options;
  
  const params = { ref };
  if (path) params.path = path;
  
  const response = await api.get(`/structure/forgejo/${owner}/${repo}`, { params });
  return response.data;
};
```

## React コンポーネント例

```jsx
import React, { useState, useEffect } from 'react';
import { getDocument, getRepositoryStructure } from './api';

const ForgejoDocumentViewer = ({ owner, repo, path = 'README.md' }) => {
  const [document, setDocument] = useState(null);
  const [structure, setStructure] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // ドキュメントと構造を並行で取得
        const [docData, structureData] = await Promise.all([
          getDocument(owner, repo, path),
          getRepositoryStructure(owner, repo)
        ]);
        
        setDocument(docData);
        setStructure(structureData);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [owner, repo, path]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h1>{document?.name}</h1>
      
      <div style={{ display: 'flex' }}>
        {/* ファイル一覧 */}
        <aside style={{ width: '300px', marginRight: '20px' }}>
          <h3>Files</h3>
          <ul>
            {structure?.tree.map((item, index) => (
              <li key={index}>
                {item.type === 'directory' ? '📁' : '📄'} {item.name}
              </li>
            ))}
          </ul>
        </aside>
        
        {/* ドキュメント内容 */}
        <main style={{ flex: 1 }}>
          <pre style={{ whiteSpace: 'pre-wrap' }}>
            {document?.content.content}
          </pre>
          
          {/* リンク情報 */}
          {document?.links && document.links.length > 0 && (
            <div>
              <h3>Links in document:</h3>
              <ul>
                {document.links.map((link, index) => (
                  <li key={index}>
                    <a href={link.url} target="_blank" rel="noopener noreferrer">
                      {link.text}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default ForgejoDocumentViewer;
```

## 設定とセットアップ

### 1. バックエンドサーバーの起動
```bash
cd doc_ai_helper_backend
python -m uvicorn doc_ai_helper_backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 環境変数の設定
`.env` ファイルに以下を設定：

```bash
# Forgejo server settings
FORGEJO_BASE_URL=https://your-forgejo-server.com
FORGEJO_TOKEN=your_access_token_here

# Alternative: Basic auth (not recommended)
# FORGEJO_USERNAME=your_username
# FORGEJO_PASSWORD=your_password

# SSL settings (for self-signed certificates)
FORGEJO_VERIFY_SSL=False
```

### 3. CORS設定
本番環境では、フロントエンドのオリジンを適切に設定してください：

```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## テスト用スクリプト

### API接続テスト
```bash
python examples/frontend_api_demo.py
```

### curl での動作確認
```bash
# ヘルスチェック
curl http://localhost:8000/health

# リポジトリ構造取得
curl "http://localhost:8000/api/v1/documents/structure/forgejo/myuser/myrepo"

# ドキュメント取得
curl "http://localhost:8000/api/v1/documents/contents/forgejo/myuser/myrepo/README.md"
```

## トラブルシューティング

### よくある問題

1. **404 Not Found**: URLパスが正しいか確認してください（`/api/v1/documents/` がプレフィックス）
2. **500 Internal Server Error**: Forgejoサーバーへの接続設定を確認してください
3. **認証エラー**: アクセストークンが正しく設定されているか確認してください
4. **SSL証明書エラー**: 自己署名証明書の場合は `FORGEJO_VERIFY_SSL=False` を設定

### デバッグ方法

1. ログレベルを DEBUG に設定：
   ```bash
   export LOG_LEVEL=DEBUG
   ```

2. バックエンドのログを確認：
   ```bash
   python -m uvicorn doc_ai_helper_backend.main:app --reload --log-level debug
   ```

3. 接続テストスクリプトを実行：
   ```bash
   python examples/debug_forgejo_connection.py
   ```
