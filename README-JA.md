# ComfyUI PyPromptGenerator Node

Pythonスクリプトを使用して動的なプロンプト生成を可能にする、ComfyUI用の強力なカスタムノードです。この拡張機能により、スクリプトを通じて洗練されたポジティブ・ネガティブプロンプトを作成でき、従来の静的プロンプトよりも柔軟性と制御性を提供します。

以下のような場面に最適です：
- **条件付きプロンプト生成** - ポジティブコンテンツに基づいて補完的なネガティブ用語を追加
- **重み付きランダム選択** - 特定の確率でプロンプト要素を選択
- **複雑なプロンプトロジック** - テンプレート言語を学ぶ代わりにPythonの全機能を使用
- **ファイルベースプロンプト** - 外部ファイルからプロンプトスクリプトを読み込み実行
- **動的ワイルドカードサポート** - キャッシュ機能付きの高度なワイルドカード展開

## インストール

### オプション1: ComfyUI Manager（推奨）
1. [ComfyUI](https://docs.comfy.org/get_started)をインストール
2. [ComfyUI-Manager](https://github.com/ltdrdata/ComfyUI-Manager)をインストール
3. ComfyUI-Managerで「PyPromptGenerator」を検索してインストール
4. ComfyUIを再起動

### オプション2: 手動インストール
1. ComfyUIのインストールディレクトリに移動
2. `custom_nodes/`フォルダに移動
3. このリポジトリをクローン：
   ```bash
   git clone https://github.com/pickles/ComfyUI-PyPromptGenerator.git
   ```
4. ComfyUIを再起動

## 富士山デモによるクイックスタート

このプロジェクトには、PyPromptGeneratorの全機能を美しい富士山アートワークプロンプトの生成を通じて紹介する包括的なデモスクリプトが含まれています。

### デモの実行

プロジェクトにはサンプルスクリプト実行用の便利なラッパースクリプトが含まれています：

```bash
# プロジェクトディレクトリに移動
cd ComfyUI-PyPromptGenerator

# 利用可能なサンプルスクリプトを一覧表示
python run_sample.py --list

# 富士山ジェネレーターデモを実行
python run_sample.py mount_fuji_generator

# ヘルプを表示
python run_sample.py --help
```

### 富士山ジェネレーターの機能

`mount_fuji_generator.py`では以下の機能を実演：

- **🎨 アートスタイル選択**: 日本画、浮世絵、水墨画、水彩画、写真的リアリズム
- **🌸 季節変化**: 春の桜、秋の紅葉、冬の雪景色、夏の緑
- **🏔️ 動的構図**: 河口湖からの眺め、忠霊塔、田園風景、日本庭園
- **🎨 色彩パレット**: ソフトパステル、劇的な夕焼け、モノクロ調、アース系
- **✨ 大気効果**: レンズフレア、ボケ、ボリュメトリックライティング、大気のかすみ
- **⛩️ 伝統的要素**: 鳥居、日本の書道、金箔アクセント
- **🔄 ネストワイルドカード**: ワイルドカード参照を使った複雑な構図
- **🎲 重み付き選択**: 異なるスタイルと季節のバランスの取れた確率
- **📊 スマート構造**: 整理されたプロンプトセクションのためのBREAK記法

### サンプル出力

```
=== Mount Fuji Artwork Generation Demo ===

【Style】: ukiyo-e woodblock print
【Season】: spring with cherry blossoms  
【Composition】: reflection in lake waters
【Colors】: soft pastel colors
【Mood】: serene and peaceful
【Resolution】: 1280x720

【Positive Prompt】 (385 characters):
Mount Fuji, reflection in lake waters
BREAK
ukiyo-e woodblock print, masterpiece, fine art
BREAK
spring with cherry blossoms, sunrise golden light, soft pastel colors
BREAK
blooming sakura trees, traditional torii gate
BREAK
gentle bokeh effect, atmospheric haze
BREAK
serene and peaceful, intricate brush strokes, delicate cloud formations
BREAK
1280x720, fine art

【Statistics】:
- Number of wildcards used: 6
- Foreground elements: 2
- Artistic details: 3
- Traditional elements: None
- Atmospheric effects: 2
```

### 独自スクリプトの作成

`run_sample.py`ラッパーを使用することで、独自のプロンプト生成スクリプトを作成・実行できます：

1. `sample_scripts/`ディレクトリに新しいPythonファイルを作成
2. インポートなしでPyPromptGeneratorの全ユーティリティ関数を使用
3. スクリプトを実行：`python run_sample.py your_script_name`

## 機能

### 🎯 **PyPromptGeneratorノード**
- **インラインPythonスクリプト**: ノード内で直接プロンプト生成ロジックを記述
- **豊富なユーティリティ関数**: 重み付き選択、リスト操作、ランダム化のための組み込み関数
- **サンドボックス実行**: Pythonの機能への制御されたアクセスによる安全な実行環境

### 📁 **PyPromptFileGeneratorノード**
- **外部スクリプトファイル**: ファイルからPythonスクリプトを読み込んで実行
- **ホットリロード**: ファイル変更を自動検出してスクリプトをリロード
- **整理されたワークフロー**: 複雑なプロンプトロジックを別の再利用可能ファイルに保持
- **バージョン管理**: プロジェクト内でプロンプトスクリプトを追跡・管理

### 🛠 **強力なユーティリティ関数**
すべてのノードで専用ユーティリティ関数にアクセス可能：

- **`choice(items, count=1)`** - 重み付きサポート付きランダム選択
  ```python
  # 基本選択
  choice(["red", "blue", "green"])
  
  # 重み付き選択（redが3倍の確率）
  choice(["3::red", "1::blue", "1::green"])
  
  # 複数選択（重複なし）
  choice(["cat", "dog", "bird"], count=2)
  ```

- **`weighted_choice(items, weights=None)`** - 高度な重み付き選択
- **`shuffle_list(items)`** - 元のリストを変更せずにランダム化
- **`random_range(min, max, step=1)`** - 範囲内での乱数生成
- **`random_boolean(probability=0.5)`** - カスタム確率でのランダムtrue/false
- **`join(items, separator=", ")`** - BREAKサポート付きスマート結合
- **`maybe(value, probability=0.5)`** - 条件付きコンテンツ含有
- **`flatten(nested_list, depth=None)`** - 空文字フィルタリング付きネスト構造平坦化

### 🃏 **高度なワイルドカードサポート**
- **動的読み込み**: ディレクトリからワイルドカードファイルを自動読み込み
- **キャッシュ機能**: スマートキャッシュによる効率的ワイルドカード処理
- **ネストサポート**: 複雑な構造のためのワイルドカード内ワイルドカード使用

## ワイルドカードファイルの作成

ワイルドカードファイルを使用することで、プロンプトでランダムに選択可能な再利用可能な用語リストを定義できます。システムは`wildcards/`ディレクトリから`.txt`ファイルを自動的に読み込みます。

### ファイル構造
`wildcards/`ディレクトリにテキストファイルを作成：
```
wildcards/
├── fuji_colors.txt                  # 富士山の色彩パレット
├── fuji_compositions.txt            # 構図とビューポイント
├── fuji_compositions_complex.txt    # ネストワイルドカード構図
├── fuji_details.txt                 # 芸術的詳細と効果
├── fuji_foreground.txt              # 前景要素
├── fuji_seasons.txt                 # 季節と天候条件
├── mount_fuji_styles.txt            # 富士山用アートスタイル
└── your_custom_wildcards.txt        # 独自のワイルドカードファイルを追加
```

プロジェクトには例として富士山テーマのワイルドカードファイルが含まれていますが、任意の題材用に独自のワイルドカードファイルを作成できます。

### ファイル形式
各ワイルドカードファイルは1行に1つのアイテムを含む必要があります：

**例: `wildcards/mount_fuji_styles.txt`**
```
traditional Japanese painting
ukiyo-e woodblock print
sumi-e ink painting
watercolor landscape
oil painting masterpiece
digital art concept
photorealistic landscape
anime landscape style
studio ghibli style
minimalist landscape
impressionist painting
vintage postcard style
```

**例: `wildcards/fuji_colors.txt`**
```
soft pastel colors
vibrant autumn hues
monochromatic blue tones
warm golden lighting
cool morning blues
dramatic sunset oranges
ethereal misty whites
deep forest greens
pristine snow whites
rich earth tones
```

**例: `wildcards/fuji_seasons.txt`**
```
spring with cherry blossoms
summer with lush greenery
autumn with red maple leaves
winter with snow-capped peak
early morning mist
sunset golden hour
clear blue sky day
dramatic storm clouds
moonlit night scene
dawn breaking over mountains
```

### 高度なワイルドカード機能

#### 重み付きエントリ
`weight::item`形式を使用してエントリに重みを追加：
```
# effects.txt
10::highly detailed
5::masterpiece
3::professional
2::cinematic lighting
1::award winning
```

#### コメントと空行
- `#`で始まる行はコメントとして扱われ、無視されます
- 空行は自動的にフィルタリングされます
- コメントを使用してワイルドカードファイルを整理

**例: `wildcards/moods.txt`**
```
# ポジティブな雰囲気
cheerful
serene
confident
playful

# ニュートラルな雰囲気
calm
focused
contemplative

# 強烈な雰囲気
dramatic
mysterious
epic
```

#### ネストワイルドカード（上級者向け）
`{wildcard_name}`構文を使用してワイルドカードファイル内で他のワイルドカードファイルを参照可能：

**例: `wildcards/fuji_compositions_complex.txt`**
```
{mount_fuji_styles} of Mount Fuji in {fuji_seasons}
{fuji_compositions} with {fuji_foreground} in foreground
{fuji_colors} Mount Fuji landscape with {fuji_details}
traditional Japanese {mount_fuji_styles} featuring {fuji_foreground}
{fuji_seasons} Mount Fuji scene with {fuji_compositions}
```

**ネストワイルドカードの動作:**
- `{wildcard_name}`を使用して他のワイルドカードファイルを参照（アンダースコアプレフィックスなし）
- 1行あたり複数の参照をサポート
- 各参照は参照されたワイルドカードからのランダム選択で置換
- 自己参照は検出され、防止されます
- 無効な参照は警告付きでそのまま残されます

**展開例:**
- `{mount_fuji_styles} of Mount Fuji in {fuji_seasons}` は `"ukiyo-e woodblock print of Mount Fuji in spring with cherry blossoms"` になる可能性
- `{fuji_colors} Mount Fuji landscape with {fuji_details}` は `"dramatic sunset oranges Mount Fuji landscape with intricate brush strokes"` になる可能性

### スクリプトでのワイルドカード使用

ワイルドカードファイルは`_`プレフィックス付きの変数として自動的に読み込まれます：

```python
# ワイルドカード変数は自動的に利用可能
# _mount_fuji_styles, _fuji_colors, _fuji_seasons, etc.

# 基本的な使用法
selected_style = choice(_mount_fuji_styles)
selected_color = choice(_fuji_colors)
selected_season = choice(_fuji_seasons)

positive_prompt = f"{selected_style}, {selected_color}, {selected_season}"

# 複数選択を使った高度な使用法
style_combo = choice(_mount_fuji_styles, count=2)  # 2つの異なるスタイルを取得
details = choice(_fuji_details, count=3)  # 3つの異なる詳細を取得

positive_prompt = f"{join(style_combo)}, Mount Fuji, {join(details)}"

# 季節要素との条件付き使用
if "spring" in selected_season:
    foreground = choice(_fuji_foreground)
    positive_prompt += f", {foreground}"

# 使用前にワイルドカードの存在確認
if '_fuji_compositions_complex' in globals():
    complex_comp = choice(_fuji_compositions_complex)
    positive_prompt = complex_comp
else:
    composition = "majestic view from Lake Kawaguchi"  # フォールバック
```

### ワイルドカード管理関数

```python
# ワイルドカードファイルをリロード（開発時に便利）
refresh_wildcards()

# 利用可能なワイルドカード変数をすべて取得
wildcard_vars = get_wildcard_vars()
print(f"利用可能なワイルドカード: {list(wildcard_vars.keys())}")

# カスタムディレクトリからワイルドカードを読み込み
custom_wildcards = load_wildcards("/path/to/custom/wildcards")
```

### ベストプラクティス

1. **カテゴリ別に整理**: 異なるタイプのコンテンツに対して別々のファイルを作成
2. **説明的な名前を使用**: ファイル名が変数名になります（`styles.txt` → `_styles`）
3. **重みを含める**: 選択確率をより制御するために重みを使用
4. **コメントでドキュメント化**: `#`コメントを使用してエントリを整理・説明
5. **組み合わせをテスト**: ワイルドカードの組み合わせが意味をなすことを確認
6. **バージョン管理**: チームプロジェクトではワイルドカードファイルをバージョン管理下に置く

### ワイルドカードのトラブルシューティング

**ワイルドカードが見つからない:**
```python
# 常にワイルドカードの存在を確認
if '_mount_fuji_styles' in globals():
    style = choice(_mount_fuji_styles)
else:
    print("ワイルドカード _mount_fuji_styles が見つかりません")
    style = "traditional Japanese painting"
```

**変更後のリロード:**
```python
# ワイルドカードファイルを修正した場合は強制リロード
refresh_wildcards()
selected_item = choice(_fuji_colors)  # 更新されたファイルを使用
```

### 🔧 **開発者向け機能**
- **包括的テスト**: 全機能をカバーする94のテストケースを含む完全なテストスイート
- **型安全性**: 適切な型ヒント付きMyPy互換
- **コード品質**: Ruffリンティングとpre-commitフック
- **ドキュメント**: 豊富なインラインドキュメントと例
- **サンプルスクリプト**: 全機能を実演する完全な富士山アートジェネレーター
- **スクリプトラッパー**: テストと開発用の使いやすい`run_sample.py`

## 使用例

### 基本的なプロンプト生成
```python
# シンプルな条件付きプロンプト
if random_boolean(0.7):
    positive_prompt = "beautiful landscape, " + choice(["sunset", "sunrise", "noon"])
else:
    positive_prompt = "portrait, " + choice(["smiling", "serious", "contemplative"])

negative_prompt = "blurry, low quality"
```

### 重み付き選択
```python
# 異なるレアリティのキャラクター
character = choice([
    "10::warrior",    # 一般的（10倍の重み）
    "5::mage",        # アンコモン（5倍の重み） 
    "1::dragon"       # レア（1倍の重み）
])

positive_prompt = f"{character}, fantasy art"
negative_prompt = "modern, realistic"
```

### 補完ネガティブ
```python
# ポジティブコンテンツに基づいて自動的にネガティブ用語を生成
styles = ["anime", "realistic", "cartoon", "oil painting"]
chosen_style = choice(styles)

positive_prompt = f"{chosen_style} style, beautiful woman"

# 他のスタイルをネガティブに追加
other_styles = [s for s in styles if s != chosen_style]
negative_prompt = join(other_styles) + ", ugly, deformed"
```

### ファイルベーススクリプトを使った複雑なロジック
ファイル `advanced_portrait.py` を作成：
```python
# キャラクター原型を定義
archetypes = {
    "warrior": {
        "features": ["strong jaw", "battle scars", "determined eyes"],
        "avoid": ["delicate", "frail", "peaceful"]
    },
    "mage": {
        "features": ["wise eyes", "mystical aura", "intricate robes"],
        "avoid": ["mundane", "simple", "ordinary"]
    }
}

# 原型を選択
archetype = choice(list(archetypes.keys()))
data = archetypes[archetype]

# プロンプトを構築
features = choice(data["features"], count=2)
positive_prompt = f"{archetype}, {join(features)}, masterpiece"
negative_prompt = join(data["avoid"]) + ", low quality"
```

### プロンプト構造にBREAKを使用
```python
# ブレーク付きの構造化プロンプトを作成
elements = [
    "portrait of a woman",
    "BREAK",
    choice(["red hair", "blonde hair", "black hair"]),
    choice(["blue eyes", "green eyes", "brown eyes"]),
    "BREAK", 
    "photorealistic, high detail"
]

positive_prompt = join(elements)
# 結果: "portrait of a woman\nBREAK\nred hair, blue eyes\nBREAK\nphotorealistic, high detail"
```

### ネストワイルドカードの使用
```python
# ネスト参照付きワイルドカードファイルを作成
# mount_fuji_styles.txt: traditional Japanese painting, ukiyo-e woodblock print, sumi-e ink painting
# fuji_colors.txt: soft pastel colors, dramatic sunset oranges, monochromatic blue tones
# fuji_compositions_complex.txt: {mount_fuji_styles} of Mount Fuji in {fuji_seasons}

# スクリプトでネストワイルドカードを使用
if '_fuji_compositions_complex' in globals():
    complex_composition = choice(_fuji_compositions_complex)
    # 結果例: "ukiyo-e woodblock print of Mount Fuji in spring with cherry blossoms"
    positive_prompt = f"{complex_composition}, masterpiece, highly detailed"
else:
    positive_prompt = "Mount Fuji landscape, masterpiece, highly detailed"

negative_prompt = "low quality, blurry, modern buildings"
```

## 開発

## 開発

### 開発環境のセットアップ

開発依存関係とpre-commitフックをインストール：

```bash
cd ComfyUI-PyPromptGenerator
pip install -e .[dev]
pre-commit install
```

`-e`フラグにより「ライブ」インストールが行われ、拡張機能への変更がComfyUI再起動時に自動的に反映されます。

### テストの実行

プロジェクトには94のテストケースからなる包括的なテストカバレッジが含まれています：

```bash
# すべてのテストを実行
pytest

# 特定のテストカテゴリを実行
pytest -m unit          # ユニットテストのみ
pytest -m integration   # 統合テストのみ
pytest -m slow          # 低速テストのみ

# カバレッジ付きで実行
pytest --cov=src --cov-report=html

# 詳細出力でテストを実行
pytest -v
```

テストカテゴリには以下が含まれます：
- **choice関数テスト** (17テスト) - 重み付き選択、複数選択、エッジケース
- **ユーティリティ関数テスト** (20テスト) - `maybe`、`flatten`、`join`を含む全ユーティリティ関数
- **ネストワイルドカードテスト** (9テスト) - 高度なワイルドカード機能
- **統合テスト** (13テスト) - ComfyUIノード統合と複雑なシナリオ
- **ワイルドカードテスト** (10テスト) - ワイルドカード読み込み、キャッシュ、管理
- **ファイルジェネレーターテスト** (8テスト) - ファイルベーススクリプト実行
- **flatten関数テスト** (13テスト) - 様々なシナリオでの配列平坦化
- **その他の専門テスト** (4テスト) - 追加エッジケースと機能

### コード品質

このプロジェクトではコード品質維持のため複数のツールを使用：

- **Ruff**: 高速Pythonリンターとフォーマッター
- **MyPy**: 静的型チェック
- **Pre-commit**: 自動コード品質チェック
- **Pytest**: 包括的テストフレームワーク

### プロジェクト構造

```
ComfyUI-PyPromptGenerator/
├── src/pyprompt_generator/           # メインパッケージ
│   ├── nodes.py                     # ComfyUIノード実装
│   ├── utils.py                     # ネストワイルドカード付きユーティリティ関数
│   └── __init__.py                  # パッケージ初期化
├── sample_scripts/                   # サンプルスクリプトとデモ
│   └── mount_fuji_generator.py      # 包括的な富士山アートジェネレーターデモ
├── tests/                           # 包括的テストスイート（94テスト）
│   ├── test_choice.py               # choice関数テスト
│   ├── test_file_generator.py       # ファイルジェネレーターノードテスト
│   ├── test_flatten.py              # flatten関数テスト
│   ├── test_integration.py          # 統合テスト
│   ├── test_nested_wildcards.py     # ネストワイルドカードテスト
│   ├── test_utils.py                # ユーティリティ関数テスト
│   ├── test_wildcard.py             # ワイルドカード関数テスト
│   ├── test_wildcard_manager.py     # WildcardManagerテスト
│   ├── conftest.py                  # テスト設定
│   └── pytest.ini                   # Pytest設定
├── wildcards/                       # 富士山テーマワイルドカードファイル
│   ├── fuji_colors.txt              # 富士山用色彩パレット
│   ├── fuji_compositions.txt        # 構図とビューポイント
│   ├── fuji_compositions_complex.txt # ネストワイルドカード構図
│   ├── fuji_details.txt             # 芸術的詳細と効果
│   ├── fuji_foreground.txt          # 前景要素
│   ├── fuji_seasons.txt             # 季節と天候
│   ├── mount_fuji_styles.txt        # 富士山用アートスタイル
│   └── create_wildcards_here        # カスタムワイルドカード用プレースホルダー
├── run_sample.py                    # サンプルスクリプト実行ラッパー
├── .github/                         # GitHub設定
│   └── workflows/                   # CI/CDワークフロー
├── .vscode/                         # VS Code設定
├── pyproject.toml                   # プロジェクト設定
├── MANIFEST.in                      # パッケージマニフェスト
├── LICENSE                          # MITライセンス
├── README.md                        # ドキュメント（英語）
└── README-JA.md                     # ドキュメント（日本語）
```

## コントリビューション

コントリビューションを歓迎します！このプロジェクトは標準的なオープンソースコントリビューション慣行に従います：

1. **リポジトリをフォーク**
2. **機能ブランチを作成**: `git checkout -b feature/amazing-feature`
3. **変更を行う**: テストが通り、コードがスタイルガイドラインに従うことを確認
4. **テストを実行**: `pytest` と `pre-commit run --all-files`
5. **変更をコミット**: `git commit -m "Add amazing feature"`
6. **ブランチにプッシュ**: `git push origin feature/amazing-feature`
7. **プルリクエストを開く**

### ガイドライン
- 新機能にはテストを追加
- ユーザー向け変更にはドキュメントを更新
- 既存のコードスタイルと慣行に従う
- すべてのCIチェックが通ることを確認

## APIリファレンス

### ノードクラス

#### `PyPromptGeneratorNode`
インラインスクリプト実行のメインノード。

**入力:**
- `script` (STRING): 実行するPythonスクリプト

**出力:**
- `positive_prompt` (STRING): 生成されたポジティブプロンプト
- `negative_prompt` (STRING): 生成されたネガティブプロンプト

#### `PyPromptFileGeneratorNode`
ファイルベースのスクリプト実行ノード。

**入力:**
- `script_file` (STRING): Pythonスクリプトファイルのパス
- `base_path` (STRING, オプション): 相対パスのベースディレクトリ

**出力:**
- `positive_prompt` (STRING): 生成されたポジティブプロンプト
- `negative_prompt` (STRING): 生成されたネガティブプロンプト

### ユーティリティ関数リファレンス

完全な関数ドキュメントと例については、[`utils.py`](src/pyprompt_generator/utils.py)のインラインドキュメントを参照してください。

## トラブルシューティング

### よくある問題

**インポートエラー**
```
ImportError: cannot import name 'PyPromptGeneratorNode'
```
- インストール後にComfyUIが再起動されていることを確認
- 拡張機能が正しい`custom_nodes/`ディレクトリにあることを確認

**スクリプト実行エラー**
```
NameError: name 'choice' is not defined
```
- すべてのユーティリティ関数はスクリプトで自動的に利用可能
- インポート不要 - 関数は実行環境に注入されます

**ファイルが見つからない（PyPromptFileGeneratorNode）**
```
FileNotFoundError: Script file not found
```
- ComfyUIディレクトリからの相対パスが正しいことを確認
- 相対パスで問題がある場合は絶対パスを使用
- ファイルに`.py`拡張子があることを確認

### パフォーマンスのヒント

- 複雑なロジックにはファイルベーススクリプトを使用して再コンパイルを避ける
- ワイルドカード集約的ワークフローではキャッシュを有効化
- 両ノードとも動的コンテンツのため毎回実行時に自動更新

## レジストリへの公開

## レジストリへの公開

このカスタムノードをコミュニティの他の人と共有したい場合は、レジストリに公開できます。`pyproject.toml`の`tool.comfy`セクションにはすでにいくつかのフィールドが自動入力されていますが、正しいことを再確認してください。

https://registry.comfy.org でアカウントを作成し、APIキートークンを作成する必要があります。

- [ ] [レジストリ](https://registry.comfy.org)にアクセス。ログインしてパブリッシャーID（レジストリプロフィールの`@`記号の後のすべて）を作成
- [ ] パブリッシャーIDをpyproject.tomlファイルに追加
- [ ] GithubからのパブリッシングのためにレジストリでAPIキーを作成。[手順](https://docs.comfy.org/registry/publishing#create-an-api-key-for-publishing)
- [ ] Githubリポジトリシークレットに`REGISTRY_ACCESS_TOKEN`として追加

Githubアクションはgit pushの度に実行されます。Githubアクションを手動で実行することも可能です。完全な手順は[こちら](https://docs.comfy.org/registry/publishing)。質問がある場合は[discord](https://discord.com/invite/comfyorg)に参加してください！

## ライセンス

このプロジェクトはMITライセンスの下でライセンスされています - 詳細は[LICENSE](LICENSE)ファイルを参照してください。
