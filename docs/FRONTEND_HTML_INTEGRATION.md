# Vue.js フロントエンド HTML統合実装指示書

## 概要

既存のMarkdownドキュメントビューワーを拡張し、バックエンドから直接HTMLドキュメントを受け取って表示する機能の実装指示書です。

## 前提条件

- Vue.js フロントエンドアプリケーション
- 既存のMarkdownビューワーコンポーネント
- Markdownパーサー（markdown-it等）が実装済み
- ドキュメント表示用のコンポーネント構造が確立

## 1. バックエンドAPIレスポンス仕様

### DocumentResponse 構造

```typescript
interface DocumentResponse {
  path: string;
  name: string;
  type: 'markdown' | 'html' | 'quarto' | 'other';
  content: {
    content: string;
    encoding: string;
  };
  metadata: {
    size: number;
    last_modified: string;
    content_type: string;
    sha?: string;
    download_url?: string;
    html_url?: string;
    raw_url?: string;
    extra?: {
      html?: HTMLMetadata;
    };
  };
  repository: string;
  owner: string;
  service: string;
  ref: string;
  links?: LinkInfo[];
  transformed_content?: string;
}

interface HTMLMetadata {
  title?: string;
  description?: string;
  author?: string;
  generator?: string;
  source_file?: string;
  build_info?: Record<string, any>;
  headings: Array<{
    level: number;
    text: string;
    id?: string;
    tag: string;
  }>;
  lang?: string;
  charset?: string;
}

interface LinkInfo {
  text: string;
  url: string;
  is_image: boolean;
  position: [number, number];
  is_external: boolean;
}
```

## 2. Vue.js コンポーネント実装

### 2.1 共通型定義ファイル

```typescript
// types/document.ts
export interface DocumentResponse {
  // 上記の型定義をここに配置
}

export interface HTMLMetadata {
  // 上記の型定義をここに配置
}

export interface LinkInfo {
  // 上記の型定義をここに配置
}

export interface DocumentDisplayInfo {
  title: string;
  author?: string;
  lastModified: string;
  generator?: string;
  sourceFile?: string;
  size: number;
  language?: string;
  headings: Array<{
    level: number;
    text: string;
    anchor: string;
  }>;
}
```

### 2.2 ドキュメントビューワーコンポーネント拡張

```vue
<!-- components/DocumentViewer.vue -->
<template>
  <div class="document-viewer">
    <!-- ドキュメント情報ヘッダー -->
    <DocumentHeader 
      :document-info="documentInfo"
      :breadcrumbs="breadcrumbs"
    />
    
    <!-- 目次（オプション） -->
    <TableOfContents 
      v-if="showTOC && documentInfo.headings.length > 0"
      :headings="documentInfo.headings"
      @navigate="scrollToHeading"
    />
    
    <!-- メインコンテンツエリア -->
    <div class="document-content">
      <!-- Markdownコンテンツ（既存） -->
      <MarkdownRenderer 
        v-if="document.type === 'markdown'"
        :content="document.content.content"
        :base-url="baseUrl"
        @link-click="handleLinkClick"
      />
      
      <!-- HTMLコンテンツ（新規） -->
      <HTMLRenderer
        v-else-if="document.type === 'html'"
        :document="document"
        :base-url="baseUrl"
        @link-click="handleLinkClick"
        @source-request="handleSourceRequest"
      />
      
      <!-- その他のタイプ -->
      <div v-else class="unsupported-type">
        <p>サポートされていないドキュメントタイプ: {{ document.type }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import type { DocumentResponse, DocumentDisplayInfo } from '@/types/document';
import DocumentHeader from './DocumentHeader.vue';
import TableOfContents from './TableOfContents.vue';
import MarkdownRenderer from './MarkdownRenderer.vue';
import HTMLRenderer from './HTMLRenderer.vue';

interface Props {
  document: DocumentResponse;
  showTOC?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  showTOC: true
});

const emit = defineEmits<{
  linkClick: [url: string, external: boolean];
  sourceRequest: [sourceFile: string];
}>();

// 計算されたプロパティ
const documentInfo = computed((): DocumentDisplayInfo => {
  const htmlMeta = props.document.metadata.extra?.html;
  
  return {
    title: htmlMeta?.title || props.document.name,
    author: htmlMeta?.author,
    lastModified: props.document.metadata.last_modified,
    generator: htmlMeta?.generator,
    sourceFile: htmlMeta?.source_file,
    size: props.document.metadata.size,
    language: htmlMeta?.lang,
    headings: (htmlMeta?.headings || []).map(heading => ({
      level: heading.level,
      text: heading.text,
      anchor: heading.id || slugify(heading.text)
    }))
  };
});

const breadcrumbs = computed(() => {
  const pathParts = props.document.path.split('/');
  return pathParts.map((part, index) => ({
    text: part,
    path: pathParts.slice(0, index + 1).join('/'),
    isLast: index === pathParts.length - 1
  }));
});

const baseUrl = computed(() => {
  return `https://api.example.com/${props.document.service}/${props.document.owner}/${props.document.repository}/raw/${props.document.ref}`;
});

// イベントハンドラー
const handleLinkClick = (url: string, external: boolean) => {
  emit('linkClick', url, external);
};

const handleSourceRequest = (sourceFile: string) => {
  emit('sourceRequest', sourceFile);
};

const scrollToHeading = (anchor: string) => {
  const element = document.getElementById(anchor);
  if (element) {
    element.scrollIntoView({ behavior: 'smooth' });
  }
};

// ユーティリティ関数
const slugify = (text: string): string => {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
};
</script>
```

### 2.3 HTMLレンダラーコンポーネント（新規作成）

```vue
<!-- components/HTMLRenderer.vue -->
<template>
  <div class="html-renderer">
    <!-- Quartoソースファイル情報 -->
    <div v-if="isQuartoDocument" class="quarto-info">
      <div class="source-info">
        <Icon name="quarto" />
        <span>Quarto文書</span>
        <button 
          v-if="sourceFile" 
          @click="requestSource"
          class="source-button"
        >
          ソースを表示 ({{ sourceFile }})
        </button>
      </div>
    </div>
    
    <!-- HTMLコンテンツ -->
    <div 
      ref="contentContainer"
      class="html-content"
      v-html="sanitizedContent"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue';
import DOMPurify from 'dompurify';
import type { DocumentResponse } from '@/types/document';

interface Props {
  document: DocumentResponse;
  baseUrl: string;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  linkClick: [url: string, external: boolean];
  sourceRequest: [sourceFile: string];
}>();

const contentContainer = ref<HTMLElement>();

// 計算されたプロパティ
const htmlMetadata = computed(() => props.document.metadata.extra?.html);

const isQuartoDocument = computed(() => 
  htmlMetadata.value?.generator === 'Quarto'
);

const sourceFile = computed(() => htmlMetadata.value?.source_file);

const sanitizedContent = computed(() => {
  const content = props.document.transformed_content || props.document.content.content;
  
  return DOMPurify.sanitize(content, {
    ALLOWED_TAGS: [
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'p', 'div', 'span', 'section', 'article',
      'a', 'img', 'figure', 'figcaption',
      'ul', 'ol', 'li', 'dl', 'dt', 'dd',
      'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td',
      'pre', 'code', 'blockquote',
      'strong', 'em', 'b', 'i', 'u', 'mark',
      'br', 'hr'
    ],
    ALLOWED_ATTR: [
      'href', 'src', 'alt', 'title',
      'class', 'id', 'data-*',
      'target', 'rel',
      'width', 'height',
      'style' // 制限付きで許可
    ],
    ALLOWED_URI_REGEXP: /^(?:(?:https?|ftp):\/\/|mailto:|tel:|#|\/)/i,
    FORBID_TAGS: ['script', 'style', 'iframe', 'object', 'embed'],
    FORBID_ATTR: ['onload', 'onerror', 'onclick'] // イベントハンドラー禁止
  });
});

// メソッド
const requestSource = () => {
  if (sourceFile.value) {
    emit('sourceRequest', sourceFile.value);
  }
};

const setupEventListeners = () => {
  if (!contentContainer.value) return;
  
  // リンククリックの処理
  const links = contentContainer.value.querySelectorAll('a[href]');
  links.forEach(link => {
    link.addEventListener('click', handleLinkClick);
  });
  
  // 見出しにIDを追加（目次リンク用）
  const headings = contentContainer.value.querySelectorAll('h1, h2, h3, h4, h5, h6');
  headings.forEach(heading => {
    if (!heading.id) {
      heading.id = slugify(heading.textContent || '');
    }
  });
};

const handleLinkClick = (event: Event) => {
  const target = event.target as HTMLAnchorElement;
  const href = target.getAttribute('href');
  
  if (!href) return;
  
  // 外部リンクの判定
  const isExternal = /^https?:\/\//.test(href) || href.startsWith('mailto:');
  
  // アンカーリンクの場合は通常の動作を許可
  if (href.startsWith('#')) {
    return;
  }
  
  // SPAナビゲーション用のイベント発火
  if (!isExternal) {
    event.preventDefault();
    emit('linkClick', href, false);
  } else {
    // 外部リンクの場合は新しいタブで開く
    event.preventDefault();
    window.open(href, '_blank', 'noopener,noreferrer');
    emit('linkClick', href, true);
  }
};

const slugify = (text: string): string => {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
};

// ライフサイクル
onMounted(async () => {
  await nextTick();
  setupEventListeners();
});
</script>

<style scoped>
.html-renderer {
  width: 100%;
}

.quarto-info {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.source-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.source-button {
  background: #0d6efd;
  color: white;
  border: none;
  padding: 0.25rem 0.75rem;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 0.875rem;
}

.source-button:hover {
  background: #0b5ed7;
}

.html-content {
  /* 既存のMarkdownスタイルを継承 */
  line-height: 1.6;
  color: var(--text-color);
}

/* HTMLコンテンツ用のスタイル調整 */
.html-content :deep(h1),
.html-content :deep(h2),
.html-content :deep(h3),
.html-content :deep(h4),
.html-content :deep(h5),
.html-content :deep(h6) {
  margin-top: 2rem;
  margin-bottom: 1rem;
  font-weight: 600;
  line-height: 1.25;
  color: var(--heading-color);
}

.html-content :deep(h1) { font-size: 2.25rem; }
.html-content :deep(h2) { font-size: 1.875rem; }
.html-content :deep(h3) { font-size: 1.5rem; }
.html-content :deep(h4) { font-size: 1.25rem; }
.html-content :deep(h5) { font-size: 1.125rem; }
.html-content :deep(h6) { font-size: 1rem; }

.html-content :deep(p) {
  margin-bottom: 1rem;
}

.html-content :deep(a) {
  color: var(--link-color);
  text-decoration: none;
}

.html-content :deep(a:hover) {
  color: var(--link-hover-color);
  text-decoration: underline;
}

.html-content :deep(pre) {
  background: var(--code-bg);
  border-radius: 0.375rem;
  padding: 1rem;
  overflow-x: auto;
  margin: 1rem 0;
}

.html-content :deep(code) {
  background: var(--inline-code-bg);
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-size: 0.875em;
}

.html-content :deep(pre code) {
  background: transparent;
  padding: 0;
}

.html-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 0.375rem;
  margin: 1rem 0;
}

.html-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
}

.html-content :deep(th),
.html-content :deep(td) {
  border: 1px solid var(--border-color);
  padding: 0.5rem;
  text-align: left;
}

.html-content :deep(th) {
  background: var(--table-header-bg);
  font-weight: 600;
}
</style>
```

### 2.4 ドキュメントヘッダーコンポーネント

```vue
<!-- components/DocumentHeader.vue -->
<template>
  <div class="document-header">
    <!-- パンくずナビゲーション -->
    <nav class="breadcrumbs" aria-label="パンくずナビゲーション">
      <ol class="breadcrumb-list">
        <li v-for="(crumb, index) in breadcrumbs" :key="index" class="breadcrumb-item">
          <button 
            v-if="!crumb.isLast"
            @click="navigateTo(crumb.path)"
            class="breadcrumb-link"
          >
            {{ crumb.text }}
          </button>
          <span v-else class="breadcrumb-current">{{ crumb.text }}</span>
          <span v-if="!crumb.isLast" class="breadcrumb-separator">/</span>
        </li>
      </ol>
    </nav>
    
    <!-- ドキュメント情報 -->
    <div class="document-info">
      <h1 class="document-title">{{ documentInfo.title }}</h1>
      
      <div class="document-meta">
        <div v-if="documentInfo.author" class="meta-item">
          <Icon name="user" />
          <span>{{ documentInfo.author }}</span>
        </div>
        
        <div class="meta-item">
          <Icon name="calendar" />
          <time :datetime="documentInfo.lastModified">
            {{ formatDate(documentInfo.lastModified) }}
          </time>
        </div>
        
        <div v-if="documentInfo.generator" class="meta-item">
          <Icon name="tool" />
          <span>{{ documentInfo.generator }}</span>
        </div>
        
        <div class="meta-item">
          <Icon name="file" />
          <span>{{ formatFileSize(documentInfo.size) }}</span>
        </div>
        
        <div v-if="documentInfo.language" class="meta-item">
          <Icon name="globe" />
          <span>{{ documentInfo.language }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { DocumentDisplayInfo } from '@/types/document';

interface Props {
  documentInfo: DocumentDisplayInfo;
  breadcrumbs: Array<{
    text: string;
    path: string;
    isLast: boolean;
  }>;
}

defineProps<Props>();

const emit = defineEmits<{
  navigate: [path: string];
}>();

const navigateTo = (path: string) => {
  emit('navigate', path);
};

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: 'long', 
    day: 'numeric'
  });
};

const formatFileSize = (bytes: number): string => {
  const sizes = ['B', 'KB', 'MB', 'GB'];
  if (bytes === 0) return '0 B';
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
};
</script>

<style scoped>
.document-header {
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 1.5rem;
  margin-bottom: 2rem;
}

.breadcrumbs {
  margin-bottom: 1rem;
}

.breadcrumb-list {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  list-style: none;
  margin: 0;
  padding: 0;
  gap: 0.25rem;
}

.breadcrumb-item {
  display: flex;
  align-items: center;
}

.breadcrumb-link {
  background: none;
  border: none;
  color: var(--link-color);
  cursor: pointer;
  font-size: 0.875rem;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
}

.breadcrumb-link:hover {
  background: var(--hover-bg);
  color: var(--link-hover-color);
}

.breadcrumb-current {
  color: var(--text-muted);
  font-size: 0.875rem;
  padding: 0.25rem 0.5rem;
}

.breadcrumb-separator {
  color: var(--text-muted);
  margin: 0 0.25rem;
}

.document-title {
  font-size: 2.25rem;
  font-weight: 700;
  margin: 0 0 1rem 0;
  color: var(--heading-color);
  line-height: 1.2;
}

.document-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  color: var(--text-muted);
  font-size: 0.875rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

@media (max-width: 768px) {
  .document-title {
    font-size: 1.75rem;
  }
  
  .document-meta {
    flex-direction: column;
    gap: 0.5rem;
  }
}
</style>
```

## 3. APIクライアント実装

### 3.1 ドキュメントAPIクライント

```typescript
// services/documentApi.ts
import type { DocumentResponse } from '@/types/document';

export class DocumentApiClient {
  private baseUrl: string;
  
  constructor(baseUrl: string = '/api/v1') {
    this.baseUrl = baseUrl;
  }
  
  async getDocument(
    service: string,
    owner: string,
    repo: string,
    path: string,
    options: {
      ref?: string;
      transformLinks?: boolean;
      baseUrl?: string;
    } = {}
  ): Promise<DocumentResponse> {
    const {
      ref = 'main',
      transformLinks = true,
      baseUrl: linkBaseUrl
    } = options;
    
    const url = new URL(
      `${this.baseUrl}/documents/contents/${service}/${owner}/${repo}/${path}`,
      window.location.origin
    );
    
    // クエリパラメータを設定
    url.searchParams.set('ref', ref);
    url.searchParams.set('transform_links', transformLinks.toString());
    if (linkBaseUrl) {
      url.searchParams.set('base_url', linkBaseUrl);
    }
    
    const response = await fetch(url.toString());
    
    if (!response.ok) {
      throw new Error(`Failed to fetch document: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  }
  
  async getRepositoryStructure(
    service: string,
    owner: string,
    repo: string,
    options: {
      ref?: string;
      path?: string;
    } = {}
  ) {
    const { ref = 'main', path = '' } = options;
    
    const url = new URL(
      `${this.baseUrl}/documents/structure/${service}/${owner}/${repo}`,
      window.location.origin
    );
    
    url.searchParams.set('ref', ref);
    if (path) {
      url.searchParams.set('path', path);
    }
    
    const response = await fetch(url.toString());
    
    if (!response.ok) {
      throw new Error(`Failed to fetch repository structure: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  }
}

// シングルトンインスタンス
export const documentApi = new DocumentApiClient();
```

## 4. Vue Composable (状態管理)

### 4.1 ドキュメント状態管理Composable

```typescript
// composables/useDocument.ts
import { ref, computed } from 'vue';
import type { DocumentResponse } from '@/types/document';
import { documentApi } from '@/services/documentApi';

export function useDocument() {
  const currentDocument = ref<DocumentResponse | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  
  // 計算されたプロパティ
  const isMarkdown = computed(() => 
    currentDocument.value?.type === 'markdown'
  );
  
  const isHTML = computed(() => 
    currentDocument.value?.type === 'html'
  );
  
  const isQuarto = computed(() => 
    currentDocument.value?.metadata.extra?.html?.generator === 'Quarto'
  );
  
  const documentTitle = computed(() => {
    if (!currentDocument.value) return '';
    
    const htmlMeta = currentDocument.value.metadata.extra?.html;
    return htmlMeta?.title || currentDocument.value.name;
  });
  
  // メソッド
  const loadDocument = async (
    service: string,
    owner: string,
    repo: string,
    path: string,
    options: {
      ref?: string;
      transformLinks?: boolean;
      baseUrl?: string;
    } = {}
  ) => {
    loading.value = true;
    error.value = null;
    
    try {
      const document = await documentApi.getDocument(
        service, owner, repo, path, options
      );
      currentDocument.value = document;
      
      // ページタイトルを更新
      if (document.metadata.extra?.html?.title) {
        document.title = document.metadata.extra.html.title;
      }
      
      return document;
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error';
      throw err;
    } finally {
      loading.value = false;
    }
  };
  
  const loadSourceFile = async (sourceFile: string) => {
    if (!currentDocument.value) {
      throw new Error('No current document loaded');
    }
    
    const { service, owner, repository, ref } = currentDocument.value;
    
    return loadDocument(
      service,
      owner,
      repository,
      sourceFile,
      { ref }
    );
  };
  
  const clearDocument = () => {
    currentDocument.value = null;
    error.value = null;
  };
  
  return {
    // 状態
    currentDocument: readonly(currentDocument),
    loading: readonly(loading),
    error: readonly(error),
    
    // 計算されたプロパティ
    isMarkdown,
    isHTML,
    isQuarto,
    documentTitle,
    
    // メソッド
    loadDocument,
    loadSourceFile,
    clearDocument
  };
}
```

## 5. Vue Router統合

### 5.1 ルーター設定

```typescript
// router/index.ts
import { createRouter, createWebHistory } from 'vue-router';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/docs/:service/:owner/:repo/:path(.*)*',
      name: 'Document',
      component: () => import('@/views/DocumentView.vue'),
      props: route => ({
        service: route.params.service,
        owner: route.params.owner,
        repo: route.params.repo,
        path: route.params.path,
        ref: route.query.ref || 'main'
      })
    }
  ]
});

export default router;
```

### 5.2 ドキュメントビューページ

```vue
<!-- views/DocumentView.vue -->
<template>
  <div class="document-view">
    <div v-if="loading" class="loading-state">
      <Spinner />
      <p>ドキュメントを読み込み中...</p>
    </div>
    
    <div v-else-if="error" class="error-state">
      <Icon name="error" />
      <h2>エラーが発生しました</h2>
      <p>{{ error }}</p>
      <button @click="retryLoad" class="retry-button">
        再試行
      </button>
    </div>
    
    <DocumentViewer
      v-else-if="currentDocument"
      :document="currentDocument"
      :show-t-o-c="true"
      @link-click="handleLinkClick"
      @source-request="handleSourceRequest"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useDocument } from '@/composables/useDocument';
import DocumentViewer from '@/components/DocumentViewer.vue';

interface Props {
  service: string;
  owner: string;
  repo: string;
  path: string;
  ref?: string;
}

const props = withDefaults(defineProps<Props>(), {
  ref: 'main'
});

const route = useRoute();
const router = useRouter();

const {
  currentDocument,
  loading,
  error,
  loadDocument,
  loadSourceFile
} = useDocument();

// ドキュメント読み込み
const loadCurrentDocument = async () => {
  try {
    await loadDocument(
      props.service,
      props.owner,
      props.repo,
      props.path,
      {
        ref: props.ref,
        transformLinks: true,
        baseUrl: `https://api.example.com/${props.service}/${props.owner}/${props.repo}/raw/${props.ref}`
      }
    );
  } catch (err) {
    console.error('Failed to load document:', err);
  }
};

// リンククリックハンドラー
const handleLinkClick = (url: string, external: boolean) => {
  if (external) {
    // 外部リンクは新しいタブで開く
    window.open(url, '_blank', 'noopener,noreferrer');
  } else {
    // 内部リンクはSPAナビゲーション
    router.push({
      name: 'Document',
      params: {
        service: props.service,
        owner: props.owner,
        repo: props.repo,
        path: url
      },
      query: {
        ref: props.ref
      }
    });
  }
};

// ソースファイル要求ハンドラー
const handleSourceRequest = async (sourceFile: string) => {
  try {
    await loadSourceFile(sourceFile);
    
    // URLを更新してソースファイルに移動
    router.push({
      name: 'Document',
      params: {
        service: props.service,
        owner: props.owner,
        repo: props.repo,
        path: sourceFile
      },
      query: {
        ref: props.ref
      }
    });
  } catch (err) {
    console.error('Failed to load source file:', err);
  }
};

const retryLoad = () => {
  loadCurrentDocument();
};

// ライフサイクル & ウォッチャー
onMounted(() => {
  loadCurrentDocument();
});

// ルートパラメータの変更を監視
watch(
  () => [props.service, props.owner, props.repo, props.path, props.ref],
  () => {
    loadCurrentDocument();
  }
);
</script>

<style scoped>
.document-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  text-align: center;
}

.retry-button {
  background: var(--primary-color);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 0.375rem;
  cursor: pointer;
  margin-top: 1rem;
}

.retry-button:hover {
  background: var(--primary-hover-color);
}

@media (max-width: 768px) {
  .document-view {
    padding: 1rem;
  }
}
</style>
```

## 6. 必要な依存関係

### 6.1 package.json 追加依存関係

```json
{
  "dependencies": {
    "dompurify": "^3.0.5",
    "@types/dompurify": "^3.0.5"
  }
}
```

### 6.2 インストールコマンド

```bash
npm install dompurify @types/dompurify
```

## 7. セキュリティ考慮事項

### 7.1 HTMLサニタイゼーション設定

- `DOMPurify`を使用してXSS攻撃を防止
- 許可するタグと属性を明示的に制限
- イベントハンドラー属性は完全に禁止
- 外部リソースの読み込みを制限

### 7.2 CSP (Content Security Policy) 設定

```html
<!-- index.html -->
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               script-src 'self' 'unsafe-inline'; 
               style-src 'self' 'unsafe-inline'; 
               img-src 'self' data: https:; 
               connect-src 'self' https://api.example.com;">
```

## 8. テスト実装

### 8.1 HTMLレンダラーのテスト

```typescript
// tests/components/HTMLRenderer.test.ts
import { mount } from '@vue/test-utils';
import HTMLRenderer from '@/components/HTMLRenderer.vue';
import type { DocumentResponse } from '@/types/document';

const mockHTMLDocument: DocumentResponse = {
  path: 'test.html',
  name: 'test.html',
  type: 'html',
  content: {
    content: '<h1>Test</h1><p>Content with <a href="./link.html">link</a></p>',
    encoding: 'utf-8'
  },
  metadata: {
    size: 100,
    last_modified: '2023-01-01T00:00:00Z',
    content_type: 'text/html',
    extra: {
      html: {
        title: 'Test Document',
        headings: [
          { level: 1, text: 'Test', tag: 'h1' }
        ],
        lang: 'en',
        charset: 'UTF-8'
      }
    }
  },
  repository: 'test-repo',
  owner: 'test-owner',
  service: 'mock',
  ref: 'main'
};

describe('HTMLRenderer', () => {
  it('renders HTML content safely', () => {
    const wrapper = mount(HTMLRenderer, {
      props: {
        document: mockHTMLDocument,
        baseUrl: 'https://example.com'
      }
    });
    
    expect(wrapper.find('h1').text()).toBe('Test');
    expect(wrapper.find('p').exists()).toBe(true);
    expect(wrapper.find('a').exists()).toBe(true);
  });
  
  it('emits link click events', async () => {
    const wrapper = mount(HTMLRenderer, {
      props: {
        document: mockHTMLDocument,
        baseUrl: 'https://example.com'
      }
    });
    
    await wrapper.find('a').trigger('click');
    
    expect(wrapper.emitted('linkClick')).toBeTruthy();
    expect(wrapper.emitted('linkClick')![0]).toEqual(['./link.html', false]);
  });
});
```

## 9. パフォーマンス最適化

### 9.1 レイジーローディング

```typescript
// コンポーネントの遅延読み込み
const HTMLRenderer = defineAsyncComponent(() => 
  import('@/components/HTMLRenderer.vue')
);
```

### 9.2 キャッシュ戦略

```typescript
// services/documentCache.ts
class DocumentCache {
  private cache = new Map<string, DocumentResponse>();
  private maxSize = 50;
  
  get(key: string): DocumentResponse | undefined {
    return this.cache.get(key);
  }
  
  set(key: string, document: DocumentResponse): void {
    if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
    this.cache.set(key, document);
  }
  
  generateKey(service: string, owner: string, repo: string, path: string, ref: string): string {
    return `${service}/${owner}/${repo}/${path}@${ref}`;
  }
}

export const documentCache = new DocumentCache();
```

## 10. デバッグとトラブルシューティング

### 10.1 開発者ツール統合

```typescript
// デバッグ用のログ出力
if (process.env.NODE_ENV === 'development') {
  console.log('Document loaded:', currentDocument.value);
  console.log('HTML metadata:', currentDocument.value?.metadata.extra?.html);
}
```

### 10.2 エラーバウンダリー

```vue
<!-- components/ErrorBoundary.vue -->
<template>
  <div v-if="hasError" class="error-boundary">
    <h2>予期しないエラーが発生しました</h2>
    <details>
      <summary>エラー詳細</summary>
      <pre>{{ errorDetails }}</pre>
    </details>
    <button @click="resetError">リセット</button>
  </div>
  <slot v-else />
</template>

<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue';

const hasError = ref(false);
const errorDetails = ref('');

onErrorCaptured((error) => {
  hasError.value = true;
  errorDetails.value = error.toString();
  return false;
});

const resetError = () => {
  hasError.value = false;
  errorDetails.value = '';
};
</script>
```

この実装指示書に従って、既存のVue.jsアプリケーションにHTMLドキュメント表示機能を統合できます。MarkdownとHTMLの両方をサポートする統一されたドキュメントビューワーが完成します。
