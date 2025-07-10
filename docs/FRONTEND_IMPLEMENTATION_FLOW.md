# Vue.js フロントエンド実装フローチャート

## 1. 全体アーキテクチャ図

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vue Router    │────│  DocumentView   │────│ DocumentViewer  │
│                 │    │     (Page)      │    │  (Container)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                │                       ├─ DocumentHeader
                                │                       ├─ TableOfContents
                                │                       ├─ MarkdownRenderer (既存)
                                │                       └─ HTMLRenderer (新規)
                                │
                        ┌─────────────────┐
                        │  useDocument    │
                        │  (Composable)   │
                        └─────────────────┘
                                │
                        ┌─────────────────┐
                        │ DocumentApiClient│
                        └─────────────────┘
                                │
                        ┌─────────────────┐
                        │   Backend API   │
                        └─────────────────┘
```

## 2. データフロー図

### 2.1 HTMLドキュメント表示フロー

```
[ユーザー]
    │
    │ URLアクセス (/docs/mock/owner/repo/file.html)
    ▼
[Vue Router]
    │
    │ ルートパラメータ解析
    ▼
[DocumentView]
    │
    │ loadDocument() 呼び出し
    ▼
[useDocument Composable]
    │
    │ API呼び出し
    ▼
[DocumentApiClient]
    │
    │ HTTP Request
    ▼
[Backend API] (/api/v1/documents/contents/...)
    │
    │ DocumentResponse 返却
    ▼
[HTMLProcessor (Backend)]
    │
    │ HTML解析・メタデータ抽出・リンク変換
    ▼
[DocumentResponse with HTML metadata]
    │
    │ レスポンス
    ▼
[Vue Frontend]
    │
    │ DocumentViewer に渡す
    ▼
[HTMLRenderer]
    │
    │ DOMPurify でサニタイズ
    ▼
[DOM表示]
```

### 2.2 リンククリック処理フロー

```
[ユーザー]
    │
    │ リンククリック
    ▼
[HTMLRenderer]
    │
    │ preventDefault() & イベント発火
    ▼
[DocumentViewer]
    │
    │ @link-click イベント受信
    ▼
[DocumentView]
    │
    │ 内部リンク判定
    ▼
[Vue Router]
    │
    │ 新しいドキュメントページに遷移
    ▼
[新しいDocumentView]
    │
    │ 新しいドキュメント読み込み
    ▼
[表示更新]
```

### 2.3 Quartoソースファイル表示フロー

```
[HTMLRenderer]
    │
    │ Quartoドキュメントでソースボタンクリック
    ▼
[DocumentViewer]
    │
    │ @source-request イベント発火
    ▼
[DocumentView]
    │
    │ handleSourceRequest()
    ▼
[useDocument]
    │
    │ loadSourceFile() - .qmdファイル取得
    ▼
[Backend API]
    │
    │ Markdownコンテンツ返却
    ▼
[MarkdownRenderer]
    │
    │ Markdownとして表示
    ▼
[表示切り替え完了]
```

## 3. コンポーネント責任分離

### 3.1 コンポーネント階層と責任

```
DocumentView (Page Level)
├── 責任: ルーティング、状態管理、エラーハンドリング
├── 役割: useDocument composable の統合、ナビゲーション制御
│
├─ DocumentViewer (Container Level)
│   ├── 責任: ドキュメントタイプに応じたレンダラー選択
│   ├── 役割: 共通レイアウト、イベントの中継
│   │
│   ├─ DocumentHeader (Presentation Level)
│   │   ├── 責任: ドキュメント情報表示、パンくずナビゲーション
│   │   └── 役割: メタデータの整形表示
│   │
│   ├─ TableOfContents (Presentation Level)
│   │   ├── 責任: 見出し一覧表示、ナビゲーション
│   │   └── 役割: headings 配列からTOC生成
│   │
│   ├─ MarkdownRenderer (Presentation Level) [既存]
│   │   ├── 責任: Markdownのパース・表示
│   │   └── 役割: markdown-it等でHTML変換
│   │
│   └─ HTMLRenderer (Presentation Level) [新規]
│       ├── 責任: HTMLの安全な表示、イベント処理
│       └── 役割: DOMPurifyでサニタイズ、リンク処理
```

### 3.2 状態管理パターン

```
useDocument Composable
├── currentDocument (ref<DocumentResponse | null>)
├── loading (ref<boolean>)
├── error (ref<string | null>)
│
├── isMarkdown (computed)
├── isHTML (computed)
├── isQuarto (computed)
├── documentTitle (computed)
│
├── loadDocument()
├── loadSourceFile()
└── clearDocument()
```

## 4. 実装チェックリスト

### 4.1 フェーズ1: 基本HTML表示

- [ ] `DocumentResponse` 型定義作成
- [ ] `HTMLRenderer` コンポーネント実装
- [ ] `DOMPurify` 統合
- [ ] 基本HTMLサニタイゼーション
- [ ] `DocumentViewer` への統合
- [ ] 基本表示テスト

### 4.2 フェーズ2: メタデータ活用

- [ ] `DocumentHeader` コンポーネント拡張
- [ ] HTMLメタデータ表示機能
- [ ] 見出し構造解析
- [ ] `TableOfContents` HTML対応
- [ ] パンくずナビゲーション

### 4.3 フェーズ3: インタラクション

- [ ] リンククリック処理
- [ ] SPAナビゲーション統合
- [ ] 外部リンク処理
- [ ] アンカーリンク処理
- [ ] `DocumentApiClient` 実装

### 4.4 フェーズ4: Quarto対応

- [ ] Quartoドキュメント判定
- [ ] ソースファイル表示機能
- [ ] ソース⇔HTML切り替え
- [ ] メタデータ拡張表示
- [ ] ビルド情報表示

### 4.5 フェーズ5: 最適化・テスト

- [ ] パフォーマンス最適化
- [ ] キャッシュ機能
- [ ] エラーハンドリング強化
- [ ] ユニットテスト作成
- [ ] E2Eテスト作成

## 5. セキュリティチェックリスト

### 5.1 XSS対策

- [ ] DOMPurify設定確認
- [ ] 許可タグ・属性の制限
- [ ] イベントハンドラー禁止
- [ ] 外部スクリプト読み込み禁止
- [ ] CSP設定

### 5.2 外部リソース対策

- [ ] 画像読み込み制限
- [ ] 外部リンク新しいタブ開き
- [ ] `rel="noopener noreferrer"` 設定
- [ ] プロトコル制限 (https, mailto等)

### 5.3 インジェクション対策

- [ ] URL パラメータ検証
- [ ] パス・トラバーサル対策
- [ ] SQLインジェクション対策 (Backend)
- [ ] ファイルアップロード制限

## 6. パフォーマンス最適化チェックリスト

### 6.1 コンポーネント最適化

- [ ] 遅延読み込み (`defineAsyncComponent`)
- [ ] メモ化 (`computed`, `watch`)
- [ ] 不要な再レンダリング回避
- [ ] v-if vs v-show 適切な使用

### 6.2 ネットワーク最適化

- [ ] ドキュメントキャッシュ
- [ ] APIリクエスト重複回避
- [ ] プリフェッチ機能
- [ ] 画像遅延読み込み

### 6.3 メモリ最適化

- [ ] イベントリスナークリーンアップ
- [ ] 大きなドキュメント処理最適化
- [ ] キャッシュサイズ制限
- [ ] ガベージコレクション配慮

## 7. テスト戦略

### 7.1 ユニットテスト

```
HTMLRenderer
├── HTML表示テスト
├── サニタイゼーションテスト
├── リンクイベントテスト
├── Quartoメタデータ表示テスト
└── エラーハンドリングテスト

DocumentViewer
├── ドキュメントタイプ判定テスト
├── コンポーネント切り替えテスト
├── イベント伝播テスト
└── エラー状態テスト

useDocument
├── API呼び出しテスト
├── 状態管理テスト
├── エラーハンドリングテスト
└── キャッシュテスト
```

### 7.2 統合テスト

```
ドキュメント表示フロー
├── Markdown → HTML 切り替え
├── HTML → Quarto ソース 切り替え
├── リンクナビゲーション
└── エラー回復

APIクライアント
├── 正常系レスポンス処理
├── エラー系レスポンス処理
├── ネットワークエラー処理
└── タイムアウト処理
```

### 7.3 E2Eテスト

```
ユーザーシナリオ
├── HTMLドキュメント閲覧
├── Quartoドキュメント閲覧
├── ソースファイル表示
├── リンクナビゲーション
├── 目次使用
└── パンくずナビゲーション
```
