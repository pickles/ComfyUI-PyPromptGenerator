# Prompt CDK

`prompt_cdk.py` は、画像生成プロンプトの構成要素と制約を宣言し、条件を満たす組み合わせをランダムに生成するための小さなフレームワークです。

AWS CDKでリソースを定義して最後にsynthするように、次の流れでプロンプトを生成します。

1. `PromptProgram` を作成する
2. 髪型、顔、体型、服装、ポーズ、場所などのdimensionを定義する
3. `when().require()` または `when().forbid()` で制約を定義する
4. `synth()` で有効な組み合わせを1つ選ぶ
5. `Scene.prompt()` でプロンプトを生成する

## ファイル

- `prompt_cdk.py`
  - CDK風のプロンプト定義フレームワーク
- `generate_random_image_prompt.py`
  - 登場人物、服装、ポーズ、場所を定義した実行例
- `test_imports.py`
  - Python標準ライブラリと同一フォルダのモジュールをimportするテスト
- `import_test_helper.py`
  - `test_imports.py` から読み込まれる補助モジュール

## ComfyUIで実行する

`PyPrompt File Generator` ノードに次の値を設定します。

```text
script_file: generate_random_image_prompt.py
base_path: D:\tools\StabilityMatrix-win-x64\Data\Packages\ComfyUI\custom_nodes\ComfyUI-PyPromptGenerator\sample_scripts
```

ノードの出力は次の2つです。

- `positive_prompt`
- `negative_prompt`

## 基本的な使い方

```python
from prompt_cdk import PromptProgram, option

program = PromptProgram("SimplePortrait")

program.fixed(["masterpiece", "best quality"])

woman = program.block("woman", ["girl", "adult woman", "solo"])

woman.dimension(
    "hair",
    option("bob", "short bob haircut"),
    option("long", "long wavy hair"),
)

woman.dimension(
    "outfit",
    option("swimsuit", "one-piece swimsuit", "swimwear"),
    option("casual", "knit sweater and jeans", "casual"),
)

woman.dimension(
    "location",
    option("beach", "sunny beach, blue ocean", "beach", "outdoor"),
    option("living_room", "cozy living room", "indoor", "home"),
)

woman.when("location", tag="beach").require("outfit", tag="swimwear")
woman.when("location", tag="indoor").forbid("outfit", tag="swimwear")

scene = program.synth()

positive_prompt = scene.prompt(prefix="")
negative_prompt = "low quality, blurry, bad anatomy"
```

## Fixed

`fixed()` はランダム選択を行わず、指定した文字列を常にプロンプトへ追加します。文字列または文字列配列を渡せます。

```python
program.fixed("masterpiece")
program.fixed(["best quality", "highly detailed"])
```

固定値もOptionと同様に1項目ずつ改行して出力されます。

## Block

`block()` は、人物などに関連する固定値とdimensionを連続したまとまりとして定義します。

```python
woman = program.block("woman", ["girl", "adult woman"])
woman.dimension(
    "hair",
    option("bob", "short bob haircut"),
    option("long", "long wavy hair"),
)
woman.dimension(
    "body",
    option("slender", "slender body"),
    option("athletic", "athletic body"),
)
woman.dimension(
    "pose",
    option("standing", "standing pose"),
    option("sitting", "sitting pose"),
)

program.break_()

man = program.block("man", "boy")
man.dimension(
    "hair",
    option("short", "short black hair"),
    option("wavy", "wavy brown hair"),
)
man.dimension(
    "pose",
    option("standing", "standing pose"),
    option("walking", "walking pose"),
)
```

出力例:

```text
girl,
adult woman,
short bob haircut,
slender body,
standing pose,
BREAK
boy,
short black hair,
walking pose
```

人物を表す語と、その人物の髪型・体型・ポーズが近接するため、属性の対応付けが弱い古いStable Diffusionモデルでも利用しやすくなります。

ブロック内のdimension名は自動的に名前空間化されます。

```python
scene.summary()

# {
#     "woman.hair": "bob",
#     "woman.body": "slender",
#     "woman.pose": "standing",
#     "man.hair": "short",
#     "man.pose": "walking",
# }
```

ブロック内で `when()` を使用すると、同じブロックのdimension名を短い名前で指定できます。

```python
woman.when("location", tag="beach").require("outfit", tag="swimwear")
```

ブロックをまたぐ制約や、ブロック外のdimensionとの制約には完全名を使用します。

```python
program.when("location", tag="beach").require(
    "woman.outfit",
    tag="swimwear",
)
```

## Option

`option()` は、dimension内で選択される候補を作成します。

```python
option(
    "one_piece_swimsuit",
    "elegant one-piece swimsuit",
    "swimwear",
    "beachwear",
    weight=2.0,
    negative="winter coat, business suit",
    break_before=True,
)
```

引数の意味:

| 引数 | 説明 |
|---|---|
| 第1引数 | optionを識別する一意なkey |
| 第2引数 | プロンプトへ追加する文字列 |
| 第3引数以降 | 制約で利用する任意のtag |
| `weight` | 選択される相対的な重み。初期値は`1.0` |
| `negative` | このoptionが採用された場合に追加するNegative断片 |
| `break_before` | このoptionが採用された場合、直前に`BREAK`行を挿入 |

keyは特定の候補を指定するときに使います。tagは複数の候補をまとめて扱うときに使います。

### Optionに複数のプロンプト断片を指定する

第2引数には、`fixed()` と同様に文字列または文字列の配列を指定できます。
配列を渡したOptionが採用されると、すべての要素が定義順に1項目ずつ改行して出力されます。

```python
from random import choice

program.dimension(
    "woman",
    option(
        "casual_woman",
        [
            "adult woman",
            choice(["short bob haircut", "long wavy hair"]),
            choice(["slender build", "athletic build"]),
        ],
        "woman",
        "casual",
    ),
)
```

この例ではスクリプト実行時に髪型と体型がそれぞれ選ばれ、`casual_woman` が採用された場合にまとめてプロンプトへ追加されます。

```text
adult woman,
short bob haircut,
athletic build
```

### 採用時にNegativeを追加する

`negative` を指定すると、そのoptionが選ばれた場合だけNegativeプロンプトへ追加されます。

```python
program.dimension(
    "location",
    option(
        "beach",
        "sunny beach, blue ocean",
        "beach",
        "outdoor",
        negative="indoor, living room, studio background",
    ),
    option(
        "living_room",
        "cozy modern living room",
        "indoor",
        "home",
        negative="beach, ocean, outdoor background",
    ),
)
```

海辺が選ばれた場合は `indoor, living room, studio background` が追加され、リビングが選ばれた場合は `beach, ocean, outdoor background` が追加されます。

## Dimension

`dimension()` は、ランダムに選択する項目を定義します。

```python
program.dimension(
    "body",
    option("slender", "slender build"),
    option("athletic", "athletic build"),
    option("curvy", "curvy build"),
)
```

dimension名は自由に追加できます。

```python
program.dimension(
    "weather",
    option("sunny", "clear sunny weather", "clear"),
    option("rain", "gentle rain, wet pavement", "rain"),
)

program.dimension(
    "camera",
    option("portrait", "portrait shot, 85mm lens"),
    option("wide", "wide-angle environmental shot"),
)
```

各dimensionから必ず1つのoptionが選ばれます。

### Dimensionの前にBREAKを入れる

dimension定義の間に `break_()` を置くと、次のdimensionの直前に `BREAK` が入ります。

```python
program.dimension(
    "body",
    option("slender", "slender build"),
    option("athletic", "athletic build"),
)

program.break_()

program.dimension(
    "outfit",
    option("casual", "knit sweater and jeans"),
    option("dress", "light summer dress"),
)
```

メソッドを連結して書くこともできます。

```python
program.dimension(
    "body",
    option("athletic", "athletic build"),
).break_().dimension(
    "outfit",
    option("activewear", "modern athletic wear"),
)
```

`break_()` の後には必ずdimension、block、fixedなどのプロンプト要素を定義してください。末尾に `break_()` を置いたまま `synth()` するとエラーになります。

従来の `break_before=True` をdimensionに指定する方法も利用できます。

```python
program.dimension(
    "outfit",
    option("casual", "knit sweater and jeans"),
    option("dress", "light summer dress"),
    break_before=True,
)
```

特定のoptionが選ばれた場合だけ `BREAK` を入れる場合:

```python
option(
    "dramatic",
    "dramatic cinematic lighting",
    break_before=True,
)
```

## 制約

### require

条件に一致した場合、別のdimensionが指定条件を満たすことを要求します。

```python
# 海辺では必ず水着にする
program.when("location", tag="beach").require(
    "outfit",
    tag="swimwear",
)
```

keyによる指定も可能です。

```python
# ソファのポーズはリビングだけで使用する
program.when("pose", tag="sofa").require(
    "location",
    key="living_room",
)
```

### 複数key

`when()`、`require()`、`forbid()` は、単一の `key` に加えて複数の `keys` を指定できます。

Optionはkeyを1つだけ持つため、`keys` は指定したkeyのいずれかに一致するOR条件です。

```python
program.when(
    "location",
    keys=["living_room", "cafe", "studio"],
).forbid(
    "woman.outfit",
    keys=["one_piece_swimsuit", "rash_guard"],
)
```

| 指定 | 意味 |
|---|---|
| `key="beach"` | 単一keyに一致 |
| `keys=["beach", "pool"]` | 指定したkeyのいずれかに一致 |

`key` と `keys` を同時に指定することはできません。

key条件とtag条件を同時に指定した場合は、両方を満たすOptionだけが一致します。

```python
program.when(
    "location",
    keys=["beach", "pool"],
    tag="outdoor",
)
```

### 複数タグ

`when()`、`require()`、`forbid()` は、単一の `tag` に加えて複数の `tags` を指定できます。

すべてのタグを持つ場合に一致させるには `match="all"` を使用します。

```python
program.when(
    "location",
    tags=["beach", "outdoor"],
    match="all",
).require(
    "woman.outfit",
    tags=["swimwear", "beachwear"],
    match="all",
)
```

いずれかのタグを持つ場合に一致させるには `match="any"` を使用します。

```python
program.when(
    "location",
    tags=["home", "cafe", "studio"],
    match="any",
).forbid(
    "woman.outfit",
    tag="swimwear",
)
```

| 指定 | 意味 |
|---|---|
| `tag="beach"` | 単一タグに一致 |
| `tags=["beach", "outdoor"]` | 複数タグを指定 |
| `match="all"` | 指定したすべてのタグを持つ場合に一致。初期値 |
| `match="any"` | 指定したタグを1つ以上持つ場合に一致 |

`tag` と `tags` を同時に指定することはできません。

### forbid

条件に一致した場合、別のdimensionが指定条件を満たすことを禁止します。

```python
# 室内では水着を禁止する
program.when("location", tag="indoor").forbid(
    "outfit",
    tag="swimwear",
)
```

### 双方向の制約

次の2つは意味が異なります。

```python
program.when("location", tag="beach").require("outfit", tag="swimwear")
program.when("outfit", tag="swimwear").require("location", tag="beach")
```

1行目だけの場合、「海辺なら水着」は保証されますが、水着が別の場所で選ばれる可能性は残ります。

水着を海辺だけに限定したい場合は、両方を定義してください。

```python
# 海辺なら水着
program.when("location", tag="beach").require("outfit", tag="swimwear")

# 水着なら海辺
program.when("outfit", tag="swimwear").require("location", tag="beach")
```

## 重み付き選択

`weight` が大きい候補ほど選ばれやすくなります。

```python
program.dimension(
    "hair",
    option("bob", "short bob haircut", weight=3.0),
    option("long", "long wavy hair", weight=1.0),
    option("pixie", "textured pixie cut", weight=0.5),
)
```

この例では、制約による候補除外を行った後、`bob`が`long`の約3倍の重みで選択されます。

複数dimensionの組み合わせでは、各optionのweightを掛け合わせた値が組み合わせ全体の重みになります。

## Seed

毎回異なる結果を生成する場合:

```python
scene = program.synth(seed=None)
```

同じ結果を再現する場合:

```python
scene = program.synth(seed=12345)
```

`generate_random_image_prompt.py` では、ファイル上部の値を変更できます。

```python
SEED = None
```

## Scene

`synth()` は `Scene` を返します。

### プロンプトを生成する

```python
positive_prompt = scene.prompt(
    "masterpiece, best quality, highly detailed, solo"
)
```

prefixの後ろに、dimensionの定義順で選択されたprompt文字列が追加されます。

prefixと各Optionはそれぞれ別の行に出力されます。`break_before=True` が指定された箇所では、独立した `BREAK` 行が挿入されます。

```text
masterpiece, best quality, highly detailed, solo,
short bob haircut,
gentle oval face,
slender build,
BREAK
light summer dress,
natural walking pose,
BREAK
sunny beach, blue ocean
```

### Negativeプロンプトを生成する

```python
negative_prompt = scene.negative_prompt(
    "low quality, blurry, bad anatomy"
)
```

基本Negativeの後ろに、採用されたoptionの `negative` がdimensionの定義順で1行ずつ追加されます。選ばれなかったoptionのNegativeは追加されません。

### 選択結果を確認する

```python
print(scene.summary())
```

出力例:

```python
{
    "woman.hair": "short_bob",
    "woman.face": "gentle",
    "woman.body": "athletic",
    "woman.outfit": "one_piece_swimsuit",
    "woman.pose": "walking",
    "location": "beach",
}
```

## 完全な実行例

実際の定義は `generate_random_image_prompt.py` を参照してください。

このスクリプトには次の制約が含まれています。

- 女性の固定値と属性を1つのblockとして定義
- 品質タグを固定文字列配列として定義
- 海辺では水着を要求
- 水着は海辺でのみ使用
- 室内では水着を禁止
- 岸辺を歩くポーズは海辺でのみ使用
- ソファのポーズはリビングでのみ使用
- ストレッチのポーズではアクティブウェアを要求

## 独自スクリプトを作る

`generate_random_image_prompt.py` をコピーして、dimensionと制約を変更するのが簡単です。

PyPromptGeneratorNodeは、カスタムノード直下のフォルダを次の優先順位で自動的にimport検索パスへ追加します。

1. `scripts/`
2. `sample_scripts/`

そのため、同じフォルダの `prompt_cdk.py` を通常のimport文で読み込めます。

```python
from prompt_cdk import PromptProgram, option
```

`scripts/` と `sample_scripts/` に同名のモジュールがある場合は、個人用の `scripts/` が優先されます。

`prompt_cdk.py` の編集をComfyUIの再起動なしで反映したい場合は、実行例のように `importlib.reload()` を使用してください。

## エラー

### No valid prompt combinations

すべての組み合わせが制約により除外された場合に発生します。

```text
ValueError: No valid prompt combinations for CharacterPortrait
```

矛盾する制約がないか、要求されたkeyまたはtagを持つoptionが存在するか確認してください。

### `__import__ not found`

ComfyUIが制限付き実行環境の旧バージョンを読み込んでいます。ブラウザだけでなく、ComfyUIプロセスを完全に停止して再起動してください。

### `No module named 'prompt_cdk'`

次を確認してください。

- `prompt_cdk.py` と実行スクリプトが同じ `sample_scripts` フォルダにある
- 実行スクリプトに上記のbootstrap処理がある
- `base_path` が正しい

## パフォーマンス

`synth()` は、全dimensionの直積から制約を満たす組み合わせを列挙します。

通常のプロンプト定義では十分高速ですが、dimensionやoptionを大量に追加すると組み合わせ数が急増します。

例:

```text
髪型10 × 顔10 × 服装20 × ポーズ20 × 場所20 = 800,000通り
```

大規模な定義では、候補数を減らすか、用途ごとに複数の`PromptProgram`へ分割してください。

## セキュリティ

これらのスクリプトはサンドボックス化されていません。ComfyUIプロセスと同じ権限で、ファイル、ネットワーク、プロセス、環境変数などへアクセスできます。

信頼できないスクリプトやワークフローは実行しないでください。

## Git管理

`sample_scripts/` はGit管理対象です。サンプルと `prompt_cdk.py` を同じフォルダ構成のまま配布してください。
