うん、そのやり方なら、**「一発で `/xxx` → `/yyy`」と命令するより、エージェントに移行プロジェクトのルールを覚えさせて、画面単位で順番に移植させる**のがかなり重要です。

 10万行規模なら、個人的には **Copilot Pro+ か Max + VS CodeのAgent mode** を前提にします。現在のGitHubの料金体系では、Proは月$10・AI Credits $15、Pro+は月$39・$70、Maxは月$100・$200です。Agent mode自体は有料プランで利用できます。 GitHub

 ## おすすめの進め方

 こんな構成にします。

```
/xxx                  ← 既存WinForms
  ├─ FormA.cs
  ├─ FormB.cs
  ├─ FormC.cs
  └─ ...

/yyy                  ← 新Vue3
  ├─ src/
  │   ├─ views/
  │   ├─ components/
  │   ├─ api/
  │   └─ ...
  ├─ package.json
  └─ ...

/.github/
  ├─ copilot-instructions.md
  ├─ instructions/
  │   └─ vue-migration.instructions.md
  └─ prompts/
      └─ migrate-screen.prompt.md
```

 GitHub自身も、リポジトリ全体のルールは `copilot-instructions.md`、特定ディレクトリ向けは `.instructions.md`、繰り返し使う作業は prompt file に分ける方法を案内しています。 GitHub Docs+1

---

 # ① 最初に「移植ルール」を作らせる

 いきなり

 > `/xxx`を`/yyy`に移植して

 はやらない方がいいです。

 まずAgentにこれを投げます。

```
このリポジトリの /xxx にある既存WinFormsアプリを、
/yyy に Vue 3 + TypeScript + Vuetify 3 で段階的に移植する。

まずコードを変更せず、以下を調査してほしい。

1. /xxx のプロジェクト構成
2. Form / UserControl の一覧
3. 各画面の依存関係
4. イベント処理
5. DB/APIアクセス
6. 共通コンポーネント
7. 画面間遷移
8. バリデーション
9. 権限・認証関連
10. グローバル状態
11. WinForms固有機能
12. 移植時にそのままVueへ変換できない部分

そのうえで、
「WinForms → Vue3/Vuetify3 移植マップ」
をMarkdownで作成して。

まだコード変更はしないで。
```

 **ここではコードを書かせない。**

 まずAIに10万行を読ませて、構造を理解させます。

---

 # ② 移行ルールを `copilot-instructions.md` に固定

 次に、

```
今調査した内容を元に、
.github/copilot-instructions.md
を作成して。

今後このリポジトリでWinFormsからVue3/Vuetify3へ
移植するときの共通ルールとして使う。

以下を必ず含める。

- Vue 3 Composition API
- TypeScript
- Vuetify 3
- コンポーネント設計
- API呼び出し方針
- 状態管理
- ルーティング
- バリデーション
- エラーハンドリング
- 命名規則
- 既存WinFormsとの対応関係
- 移植してはいけないもの
- テスト方針
- ビルド・lint・testの実行方法

1000行を超える巨大な指示にはせず、
必要最小限にまとめて。
```

 これを作らせます。

 GitHubも「指示は短く具体的に」「リポジトリ全体に適用するルールは `copilot-instructions.md` に入れる」という方向を推奨しています。 GitHub Docs+1

---

 # ③ ここが重要：「一画面ずつ移植」する

 10万行全部を一度に渡さない。

 例えば、

```
/xxx/CustomerForm.cs
/xxx/CustomerForm.Designer.cs
```

 を1画面目として、

```
/yyy/src/views/CustomerView.vue
```

 に移植する。

 Agentにはこう言います。

```
/xxx/CustomerForm.cs
/xxx/CustomerForm.Designer.cs
および、この画面が直接依存しているコードを調査してください。

この画面を /yyy に Vue3 + TypeScript + Vuetify3 で移植してください。

ただし、以下を厳守してください。

- 既存WinFormsコードは変更しない
- /yyy 配下だけ変更する
- 既存APIの仕様を勝手に変更しない
- 不明な仕様を推測して実装しない
- 推測が必要な箇所は TODO として記録する
- WinFormsのイベント処理をVueのComposition APIへ適切に変換する
- UIはVuetify3を使用する
- TypeScriptのanyを原則使用しない
- 既存画面の入力項目・ボタン・一覧・バリデーションを漏らさない
- 画面遷移も移植する
- 必要なAPI層、型、コンポーネントも作成する

実装後、

1. npm install
2. npm run lint
3. npm run type-check
4. npm run build
5. テスト

を実行して、エラーがあれば修正してください。

最後に、
「WinFormsの何がVueの何に移植されたか」
を一覧にしてください。
```

 このくらい具体的にした方がいいです。

 GitHubの公式ドキュメントでも、複雑なタスクは分割し、要求・制約・期待する結果を具体的にすることが推奨されています。 GitHub Docs

---

 # ④ さらに「調査 → 実装 → 検証」を分ける

 俺ならここをかなり重視します。

 ### Phase 1

```
調査だけして。
コード変更禁止。
```

 ↓

 ### Phase 2

```
実装計画を作って。
コード変更禁止。
```

 ↓

 ### Phase 3

```
計画に従って実装して。
```

 ↓

 ### Phase 4

```
テストして。
```

 ↓

 ### Phase 5

```
WinFormsとVueの差分を確認して。
漏れている機能を列挙して。
```

 ↓

 ### Phase 6

```
漏れている機能を修正して。
```

 このループです。

---

 # ⑤ 画面ごとにGit branchを切る

 例えば、

```
migration/customer
migration/order
migration/product
migration/invoice
```

 みたいにします。

 そして、

```
CustomerForm
↓
CustomerView.vue
↓
テスト
↓
レビュー
↓
merge
```

 という単位。

 **10万行を1つのAgentセッションで完成させようとしない**ことがかなり重要です。

---

 # ⑥ さらに「移植専用Agent」を作る

 ここまでやるとかなり楽になります。

 例えば `.github/agents/winforms-migrator.md` を作って、

```
# WinForms Migration Agent

あなたはWinFormsからVue3 + TypeScript + Vuetify3への
移行を専門とするエージェントです。

## Source

既存WinForms:
 /xxx

## Target

Vue:
 /yyy

## Rules

- Sourceは変更しない
- Targetのみ変更する
- Vue 3 Composition APIを使用
- TypeScriptを使用
- Vuetify 3を使用
- UI仕様を勝手に変更しない
- API仕様を勝手に変更しない
- 不明な仕様を推測しない
- 推測した場合はTODOにする
- anyを極力使わない
- 重複コードを作らない
- 共通処理は共通化する
- npm run lint
- npm run type-check
- npm run build
- testを実行する

## Migration Process

1. Sourceを調査
2. 依存関係を確認
3. 移植計画を作成
4. 実装
5. 型チェック
6. lint
7. build
8. test
9. WinFormsとの機能差分を確認
10. 結果を報告
```

 というAgentを作ります。

 CopilotではCustom Agentをリポジトリに定義できます。 GitHub Docs

---

 # ⑦ そうすると最終的にあなたの指示は短くなる

 理想はこれです。

```
CustomerFormを移植して。
```

 Agent側には、

```
WinForms Migration Agent
        ↓
/xxx/CustomerForm.cs
        ↓
依存関係解析
        ↓
/yyy/src/views/CustomerView.vue
        ↓
API
        ↓
components
        ↓
validation
        ↓
test
        ↓
build
        ↓
差分確認
```

 という流れを覚えさせる。

 つまり、**あなたが毎回長文プロンプトを書く必要をなくす**わけです。

---

 # ⑧ 10万行なら「画面」より先に共通部分を移植する

 ここはかなり重要です。

 例えばWinForms側に、

```
Common/
 ├─ MessageBox
 ├─ Validation
 ├─ DataGrid
 ├─ DatePicker
 ├─ ComboBox
 ├─ Permission
 ├─ Login
 ├─ UserContext
 └─ ApiClient
```

 みたいなのがあるなら、先にVue側へ作らせます。

```
/yyy/src/
 ├─ components/
 ├─ composables/
 ├─ services/
 ├─ stores/
 ├─ types/
 ├─ utils/
 └─ views/
```

 この土台ができてから、

```
FormA
FormB
FormC
...
```

 を移植する。

 そうしないとAgentが画面ごとに、

```
CustomerTable.vue
CustomerApi.ts
CustomerValidation.ts
CustomerDialog.vue
```

 みたいな似たものを大量に作ってしまいます。

---

 # ⑨ Copilotのプラン

 今回の用途なら、私はこう考えます。

 ### Pro

 小規模な検証なら十分。

 ただし10万行の大規模移行を**Agent中心でガンガン回す用途では、AI Creditsが足りなくなる可能性があります**。

 ### Pro+

 今回の用途なら、まずここを検討。

 月$39、月$70分のAI Creditsが含まれます。Proの4倍以上の利用枠とされています。 GitHub

 **10万行移行を数週間〜数か月かけてやるなら、まずPro+で始める**のが現実的だと思います。

 ### Max

 「人間はレビューだけして、Agentをかなり大量に回す」という使い方なら候補。

 月$100、月$200分のAI Creditsが含まれ、Pro+よりさらに利用枠が大きいです。 GitHub

---

 ## 俺ならこうする

 今回の条件なら、

```
GitHub Copilot Pro+
        │
        ▼
VS Code
        │
        ▼
Agent mode
        │
        ├── .github/copilot-instructions.md
        │
        ├── .github/instructions/
        │
        ├── .github/prompts/
        │
        └── .github/agents/
                    │
                    ▼
             Migration Agent
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
      /xxx                     /yyy
    WinForms                 Vue3
                              +
                           Vuetify3
```

 という形にします。

 そして、

 **「10万行全部移植して」**

 ではなく、

```
① 全体解析
② 移行ルール作成
③ Vue基盤作成
④ 共通部品移植
⑤ 1画面移植
⑥ テスト
⑦ 1画面移植
⑧ テスト
...
```

 と進めます。

 特に①〜④を最初にきっちりやることで、後半の大量の画面移植をかなり機械的にできます。

 もし実際にやるなら、次に **「WinForms 10万行 → Vue3/Vuetify3移行用の `.github/` 一式（`copilot-instructions.md`、`AGENTS.md`、Migration Agent、prompt）」をそのままコピペできる形**で作るのが一番実用的です。


基本的には、**「① 全体解析」でAgentが理解した内容が、そのまま次回のAgentセッションのコンテキストとして丸ごと残る、とは考えない方がいい**です。

 ただし、**次回も使える形に自分で残す**ことはできます。むしろ10万行規模なら、こちらを強くおすすめします。

 ### 一番いい方法

 ①の解析結果をAgentに**ファイルとして保存させる**。

 例えば、

```
/yyy
  └─ docs/
      ├─ migration-overview.md
      ├─ migration-map.md
      ├─ architecture.md
      ├─ screen-inventory.md
      ├─ dependency-map.md
      └─ migration-rules.md
```

 そして最初の指示をこうします。

```
/xxx のWinFormsアプリを全面的に解析してください。

ただしコード変更はしないでください。

解析結果を以下のファイルとして /yyy/docs/ に保存してください。

- migration-overview.md
  システム全体の概要

- screen-inventory.md
  全Form、UserControl、画面の一覧

- dependency-map.md
  各画面の依存関係

- architecture.md
  現在のアーキテクチャ

- migration-map.md
  WinFormsの各機能をVue3/Vuetify3の何に
  移植するかの対応表

- migration-rules.md
  今後の移植で守るべきルール

重要：
これらのドキュメントは、今後の移植作業でAgentが参照する
「プロジェクトの設計情報」として使用する。

推測した内容は推測であることを明記する。
```

 すると次回、

```
CustomerFormを移植して
```

 だけでも、Agentに

```
docs/migration-overview.md
docs/migration-map.md
docs/migration-rules.md
```

 を読ませてから作業させられます。

---

 ### さらに重要なのが `copilot-instructions.md`

 例えば、

```
.github/
└── copilot-instructions.md
```

 には、

```
# WinForms Migration Project

## Source

/xxx

## Target

/yyy

## Architecture Documentation

移行設計については以下を必ず参照する。

- /yyy/docs/migration-overview.md
- /yyy/docs/migration-map.md
- /yyy/docs/architecture.md
- /yyy/docs/migration-rules.md

## Migration Rules

- Vue 3 Composition API
- TypeScript
- Vuetify 3
- 既存WinFormsの仕様を維持
- /xxx は変更禁止
- 新規コードは /yyy に作成
- 不明な仕様を勝手に作らない
- 既存APIの仕様を変更しない
- 共通処理は再利用する
```

 としておく。

 こうすると\*\*「AIの記憶」に依存せず、Gitで管理されたプロジェクト知識\*\*になります。

---

 ### つまり

 イメージとしては、

```
          最初のAgent
               │
               ▼
       /xxx 全体を解析
               │
               ▼
       ┌───────────────┐
       │ docs/*.md     │
       │               │
       │ システム構造   │
       │ 画面一覧       │
       │ 依存関係       │
       │ 移行ルール     │
       └───────────────┘
               │
               ▼
          Git commit
               │
      ┌────────┴────────┐
      ▼                 ▼
 次のAgent          次のAgent
 CustomerForm       OrderForm
      │                 │
      └───────┬─────────┘
              ▼
          docsを読む
              │
              ▼
       Vue3/Vuetify3実装
```

 です。

 **10万行ならこの方式がかなり重要です。**

 「前回のAgentが覚えているはず」にすると、セッションが変わったときに品質がブレます。一方、`docs/` に解析結果を残してGit管理すれば、**別のAgent、別の日、別のPCでも同じ設計情報を参照できます。**

 さらに一歩進めるなら、`screen-inventory.md` に

```
Form001 → CustomerView.vue → 完了
Form002 → OrderView.vue    → 移行中
Form003 → ProductView.vue  → 未着手
```

 のような**移行進捗表**まで持たせると、10万行の移行プロジェクトをAgentにかなり自律的に進めさせられます。


★プロンプト
もし実際にやるなら、次に 「WinForms 10万行 → Vue3/Vuetify3移行用の .github/ 一式（copilot-instructions.md、AGENTS.md、Migration Agent、prompt）」をそのままコピペできる形で作るのが一番実用的です

やってみましょう。10万行規模なら、\*\*「解析 → 計画 → 1画面移植 → 検証 → 差分修正」\*\*をAgentに徹底させる構成にします。

 なお、`AGENTS.md` と `copilot-instructions.md` は役割が重複するので、今回は\*\*Copilot向けの正式な指示は `copilot-instructions.md`、汎用的なプロジェクトルールは `AGENTS.md`\*\*に分けます。

 以下をそのまま配置できます。

 ## 1\. ディレクトリ構成

```
.github/
├── copilot-instructions.md
├── agents/
│   └── winforms-migrator.agent.md
└── prompts/
    ├── analyze-winforms.prompt.md
    ├── migrate-screen.prompt.md
    └── verify-migration.prompt.md

AGENTS.md

/xxx/                         # 既存WinForms
/yyy/                         # 新Vue3 + Vuetify3
    └── docs/
        ├── migration-overview.md
        ├── screen-inventory.md
        ├── dependency-map.md
        ├── architecture.md
        ├── migration-map.md
        ├── migration-rules.md
        └── migration-progress.md
```

 最初は `/yyy/docs/` が存在しなくても構いません。最初の解析Agentに作らせます。

---

 # 2\. `.github/copilot-instructions.md`

````
# WinForms to Vue3/Vuetify3 Migration

## Project

This repository contains a legacy WinForms application and its
replacement Vue 3 application.

Source application:

- `/xxx`

Target application:

- `/yyy`

The goal is to migrate the existing WinForms application to:

- Vue 3
- TypeScript
- Vuetify 3
- Composition API

---

## Critical Rules

### Source code

`/xxx` is the legacy source of truth.

Unless explicitly requested:

- DO NOT modify files under `/xxx`
- DO NOT delete files under `/xxx`
- DO NOT rewrite the existing WinForms application
- DO NOT change existing API contracts

The migration must be implemented under `/yyy`.

---

## Functional Preservation

The migration must preserve existing behavior unless the user explicitly
requests a behavior change.

Pay particular attention to:

- screen layout
- input fields
- buttons
- grids
- dialogs
- validation
- error handling
- business rules
- calculations
- filtering
- sorting
- pagination
- keyboard behavior
- screen navigation
- permissions
- API calls
- database-related behavior
- confirmation dialogs
- loading states

Do not remove functionality merely because it appears unused.

---

## Vue Rules

Use:

- Vue 3
- Composition API
- `<script setup>`
- TypeScript
- Vuetify 3

Prefer:

- composables for reusable logic
- services for API communication
- typed models/interfaces
- reusable components
- centralized validation
- centralized error handling

Avoid:

- Options API
- unnecessary global state
- duplicated business logic
- `any`
- large monolithic Vue components

---

## Vuetify Rules

Use Vuetify 3 components where appropriate.

Prefer:

- `v-form`
- `v-text-field`
- `v-select`
- `v-autocomplete`
- `v-data-table`
- `v-dialog`
- `v-btn`
- `v-alert`
- `v-card`
- `v-tabs`
- `v-container`
- `v-row`
- `v-col`

Do not recreate standard Vuetify functionality with custom HTML unless
there is a specific reason.

---

## Architecture

Before creating a new shared component or service:

1. Search `/yyy` for an existing implementation.
2. Reuse it if appropriate.
3. Only create a new implementation when necessary.

Do not create multiple implementations of the same concept.

---

## Existing Migration Documentation

Before implementing migration work, inspect:

- `/yyy/docs/migration-overview.md`
- `/yyy/docs/screen-inventory.md`
- `/yyy/docs/dependency-map.md`
- `/yyy/docs/architecture.md`
- `/yyy/docs/migration-map.md`
- `/yyy/docs/migration-rules.md`
- `/yyy/docs/migration-progress.md`

If these files do not exist, create them when performing the initial
analysis.

---

## Unknown Behavior

Never silently invent business rules.

If behavior cannot be determined from the source code:

1. Search related code.
2. Search related forms/classes.
3. Search API definitions.
4. Search configuration.
5. Search tests.
6. Search documentation.

If the behavior is still unclear:

- implement the safest reasonable structure only when necessary
- add a `TODO`
- document the uncertainty in the migration report

Do not pretend uncertain behavior is confirmed behavior.

---

## Dependency Analysis

When migrating a screen, inspect:

- `.cs`
- `.Designer.cs`
- inherited classes
- base forms
- UserControls
- referenced services
- referenced models
- API clients
- repositories
- validation
- configuration
- resources
- event handlers
- navigation
- dialogs
- related screens

Do not migrate only the visible `.Designer.cs` layout.

---

## Migration Boundary

For each screen, determine:

- source Form/UserControl
- direct dependencies
- indirect dependencies
- APIs
- models
- shared components
- navigation
- business logic

Do not blindly copy all dependencies into the new application.

Determine whether each dependency belongs in:

- component
- composable
- service
- store
- utility
- type/model
- API layer

---

## Validation

After implementation, run the available project checks.

Prefer:

```bash
npm run lint
npm run type-check
npm run build
npm run test
````

 If one of these scripts does not exist:

 - do not invent a command
- inspect `package.json`
- use the project's actual scripts

 Fix errors caused by the migration.

---

 ## Scope Control

 When asked to migrate one screen:

 - migrate that screen
- migrate required dependencies
- do not arbitrarily migrate unrelated screens
- do not perform a repository-wide refactor

 If a shared refactor is genuinely required, explain it before making\
 large unrelated changes.

---

 ## Completion Criteria

 A screen migration is not complete merely because the Vue file exists.

 Before reporting completion:

 1. Source behavior was inspected.
2. Dependencies were inspected.
3. UI was implemented.
4. Business logic was implemented.
5. API integration was implemented.
6. Validation was implemented.
7. Navigation was implemented where applicable.
8. Type checking passes.
9. Lint passes.
10. Build passes.
11. Tests pass when available.
12. Remaining differences are documented.

---

 ## Reporting

 At the end of every migration, report:

 ### Migrated

 List the source files and target files.

 ### Functionality

 List the functionality that was migrated.

 ### Dependencies

 List important dependencies that were reused or created.

 ### Verification

 Report:

 - lint
- type-check
- build
- test

 ### TODO

 List anything that could not be confirmed.

 ### Differences

 List known differences between WinForms and Vue.

````

---

# 3. `AGENTS.md`

これはCopilot専用というより、**このリポジトリでAI Agentが作業するときのプロジェクトルール**として置きます。

```md
# AGENTS.md

## Project Goal

Migrate the legacy WinForms application in `/xxx`
to the Vue 3 + TypeScript + Vuetify 3 application in `/yyy`.

---

## Source of Truth

The legacy application is located at:

`/xxx`

The new application is located at:

`/yyy`

The WinForms implementation is the primary reference for existing
functionality unless explicitly stated otherwise.

---

## Never Modify

Do not modify `/xxx` during normal migration work.

---

## Migration Documentation

Migration knowledge is stored under:

`/yyy/docs/`

Important documents:

- `migration-overview.md`
- `screen-inventory.md`
- `dependency-map.md`
- `architecture.md`
- `migration-map.md`
- `migration-rules.md`
- `migration-progress.md`

Read the relevant documents before implementing migration work.

---

## Development Principles

1. Preserve existing behavior.
2. Prefer reuse over duplication.
3. Keep business logic separate from UI.
4. Use TypeScript types.
5. Use Vue 3 Composition API.
6. Use Vuetify 3.
7. Keep components reasonably small.
8. Do not introduce unnecessary dependencies.
9. Do not silently change API contracts.
10. Do not invent undocumented business rules.

---

## Migration Strategy

Migration is performed incrementally.

Preferred order:

1. Repository analysis
2. Architecture definition
3. Shared infrastructure
4. Shared components
5. Individual screens
6. Verification
7. Regression testing

Do not attempt to migrate the entire legacy application in a single
operation.

---

## Screen Migration

For each screen:

1. Identify the source Form/UserControl.
2. Read the `.cs` file.
3. Read the `.Designer.cs` file.
4. Inspect base classes.
5. Inspect event handlers.
6. Inspect API calls.
7. Inspect models.
8. Inspect validation.
9. Inspect navigation.
10. Inspect related shared functionality.
11. Create a migration plan.
12. Implement.
13. Verify.
14. Update migration progress.

---

## Uncertainty

Never hide uncertainty.

When behavior cannot be determined:

- search further
- document the uncertainty
- add TODO if appropriate

Do not invent business behavior.

---

## Verification

A migration should be considered complete only after available:

- lint
- type-check
- build
- tests

have been executed and relevant errors have been addressed.
````

---

 # 4\. `winforms-migrator.agent.md`

 ここが**実際に使うAgent本体**です。

````
---
name: winforms-migrator
description: Migrates WinForms screens and functionality from /xxx to Vue 3 + TypeScript + Vuetify 3 in /yyy.
---

# WinForms Migration Agent

You are a senior software engineer specializing in
legacy WinForms modernization.

Your job is to migrate functionality from:

`/xxx`

to:

`/yyy`

using:

- Vue 3
- TypeScript
- Composition API
- Vuetify 3

---

# IMPORTANT

Do not modify `/xxx` unless the user explicitly requests it.

All migration implementation should be performed under `/yyy`.

---

# Before Starting

Read:

- `AGENTS.md`
- `.github/copilot-instructions.md`

Then inspect the migration documentation under:

`/yyy/docs/`

If migration documentation does not exist, perform repository analysis
before implementing screens.

---

# Migration Process

For every requested migration, follow this sequence.

## Step 1 — Identify

Identify:

- Form
- UserControl
- base class
- related classes
- Designer file
- models
- services
- API calls
- validation
- navigation
- dialogs
- shared controls

---

## Step 2 — Analyze

Understand:

- UI structure
- state
- events
- business rules
- API behavior
- validation
- error handling
- navigation
- permissions
- lifecycle

Do not start implementation until the relevant source has been
understood.

---

## Step 3 — Plan

Create a concise migration plan.

Map:

WinForms:

`Form / UserControl / event / service`

to:

Vue:

`View / Component / Composable / Service / Store`

---

## Step 4 — Implement

Implement the migration in `/yyy`.

Use:

- Vue 3
- `<script setup>`
- TypeScript
- Vuetify 3

Reuse existing `/yyy` components and services whenever possible.

---

## Step 5 — Verify

Run the project's available checks.

Inspect `package.json` first.

Prefer:

```bash
npm run lint
npm run type-check
npm run build
npm run test
````

 Fix migration-related errors.

---

 ## Step 6 — Compare

 Compare the migrated implementation with the original WinForms\
 implementation.

 Check:

 - fields
- buttons
- tables
- dialogs
- validation
- events
- API calls
- business logic
- navigation
- error handling
- permissions
- loading states

 Identify missing behavior.

---

 ## Step 7 — Update Documentation

 Update:

 `/yyy/docs/migration-progress.md`

 with the migration status.

 If important architectural information was discovered, update the\
 appropriate documentation file.

---

 # Scope Rules

 If the user asks:

 "migrate CustomerForm"

 do not migrate the entire application.

 Only migrate:

 - CustomerForm
- required dependencies
- required shared infrastructure

 Avoid unrelated refactoring.

---

 # Safety Rules

 Never:

 - delete the original WinForms code
- modify unrelated screens
- change API contracts without explicit instruction
- invent business rules
- replace existing functionality with placeholders
- report success when build/type-check is failing

---

 # Final Response

 After migration, report:

 ## Migrated

 Source files and target files.

 ## Functionality

 What was migrated.

 ## Reused

 Existing Vue components/services that were reused.

 ## Created

 New components/services/types.

 ## Verification

 Results of:

 - lint
- type-check
- build
- test

 ## Remaining Issues

 Anything unresolved.

 ## TODO

 Any behavior that could not be confirmed.

````

---

# 5. 最初に一度だけ実行する解析Prompt

`.github/prompts/analyze-winforms.prompt.md`

```md
---
name: analyze-winforms
description: Analyze the legacy WinForms application and create migration documentation.
---

Analyze the WinForms application under:

`/xxx`

The target Vue application is:

`/yyy`

Do not modify `/xxx`.

Do not implement Vue screens yet.

Create or update:

`/yyy/docs/`

with:

- `migration-overview.md`
- `screen-inventory.md`
- `dependency-map.md`
- `architecture.md`
- `migration-map.md`
- `migration-rules.md`
- `migration-progress.md`

## migration-overview.md

Describe:

- application purpose
- major modules
- architecture
- important technologies
- major external dependencies

## screen-inventory.md

Create a complete inventory of:

- Forms
- UserControls
- dialogs
- major screens

For each item include:

- source path
- class name
- purpose
- major dependencies
- migration status

## dependency-map.md

Document important dependencies between:

- Forms
- UserControls
- services
- models
- APIs
- shared components

## architecture.md

Describe the existing WinForms architecture and map it to the
planned Vue architecture.

## migration-map.md

Create a mapping such as:

WinForms Form
→ Vue View

WinForms UserControl
→ Vue Component

event handler
→ Vue event/composable

service
→ API service

global state
→ appropriate Vue state mechanism

## migration-rules.md

Document important discoveries and rules that future migration agents
must follow.

## migration-progress.md

Create a migration checklist for all identified screens.

Use statuses:

- NOT_STARTED
- ANALYZING
- IN_PROGRESS
- VERIFYING
- COMPLETED
- BLOCKED

Do not invent behavior.

Mark uncertain information explicitly.

At the end, summarize the number of:

- Forms
- UserControls
- services
- major modules
- APIs

found.
````

---

 # 6\. 画面移植Prompt

 `.github/prompts/migrate-screen.prompt.md`

```
---
name: migrate-screen
description: Migrate a specific WinForms screen to Vue 3 + Vuetify 3.
---

Migrate the specified WinForms screen from `/xxx` to `/yyy`.

Before implementation:

1. Read `AGENTS.md`.
2. Read `.github/copilot-instructions.md`.
3. Read relevant files under `/yyy/docs/`.
4. Inspect the complete source implementation.
5. Inspect dependencies.
6. Inspect related screens and shared components.

Do not modify `/xxx`.

## Source

The user will provide the Form or UserControl to migrate.

## Target

Create the appropriate Vue implementation under `/yyy`.

Use:

- Vue 3
- TypeScript
- Composition API
- `<script setup>`
- Vuetify 3

## Preserve

Preserve:

- UI functionality
- validation
- business rules
- API calls
- navigation
- error handling
- loading behavior
- permissions
- dialogs
- table behavior

## Reuse

Before creating components/services:

1. Search `/yyy`.
2. Reuse existing implementations where appropriate.
3. Avoid duplication.

## Verification

After implementation:

1. Run lint.
2. Run type-check.
3. Run build.
4. Run tests if available.
5. Fix errors caused by the migration.
6. Compare the result with the original WinForms source.

## Documentation

Update:

`/yyy/docs/migration-progress.md`

Report:

- migrated files
- functionality
- reused components
- new components
- verification results
- TODOs
- known differences
```

---

 # 7\. 検証用Prompt

 `.github/prompts/verify-migration.prompt.md`

```
---
name: verify-migration
description: Compare a migrated Vue screen against its original WinForms implementation.
---

Verify the specified migrated screen.

Source:

`/xxx`

Target:

`/yyy`

Do not modify `/xxx`.

Inspect both implementations.

Compare:

- UI controls
- fields
- labels
- default values
- validation
- button behavior
- events
- API calls
- business rules
- dialogs
- navigation
- permissions
- loading states
- error handling
- table behavior
- filtering
- sorting
- pagination

Create a verification report.

Classify differences as:

- MATCH
- DIFFERENCE
- MISSING
- UNKNOWN

Do not assume UNKNOWN behavior is correct.

If a difference is clearly an implementation defect,
fix it in `/yyy`.

After fixes run the available:

- lint
- type-check
- build
- test

Update `/yyy/docs/migration-progress.md`.
```

---

 # 8\. 実際の使い方

 ここまで作ったら、最初は**いきなり移植しません**。

 Copilot Chatで `winforms-migrator` Agentを選択して、

```
/xxx を解析して移行ドキュメントを作成して。
コード変更はしないで。
```

 とします。

 あるいは `analyze-winforms` promptを使います。

 すると、

```
/yyy/docs/

migration-overview.md
screen-inventory.md
dependency-map.md
architecture.md
migration-map.md
migration-rules.md
migration-progress.md
```

 ができます。

---

 ## その後が本番

 Agentを `winforms-migrator` にして、

```
CustomerFormを移植して
```

 これだけでいいです。

 Agentは、

```
CustomerForm.cs
CustomerForm.Designer.cs
       ↓
関連UserControl
       ↓
Service
       ↓
API
       ↓
Model
       ↓
既存Vueコンポーネント
       ↓
Vue3 + Vuetify3
       ↓
lint
       ↓
type-check
       ↓
build
       ↓
差分確認
```

 という流れで動くようにします。

---

 ## そして重要なのが「進捗表」

 `migration-progress.md` は例えばこうなります。

```
# Migration Progress

| Source | Target | Status |
|---|---|---|
| CustomerForm | CustomerView.vue | COMPLETED |
| OrderForm | OrderView.vue | IN_PROGRESS |
| ProductForm | ProductView.vue | NOT_STARTED |
| InvoiceForm | InvoiceView.vue | NOT_STARTED |
| LoginForm | LoginView.vue | COMPLETED |
```

 なので、数百画面あっても、

```
「次に未移行の画面を1つ移植して」
```

 という指示ができます。

---

 ## さらに俺なら1つ追加する

 **「勝手に10万行を全部読み直さない」仕組み**も入れます。

 Agentの指示に、

```
Before reading large amounts of source code:

1. Check migration documentation.
2. Identify the specific screen.
3. Read only the source files relevant to that screen.
4. Expand the scope only when dependency analysis requires it.

Do not repeatedly scan the entire `/xxx` repository for every screen.
```

 を追加します。

 これが**Copilot Credits節約にもかなり重要**です。

 最初に全体構造をドキュメント化して、その後は

```
全体解析
    ↓
docsに保存
    ↓
CustomerFormだけ読む
    ↓
移植
    ↓
OrderFormだけ読む
    ↓
移植
    ↓
ProductFormだけ読む
    ↓
移植
```

 とする。

 \*\*「AIの記憶に頼る」のではなく、「Git管理された設計書をAIの長期記憶にする」\*\*という考え方です。

 この構成なら、あなたが実際に毎回入力するのは最終的にかなりシンプルにできます。

```
Agent: winforms-migrator

CustomerFormを移植して
```

 →

```
Agent:
調査
↓
実装
↓
テスト
↓
差分確認
↓
migration-progress.md更新
```

 という運用です。

