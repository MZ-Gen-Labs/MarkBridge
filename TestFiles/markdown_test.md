# Markdownプレビューテスト

これはMarkdownプレビュー機能をテストするためのファイルです。

## 見出しテスト

### 見出し3
#### 見出し4
##### 見出し5

---

## テキスト装飾

**太字テキスト** と *斜体テキスト* と ~~取り消し線~~ です。

`インラインコード`も表示できます。

> これは引用ブロックです。
> 複数行にまたがることもできます。

---

## リスト

### 順序なしリスト
- 項目1
- 項目2
  - ネストした項目2-1
  - ネストした項目2-2
- 項目3

### 順序付きリスト
1. 最初の項目
2. 2番目の項目
3. 3番目の項目

### チェックリスト
- [x] 完了したタスク
- [ ] 未完了のタスク
- [ ] もう一つの未完了タスク

---

## 表（テーブル）

| 機能 | ステータス | 説明 |
|------|----------|------|
| MarkItDown | ✅ 有効 | 標準変換エンジン |
| Docling | ✅ 有効 | 高度PDF解析 |
| EasyOCR | ✅ 有効 | スキャンPDF対応 |
| CUDA | ⚡ GPU | GPU高速処理 |

### 右寄せ・中央揃えの表

| 左寄せ | 中央揃え | 右寄せ |
|:-------|:--------:|-------:|
| Apple | 100円 | 10個 |
| Banana | 80円 | 25個 |
| Cherry | 300円 | 5個 |

---

## コードブロック

### Python
```python
def hello_world():
    print("Hello, MarkBridge!")
    return True

# Doclingを使用した変換
for file in files:
    result = convert(file)
```

### C#
```csharp
public class ConversionService
{
    public async Task<bool> ConvertAsync(string path)
    {
        await Task.Delay(100);
        return true;
    }
}
```

### JSON
```json
{
    "name": "MarkBridge",
    "version": "0.0.10",
    "engines": ["MarkItDown", "Docling"]
}
```

---

## リンクと画像

[MarkBridge GitHub](https://github.com/MZ-Gen-Labs/MarkBridge)

画像の例（存在しない場合はプレースホルダー）:
![サンプル画像](https://via.placeholder.com/200x100)

---

## 数式（対応している場合）

インライン数式: $E = mc^2$

ブロック数式:
$$
\sum_{i=1}^{n} x_i = x_1 + x_2 + ... + x_n
$$

---

## 水平線

上記

---

下記

---

## 特殊文字

&copy; 2024 MarkBridge | &rarr; 矢印 | &hearts; ハート

---

## 長いテキスト

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

**テスト完了！** 🎉
