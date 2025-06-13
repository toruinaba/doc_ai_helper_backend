---
title: テスト文書
description: これはテスト用のMarkdownドキュメントです
author: テスト太郎
date: 2023-01-01
tags:
  - test
  - markdown
  - sample
---

# テスト文書

これはテスト用のMarkdownドキュメントです。フロントマターやリンクの処理テストに使用されます。

## リンクテスト

以下はさまざまな種類のリンクです：

- [内部リンク](./another.md)
- [サブディレクトリリンク](./subdir/document.md)
- [絶対パスリンク](/root/document.md)
- [外部リンク](https://example.com)
- [アンカーリンク](#section)

## 画像テスト

![サンプル画像](./images/sample.png)
![外部画像](https://example.com/image.jpg)

## コードブロック

```python
def hello():
    print("Hello, world!")
```

## セクション {#section}

これはアンカーリンクのターゲットとなるセクションです。
