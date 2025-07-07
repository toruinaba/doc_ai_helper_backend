# Legacy LLM Service Components

このディレクトリには、LLMサービス層のリファクタリング前のファイルが保存されています。

## ディレクトリ構成

### `components/` (旧components/)
リファクタリング前の元のcomponentsディレクトリのバックアップです。
新しい構造では以下に分散されました：

- `messaging.py` → `../messaging/messaging.py`
- `functions.py` → `../functions/functions.py`
- `cache.py` → `../processing/cache.py`
- `templates.py` → `../processing/templates.py`
- `tokens.py` → `../processing/tokens.py`
- `response_builder.py` → `../processing/response_builder.py`
- `streaming_utils.py` → `../processing/streaming_utils.py`
- `query_manager.py` → `../query_manager.py`

### その他のlegacyファイル
- `common.py` - 削除されたLLMServiceCommonクラス
- `base_legacy.py` - 旧版の基底クラス
- `openai_*` - 旧版のOpenAI実装ファイル群

## 注意事項

これらのファイルは**アーカイブ目的のみ**で保持されており、アクティブな開発では使用されません。
新しいコードでは、リファクタリング後の構造を使用してください：

```python
# 新しい構造でのimport例
from doc_ai_helper_backend.services.llm.messaging import SystemPromptBuilder
from doc_ai_helper_backend.services.llm.functions import FunctionCallManager  
from doc_ai_helper_backend.services.llm.processing import LLMCacheService
```

リファクタリング完了日: 2025年7月7日
