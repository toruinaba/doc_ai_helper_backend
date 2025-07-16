# HTML タグを含むマークダウンサンプル

このファイルはHTMLタグ内のリンクを含むサンプルです。

## 標準的なMarkdownリンク

- [別のドキュメント](./another.md)
- [サブディレクトリ内](./subdir/doc.md)

## HTMLタグ内のリンク

これらのリンクは現在変換されていません：

<a href="./relative-link.md">HTMLアンカータグ</a>

<img src="./images/local.png" alt="HTMLイメージタグ">

<link rel="stylesheet" href="./styles/main.css">

<p>段落内の<a href="../parent.md">相対リンク</a>です。</p>

<div class="content">
  <a href="./subdir/nested.md">ネストされたHTMLリンク</a>
  <img src="./assets/icon.svg" alt="アイコン">
</div>

## 複雑なHTMLケース

<details>
  <summary>詳細を表示</summary>
  <p>詳細内容に<a href="./details.md">リンク</a>があります。</p>
  <img src="./images/detail.png" alt="詳細画像">
</details>

<table>
  <tr>
    <td><a href="./table-link.md">テーブル内リンク</a></td>
    <td><img src="./icons/check.png" alt="チェック"></td>
  </tr>
</table>