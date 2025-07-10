# Vue.js HTML統合 - 実装時の注意点とベストプラクティス

## 🚨 重要な注意点

### 1. セキュリティ第一原則

#### XSS攻撃対策

```typescript
// ❌ 危険: 生のHTMLを直接表示
const dangerousHTML = `<script>alert('XSS')</script>`;
element.innerHTML = dangerousHTML;

// ✅ 安全: DOMPurifyでサニタイズ
import DOMPurify from 'dompurify';
const safeHTML = DOMPurify.sanitize(dangerousHTML, {
  ALLOWED_TAGS: ['h1', 'h2', 'p', 'a', 'img'],
  ALLOWED_ATTR: ['href', 'src', 'alt', 'class', 'id'],
  FORBID_TAGS: ['script', 'style', 'iframe'],
  FORBID_ATTR: ['onload', 'onerror', 'onclick']
});
```

#### 設定ファイルでのサニタイゼーション設定

```typescript
// config/domPurify.ts
export const HTML_SANITIZE_CONFIG = {
  // 許可するHTMLタグ
  ALLOWED_TAGS: [
    // 見出し
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    // テキスト
    'p', 'div', 'span', 'section', 'article',
    // リンクと画像
    'a', 'img', 'figure', 'figcaption',
    // リスト
    'ul', 'ol', 'li', 'dl', 'dt', 'dd',
    // テーブル
    'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td',
    // コード
    'pre', 'code', 'blockquote',
    // 強調
    'strong', 'em', 'b', 'i', 'u', 'mark',
    // その他
    'br', 'hr'
  ],
  
  // 許可する属性
  ALLOWED_ATTR: [
    'href', 'src', 'alt', 'title',
    'class', 'id', 'data-*',
    'target', 'rel',
    'width', 'height'
  ],
  
  // 許可するURL形式
  ALLOWED_URI_REGEXP: /^(?:(?:https?|ftp):\/\/|mailto:|tel:|#|\/)/i,
  
  // 禁止するタグ
  FORBID_TAGS: ['script', 'style', 'iframe', 'object', 'embed', 'form', 'input'],
  
  // 禁止する属性（イベントハンドラー等）
  FORBID_ATTR: ['onload', 'onerror', 'onclick', 'onmouseover', 'onfocus']
};
```

### 2. パフォーマンス考慮事項

#### 大きなHTMLドキュメントの処理

```vue
<!-- ❌ 全てのHTMLを一度に表示 -->
<div v-html="largeHTMLContent"></div>

<!-- ✅ 仮想スクロールまたは分割表示 -->
<template>
  <div class="document-container">
    <!-- 可視部分のみレンダリング -->
    <VirtualScroller
      :items="documentSections"
      :item-height="200"
      v-slot="{ item }"
    >
      <div v-html="sanitize(item.content)"></div>
    </VirtualScroller>
  </div>
</template>
```

#### メモリリーク防止

```typescript
// HTMLRenderer.vue
import { onBeforeUnmount } from 'vue';

export default {
  setup() {
    const eventListeners: (() => void)[] = [];
    
    const setupEventListeners = () => {
      const links = container.value?.querySelectorAll('a');
      links?.forEach(link => {
        const handler = (e: Event) => handleLinkClick(e);
        link.addEventListener('click', handler);
        
        // クリーンアップ関数を保存
        eventListeners.push(() => {
          link.removeEventListener('click', handler);
        });
      });
    };
    
    // コンポーネント破棄時にクリーンアップ
    onBeforeUnmount(() => {
      eventListeners.forEach(cleanup => cleanup());
    });
    
    return { setupEventListeners };
  }
};
```

### 3. 型安全性の確保

#### 厳密な型定義

```typescript
// types/document.ts

// バックエンドレスポンスの完全な型定義
export interface DocumentResponse {
  readonly path: string;
  readonly name: string;
  readonly type: DocumentType;
  readonly content: DocumentContent;
  readonly metadata: DocumentMetadata;
  readonly repository: string;
  readonly owner: string;
  readonly service: string;
  readonly ref: string;
  readonly links?: readonly LinkInfo[];
  readonly transformed_content?: string;
}

// HTMLメタデータの詳細型定義
export interface HTMLMetadata {
  readonly title?: string;
  readonly description?: string;
  readonly author?: string;
  readonly generator?: string;
  readonly source_file?: string;
  readonly build_info?: Readonly<Record<string, any>>;
  readonly headings: readonly Array<{
    readonly level: number;
    readonly text: string;
    readonly id?: string;
    readonly tag: string;
  }>;
  readonly lang?: string;
  readonly charset?: string;
}

// 型ガード関数
export function isHTMLDocument(doc: DocumentResponse): doc is DocumentResponse & {
  type: 'html';
  metadata: DocumentMetadata & {
    extra: { html: HTMLMetadata };
  };
} {
  return doc.type === 'html' && doc.metadata.extra?.html !== undefined;
}

export function isQuartoDocument(doc: DocumentResponse): boolean {
  return isHTMLDocument(doc) && doc.metadata.extra.html.generator === 'Quarto';
}
```

### 4. エラーハンドリングパターン

#### 階層的エラーハンドリング

```typescript
// composables/useDocument.ts
export function useDocument() {
  const error = ref<DocumentError | null>(null);
  
  // 詳細なエラー情報
  interface DocumentError {
    type: 'network' | 'parse' | 'permission' | 'not_found';
    message: string;
    details?: Record<string, any>;
    retryable: boolean;
  }
  
  const loadDocument = async (...args) => {
    try {
      // API呼び出し
    } catch (err) {
      if (err instanceof TypeError) {
        error.value = {
          type: 'network',
          message: 'ネットワークエラーが発生しました',
          retryable: true
        };
      } else if (err.status === 404) {
        error.value = {
          type: 'not_found',
          message: 'ドキュメントが見つかりません',
          retryable: false
        };
      } else {
        error.value = {
          type: 'parse',
          message: 'ドキュメントの解析に失敗しました',
          details: { originalError: err.message },
          retryable: true
        };
      }
      throw error.value;
    }
  };
  
  return { error: readonly(error), loadDocument };
}
```

#### 段階的フォールバック

```vue
<!-- DocumentViewer.vue -->
<template>
  <div class="document-viewer">
    <!-- 最適な表示方法を試行 -->
    <HTMLRenderer
      v-if="canRenderHTML"
      :document="document"
      @error="handleHTMLError"
    />
    
    <!-- HTMLレンダリング失敗時はプレーンテキスト -->
    <PlainTextRenderer
      v-else-if="canRenderPlainText"
      :content="document.content.content"
    />
    
    <!-- 全て失敗時はエラー表示 -->
    <ErrorDisplay
      v-else
      :error="renderError"
      @retry="retryRender"
    />
  </div>
</template>

<script setup lang="ts">
const canRenderHTML = ref(true);
const canRenderPlainText = ref(true);
const renderError = ref<Error | null>(null);

const handleHTMLError = (error: Error) => {
  console.warn('HTML rendering failed, falling back to plain text:', error);
  canRenderHTML.value = false;
  
  if (!canRenderPlainText.value) {
    renderError.value = error;
  }
};
</script>
```

## 🎯 ベストプラクティス

### 1. コンポーネント設計原則

#### 単一責任原則の徹底

```vue
<!-- ❌ 責任が混在している例 -->
<template>
  <div>
    <!-- API呼び出し、データ変換、表示が混在 -->
  </div>
</template>

<!-- ✅ 責任を分離した例 -->

<!-- DocumentView.vue (データ取得・状態管理) -->
<template>
  <DocumentViewer
    :document="document"
    @link-click="handleNavigation"
  />
</template>

<!-- DocumentViewer.vue (表示制御) -->
<template>
  <div class="document-viewer">
    <DocumentHeader :info="documentInfo" />
    <HTMLRenderer
      v-if="isHTML"
      :document="document"
      @link-click="$emit('linkClick', $event)"
    />
  </div>
</template>

<!-- HTMLRenderer.vue (HTML表示専用) -->
<template>
  <div class="html-content" v-html="sanitizedContent" />
</template>
```

#### Props と Emits の明確な定義

```typescript
// HTMLRenderer.vue
interface Props {
  // 必須プロパティ
  readonly document: DocumentResponse;
  readonly baseUrl: string;
  
  // オプションプロパティ
  readonly showMetadata?: boolean;
  readonly enableNavigation?: boolean;
  readonly customSanitizeConfig?: DOMPurifyConfig;
}

interface Emits {
  // イベント名と引数の型を明確に定義
  linkClick: [url: string, external: boolean];
  sourceRequest: [sourceFile: string];
  metadataUpdate: [metadata: HTMLMetadata];
  renderError: [error: Error];
}

const props = withDefaults(defineProps<Props>(), {
  showMetadata: true,
  enableNavigation: true
});

const emit = defineEmits<Emits>();
```

### 2. 状態管理パターン

#### Composable による状態の分離

```typescript
// composables/useDocumentNavigation.ts
export function useDocumentNavigation() {
  const router = useRouter();
  const route = useRoute();
  
  const navigateToDocument = (path: string, external = false) => {
    if (external) {
      window.open(path, '_blank', 'noopener,noreferrer');
      return;
    }
    
    // 同一リポジトリ内ナビゲーション
    router.push({
      name: 'Document',
      params: {
        ...route.params,
        path
      }
    });
  };
  
  return { navigateToDocument };
}

// composables/useDocumentMeta.ts
export function useDocumentMeta(document: Ref<DocumentResponse>) {
  const documentTitle = computed(() => {
    const htmlMeta = document.value?.metadata.extra?.html;
    return htmlMeta?.title || document.value?.name || 'ドキュメント';
  });
  
  // ページタイトルの自動更新
  watchEffect(() => {
    document.title = documentTitle.value;
  });
  
  // メタタグの更新
  const updateMetaTags = () => {
    const htmlMeta = document.value?.metadata.extra?.html;
    if (htmlMeta?.description) {
      updateMetaTag('description', htmlMeta.description);
    }
    if (htmlMeta?.author) {
      updateMetaTag('author', htmlMeta.author);
    }
  };
  
  return { documentTitle, updateMetaTags };
}
```

### 3. パフォーマンス最適化

#### 適切な反応性の使用

```typescript
// ❌ 不要な反応性
const processedContent = ref('');
watch(document, () => {
  processedContent.value = processContent(document.value);
});

// ✅ 計算プロパティの使用
const processedContent = computed(() => {
  return document.value ? processContent(document.value) : '';
});

// ❌ 過度な反応性
const expensiveComputation = computed(() => {
  return heavyProcessing(document.value); // 毎回実行される
});

// ✅ メモ化の活用
const expensiveComputation = computed(() => {
  const key = `${document.value?.path}-${document.value?.metadata.last_modified}`;
  return memoizedHeavyProcessing(key, document.value);
});
```

#### 遅延読み込みの実装

```typescript
// レイジーロード用のコンポーネント
const LazyHTMLRenderer = defineAsyncComponent({
  loader: () => import('./HTMLRenderer.vue'),
  loadingComponent: LoadingSpinner,
  errorComponent: ErrorDisplay,
  delay: 200,
  timeout: 10000
});

// 画像の遅延読み込み
export function useLazyImages(container: Ref<HTMLElement | undefined>) {
  const setupLazyLoading = () => {
    if (!container.value) return;
    
    const images = container.value.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target as HTMLImageElement;
          img.src = img.dataset.src!;
          img.removeAttribute('data-src');
          imageObserver.unobserve(img);
        }
      });
    });
    
    images.forEach(img => imageObserver.observe(img));
  };
  
  return { setupLazyLoading };
}
```

### 4. テストしやすい設計

#### 依存関係の注入

```typescript
// services/documentApi.ts
export interface DocumentApiInterface {
  getDocument(service: string, owner: string, repo: string, path: string): Promise<DocumentResponse>;
}

export class DocumentApiClient implements DocumentApiInterface {
  constructor(
    private baseUrl: string,
    private httpClient: HttpClientInterface = new FetchHttpClient()
  ) {}
  
  async getDocument(...args) {
    return this.httpClient.get(/* ... */);
  }
}

// テスト用のモック
export class MockDocumentApiClient implements DocumentApiInterface {
  constructor(private mockData: Record<string, DocumentResponse>) {}
  
  async getDocument(service: string, owner: string, repo: string, path: string) {
    const key = `${service}/${owner}/${repo}/${path}`;
    return this.mockData[key] || Promise.reject(new Error('Not found'));
  }
}
```

#### テスタブルなComposable

```typescript
// composables/useDocument.ts
export function useDocument(
  apiClient: DocumentApiInterface = documentApi
) {
  const currentDocument = ref<DocumentResponse | null>(null);
  
  const loadDocument = async (...args) => {
    currentDocument.value = await apiClient.getDocument(...args);
  };
  
  return { currentDocument, loadDocument };
}

// テストでの使用
import { useDocument } from '@/composables/useDocument';
import { MockDocumentApiClient } from '@/services/documentApi';

test('ドキュメント読み込みテスト', async () => {
  const mockApi = new MockDocumentApiClient({
    'mock/owner/repo/test.html': mockHTMLDocument
  });
  
  const { currentDocument, loadDocument } = useDocument(mockApi);
  
  await loadDocument('mock', 'owner', 'repo', 'test.html');
  
  expect(currentDocument.value).toEqual(mockHTMLDocument);
});
```

### 5. アクセシビリティ対応

#### セマンティックなHTML構造

```vue
<!-- ✅ アクセシブルなドキュメント構造 -->
<template>
  <article class="document-view" role="main">
    <header class="document-header">
      <nav aria-label="パンくず" class="breadcrumbs">
        <ol class="breadcrumb-list">
          <!-- パンくずナビゲーション -->
        </ol>
      </nav>
      
      <h1 class="document-title">{{ documentTitle }}</h1>
    </header>
    
    <aside v-if="showTOC" class="table-of-contents" aria-label="目次">
      <nav>
        <h2>目次</h2>
        <ul>
          <li v-for="heading in headings" :key="heading.anchor">
            <a :href="`#${heading.anchor}`" :aria-level="heading.level">
              {{ heading.text }}
            </a>
          </li>
        </ul>
      </nav>
    </aside>
    
    <main class="document-content">
      <HTMLRenderer
        :document="document"
        @link-click="handleLinkClick"
        aria-live="polite"
      />
    </main>
  </article>
</template>
```

#### キーボードナビゲーション

```typescript
// HTMLRenderer.vue
const setupKeyboardNavigation = () => {
  document.addEventListener('keydown', (event) => {
    // Skip link navigation (見出し間ジャンプ)
    if (event.key === 'n' && event.altKey) {
      event.preventDefault();
      jumpToNextHeading();
    }
    
    if (event.key === 'p' && event.altKey) {
      event.preventDefault();
      jumpToPreviousHeading();
    }
    
    // 目次表示切り替え
    if (event.key === 't' && event.altKey) {
      event.preventDefault();
      toggleTableOfContents();
    }
  });
};
```

### 6. 国際化対応

#### i18n 対応の実装

```typescript
// locales/ja.json
{
  "document": {
    "loading": "ドキュメントを読み込み中...",
    "error": "エラーが発生しました",
    "notFound": "ドキュメントが見つかりません",
    "generatedBy": "{generator}によって生成",
    "lastModified": "最終更新: {date}",
    "showSource": "ソースを表示",
    "tableOfContents": "目次"
  }
}

// locales/en.json
{
  "document": {
    "loading": "Loading document...",
    "error": "An error occurred",
    "notFound": "Document not found",
    "generatedBy": "Generated by {generator}",
    "lastModified": "Last modified: {date}",
    "showSource": "Show Source",
    "tableOfContents": "Table of Contents"
  }
}
```

```vue
<!-- HTMLRenderer.vue -->
<template>
  <div class="html-renderer">
    <div v-if="isQuarto" class="quarto-info">
      <button @click="requestSource" class="source-button">
        {{ $t('document.showSource') }} ({{ sourceFile }})
      </button>
    </div>
    
    <div class="html-content" v-html="sanitizedContent" />
  </div>
</template>
```

これらの注意点とベストプラクティスを守ることで、安全で保守性が高く、パフォーマンスの良いVue.jsアプリケーションを構築できます。
