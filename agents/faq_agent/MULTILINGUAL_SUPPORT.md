# FAQ Agent 多語言支持指南

## 當前狀態

FAQ Agent 目前已支持**所有語言**，因為 OpenAI 的 embedding 模型是多語言的。

## 已支持功能

### 1. 多語言 Embedding
OpenAI `text-embedding-3-small` 和 `text-embedding-3-large` **原生支持 100+ 語言**:

- ✅ 中文 (繁體/簡體)
- ✅ 英文
- ✅ 日文
- ✅ 韓文
- ✅ 法文、德文、西班牙文等歐洲語言
- ✅ 阿拉伯文、希伯來文等從右到左語言
- ✅ 印地語、泰語等亞洲語言

### 2. 跨語言搜索
embedding 模型支持語義相似性，即使語言不同:

```python
# 用戶用中文提問
query = "如何重設密碼？"

# 可以找到英文 FAQ
faq = "How do I reset my password?"

# 因為語義相似，會被匹配到
```

## 優化建議

### 選項 1: 語言檢測 + 分類 (簡單)

```python
from langdetect import detect

async def search_with_language(query: str):
    lang = detect(query)  # 'zh-cn', 'en', 'ja' etc.
    
    # 優先搜索相同語言的 FAQ
    result = await search_tool.search(
        query=query,
        category=f"lang_{lang}",
        limit=10
    )
    
    # 如果結果不足，再搜索其他語言
    if len(result['results']) < 3:
        all_results = await search_tool.search(query, limit=10)
        return all_results
    
    return result
```

### 選項 2: 多語言 FAQ 管理

```python
# 為每個 FAQ 提供多語言版本
await mgmt_tool.create_faq(
    question_en="How do I reset my password?",
    question_zh="如何重設密碼？",
    question_ja="パスワードをリセットするにはどうすればよいですか？",
    answer_en="Click on 'Forgot Password'...",
    answer_zh="點擊「忘記密碼」...",
    answer_ja="「パスワードを忘れた」をクリックしてください...",
    metadata={
        'languages': ['en', 'zh', 'ja'],
        'primary_language': 'en'
    }
)

# 根據用戶語言返回對應答案
def get_answer_in_language(faq, user_lang):
    return faq[f'answer_{user_lang}'] or faq['answer_en']
```

### 選項 3: 自動翻譯 (進階)

```python
from openai import AsyncOpenAI

async def translate_answer(answer: str, target_lang: str):
    client = AsyncOpenAI()
    
    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"Translate to {target_lang}"},
            {"role": "user", "content": answer}
        ]
    )
    
    return response.choices[0].message.content
```

### 選項 4: 語言特定的全文搜索配置

```sql
-- PostgreSQL 支持多語言全文搜索
CREATE INDEX idx_faqs_question_zh 
ON faqs USING GIN (to_tsvector('chinese', question));

CREATE INDEX idx_faqs_question_en 
ON faqs USING GIN (to_tsvector('english', question));

CREATE INDEX idx_faqs_question_jp 
ON faqs USING GIN (to_tsvector('japanese', question));
```

## 實施策略

### 階段 1: 基礎多語言 (已完成)
- ✅ 使用 OpenAI 多語言 embedding
- ✅ 支持任何語言的 FAQ 和搜索
- ✅ 跨語言語義搜索

### 階段 2: 語言分類 (可選)
- 添加 `language` 欄位到 FAQ 表
- 自動檢測 FAQ 和查詢的語言
- 優先返回相同語言的結果

### 階段 3: 多語言內容 (可選)
- 支持同一 FAQ 的多語言版本
- 根據用戶語言偏好返回答案
- 自動翻譯功能

### 階段 4: 語言特定優化 (進階)
- 不同語言使用不同的分詞策略
- 語言特定的全文搜索配置
- 文化適應的答案內容

## 數據庫 Schema 擴展

```sql
-- 添加語言支持
ALTER TABLE faqs ADD COLUMN language VARCHAR(10) DEFAULT 'en';
ALTER TABLE faqs ADD COLUMN translations JSONB DEFAULT '{}';

-- 範例數據
INSERT INTO faqs (question, answer, language, translations) VALUES (
    'How do I reset my password?',
    'Click on Forgot Password...',
    'en',
    '{
        "zh": {
            "question": "如何重設密碼？",
            "answer": "點擊忘記密碼..."
        },
        "ja": {
            "question": "パスワードをリセットするには？",
            "answer": "パスワードを忘れたをクリック..."
        }
    }'
);
```

## 使用範例

### 範例 1: 自動語言檢測

```python
from langdetect import detect

async def smart_search(query: str):
    # 檢測語言
    lang = detect(query)
    
    # 記錄偏好
    search_result = await search_tool.search(
        query=query,
        metadata={'user_language': lang}
    )
    
    # 如果有翻譯，使用翻譯版本
    for result in search_result['results']:
        if lang != 'en' and 'translations' in result:
            if lang in result['translations']:
                result['answer'] = result['translations'][lang]['answer']
    
    return search_result
```

### 範例 2: 混合語言 FAQ 庫

```python
# 創建中文 FAQ
await mgmt_tool.create_faq(
    question="什麼是 Morning AI？",
    answer="Morning AI 是一個智能助理平台...",
    category="general",
    tags=["中文", "介紹"],
    metadata={'language': 'zh'}
)

# 創建英文 FAQ
await mgmt_tool.create_faq(
    question="What is Morning AI?",
    answer="Morning AI is an intelligent assistant platform...",
    category="general",
    tags=["english", "introduction"],
    metadata={'language': 'en'}
)

# 跨語言搜索仍然有效！
result = await search_tool.search("AI 助手是什麼")
# 兩個 FAQ 都可能匹配，因為語義相似
```

## 成本考慮

使用自動翻譯會增加成本:

| 功能 | 每次請求成本 | 建議 |
|------|------------|------|
| Embedding (多語言) | $0.000001 | ✅ 已包含，無額外成本 |
| 語言檢測 (langdetect) | 免費 | ✅ 推薦使用 |
| 自動翻譯 (GPT-3.5) | ~$0.0001-0.001 | ⚠️ 僅對重要 FAQ 使用 |

## 建議

1. **當前系統已足夠**: OpenAI embedding 原生支持多語言，無需額外配置

2. **可選增強**: 
   - 添加語言欄位幫助分類和過濾
   - 為重要 FAQ 提供人工翻譯版本
   - 使用 langdetect 優化搜索結果排序

3. **避免過度工程**: 
   - 不需要為每個 FAQ 自動翻譯所有語言
   - 讓語義搜索自然處理跨語言查詢
   - 僅在用戶量大且需求明確時添加複雜的多語言系統

## 總結

✅ **FAQ Agent 已經支持多語言**，無需額外配置

如果需要更精細的多語言支持:
1. 添加 `language` 欄位進行分類
2. 使用 `langdetect` 優化搜索
3. 為高頻 FAQ 提供多語言版本
4. 可選：使用 GPT 進行自動翻譯
