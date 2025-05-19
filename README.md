# ホットペッパービューティー スクレイピングツール

## 概要

このツールは、ホットペッパービューティーのウェブサイトから美容室の情報を効率的にスクレイピングするためのPythonアプリケーションです。以前のバージョンから大幅にモジュール化され、機能が拡張・改善されました。エリアごとの美容室リストの収集、詳細情報のスクレイピング、並列処理による高速化、Streamlit WebアプリケーションによるGUI操作、そして詳細なログ出力とエラーハンドリングが特徴です。

このツールは以下の2つの実行モードをサポートしています。

1.  **Streamlit Webアプリケーション (`app.py`)**: Webブラウザから直感的に操作できるGUIを提供します。エリア選択、検索フィルター、スクレイピングの開始・停止、進捗状況のリアルタイム表示、スクレイピング結果の確認、Excelファイルダウンロードなどが可能です。GUIを通じて、よりユーザーフレンドリーな操作性を実現しています。

2.  **コマンドラインアプリケーション (`main.py`)**: コマンドラインからシンプルにスクレイピングを実行できます。エリアページのURLを直接入力するだけで、簡単にスクレイピングを開始できます。自動化スクリプトやバッチ処理に組み込むのに適しています。

## ファイル構成

```
├── .streamlit/              # Streamlit設定ディレクトリ
│   └── secrets.toml.example # secrets.toml のサンプルファイル
├── area.csv                 # スクレイピング対象エリアのリスト (CSVファイル)
├── app.py                   # Streamlit Webアプリケーションのメインスクリプト
├── app_action_handlers.py    # Streamlitアプリケーションのアクションハンドラーモジュール
├── app_area_handler.py      # Streamlitアプリケーションのエリアデータ処理モジュール
├── app_progress_handler.py  # Streamlitアプリケーションの進捗処理モジュール
├── app_state_manager.py     # Streamlitアプリケーションの状態管理モジュール
├── app_ui.py                # StreamlitアプリケーションのUIコンポーネントモジュール
├── area_manager.py          # エリアデータ管理モジュール (CSVファイルの読み書き、バリデーション)
├── area_processor.py        # エリアデータ (area.csv) を処理し、サロン数を取得するスクリプト
├── config.py                # 設定ファイル (リクエスト設定、リトライ設定、セレクタなど)
├── excel_exporter.py        # スクレイピングデータをExcelファイルに出力するモジュール
├── http_client.py           # リトライ機能付きHTTPクライアントモジュール
├── logging_setup.py         # ロギング設定モジュール
├── main.py                  # コマンドラインアプリケーションのメインスクリプト
├── parallel_scraper.py      # 並列スクレイピング処理モジュール
├── requirements.txt         # 必要なPythonライブラリのリスト
├── scraper.py               # 個別のWebページから情報をスクレイピングするモジュール
├── url_utils.py             # URL処理ユーティリティモジュール
└── README.md                # このREADMEファイル
```

## 実行に必要な環境

*   **Python**: 3.8以上
*   **pip**: Pythonのパッケージ管理システム

### 必要なPythonライブラリ

必要なライブラリは `requirements.txt` にリストされています。以下のコマンドで一括インストールできます。

```bash
pip install -r requirements.txt
```

### エリアリスト CSVファイル (`area.csv`) の準備

スクレイピング対象のエリアリストを `area.csv` ファイルにUTF-8形式で用意する必要があります。`area.csv` のフォーマットは以下の通りです。

```csv
prefecture,area,url,estimated_salons,add_button_clicked
青森県,五所川原,https://beauty.hotpepper.jp/svcSE/macEF/salon/sacX495/,21,
熊本県,熊本,https://beauty.hotpepper.jp/svcSG/macGE/salon/,748,
埼玉県,練馬・ひばりヶ丘・所沢・飯能・狭山,https://beauty.hotpepper.jp/svcSA/macAS/salon/,764,
...
```

*   `prefecture`: 都道府県名
*   `area`: エリア名
*   `url`: ホットペッパービューティーのエリアページのURL (例: `https://beauty.hotpepper.jp/svcSA/macAA/salon/`)
*   `estimated_salons`: (オプション) 推定サロン数。`area_processor.py` を実行すると自動的に入力されます。
*   `add_button_clicked`: (内部使用) GUIからエリア追加時に使用するフラグ。手動で編集しないでください。

#### `area_processor.py` の実行 (サロン数自動取得)

`area.csv` にサロン数を自動的に入力したい場合、または既存のサロン数を更新したい場合は、`area_processor.py` を実行します。

```bash
python area_processor.py
```

実行後、`area_structured.csv` が生成されます。このファイルにサロン数が追記されています。`area.csv` を `area_structured.csv` で**上書き**してください。

**注意**: `area_processor.py` はウェブサイトにアクセスしてサロン数を取得するため、実行に時間がかかります。また、ウェブサイトの構造変更により正常に動作しなくなる可能性があります。処理内容は以下の通りです。

1.  `area.csv` を読み込みます。
2.  各エリアのURLにアクセスし、HTMLを解析してサロン数を抽出します。
3.  サロン数を `estimated_salons` 列に書き込みます (既存の `estimated_salons` は上書きされます)。
4.  結果を `area_structured.csv` に保存します。
5.  サロン数の統計情報 (合計、平均、最大、サロン数0のエリア数) をコンソールに表示します。

## 実行方法

### 1. Streamlit Webアプリケーションの実行 (`app.py`)

以下のコマンドでStreamlitアプリケーションを起動します。

```bash
streamlit run app.py
```

Webブラウザが自動的に開き、アプリケーションが起動します。

**Streamlitアプリケーションの使い方**:

1.  **サイドバー**:
    *   **設定**:
        *   **エリアを選択 (エクスパンダー)**:
            *   **都道府県を選択**: ドロップダウンメニューから都道府県を選択します。選択した都道府県の統計情報 (エリア数、総サロン数) が表示されます。
            *   **エリアを選択**: ドロップダウンメニューからエリアを選択します。選択したエリアの詳細情報 (サロン数) が表示されます。
        *   **検索フィルター (エクスパンダー)**:
            *   **エリア名で検索**: エリア名を入力して検索し、表示するエリアを絞り込むことができます。検索クエリを入力すると、リアルタイムで結果がフィルタリングされます。
        *   **統計情報 (エクスパンダー)**:
            *   **全体**: 全エリアの統計情報 (都道府県数、エリア総数、サロン総数) が表示されます。
            *   **検索結果**: 検索結果に該当するエリアの統計情報 (該当都道府県数、該当エリア数、該当サロン数) が表示されます。サロン数トップ5エリアも確認できます。
        *   **アプリを終了 (ボタン)**: アプリケーションを終了します。
2.  **メインエリア**:
    *   **ヘッダー**: アプリケーションのタイトル (`HPBスクレイピングアプリ`) とアイコンが表示されます。
    *   **使い方**: アプリケーションの基本的な使い方がステップ形式で説明されています。
    *   **ボタン**:
        *   **スクレイピング開始 (プライマリーボタン)**: 選択したエリアのスクレイピングを開始します。処理中はボタンが無効になります。
        *   **処理を中断 (セカンダリーボタン)**: 実行中のスクレイピングを中断します。処理中でない場合や、すでに停止処理中の場合は無効になります。
    *   **進捗表示**:
        *   **プログレスバー**: スクレイピングの全体的な進捗状況を視覚的に表示します。
        *   **ステータスメッセージ**: 現在の処理状況や、エラー、警告、成功などのメッセージをリアルタイムに表示します。
        *   **メトリクス**: スクレイピングの詳細な進捗情報を数値で表示します。
            *   **処理済み**: 処理済みのエリア数 / 全エリア数
            *   **成功**: スクレイピング成功件数
            *   **エラー**: スクレイピング失敗件数
            *   **進捗率**: 現在の進捗率 (%)
            *   **平均処理時間**: 1エリアあたりの平均処理時間 (秒/件)
            *   **残り時間**: 処理完了までの推定残り時間
    *   **スクレイピング結果**: スクレイピングが完了すると、収集されたサロンデータが表形式 (Streamlit DataFrame) で表示されます。
        *   **表示項目**: サロン名、電話番号、住所、スタッフ数、サロンURL
        *   **機能**: 列ヘッダーによるソート、ページネーション、レスポンシブ表示、URL列のリンク化
    *   **基本統計情報**: スクレイピング結果の基本統計情報が表示されます。
        *   **総サロン数**: スクレイピングで取得したサロンの総数
        *   **平均スタッフ数**: 取得したサロンの平均スタッフ数
        *   **データ取得成功率**: スクレイピング成功率 (%)
    *   **Excelファイルをダウンロード (ダウンロードボタン)**: スクレイピング結果をExcelファイル (`.xlsx`) としてダウンロードできます。ファイル名には、都道府県名、エリア名、実行日時が含まれます。`output` ディレクトリにも自動的に保存されます。
    *   **完了メッセージ**: スクレイピング完了後に、対象エリア、取得件数を含む完了メッセージが表示されます。

**オプション: パスワード認証の設定**

アプリケーションにパスワード認証を追加したい場合は、プロジェクトルートに `.streamlit` ディレクトリが自動で作成されます（存在しない場合）。その中に `secrets.toml` ファイルを配置してください（`.streamlit/secrets.toml.example`をコピーして作成できます）。
`secrets.toml` には以下のように記述します。

```toml
password = "あなたのパスワード"
```
これにより、アプリケーション起動時にパスワード入力が求められるようになります。
実際の `secrets.toml` ファイルは `.gitignore` によりGitの管理対象外となっているため、リポジトリに誤ってパスワードをコミットする心配はありません。

### 2. コマンドラインアプリケーションの実行 (`main.py`)

以下のコマンドでコマンドラインアプリケーションを実行します。

```bash
python main.py
```

**コマンドラインアプリケーションの使い方**:

1.  アプリケーション起動後、プロンプト `エリアページURLを入力してください: ` が表示されるので、スクレイピングしたいホットペッパービューティーのエリアページのURL (例: `https://beauty.hotpepper.jp/svcSA/macAA/salon/`) を入力してEnterキーを押します。
2.  スクレイピングが開始され、進捗状況 (サロンURL収集数、サロン情報取得数、成功/エラー件数など) がコンソールにリアルタイムに表示されます。
3.  スクレイピング完了後、`output` ディレクトリにExcelファイル (`hotpepper_beauty_salons_YYYYMMDDHHMMSS.xlsx`) が生成され、保存パスがコンソールに表示されます。

## モジュールの詳細

*   **`app.py`**:
    *   Streamlit Webアプリケーションのエントリーポイント。
    *   セッション状態の初期化、UIの構築、スクレイピング処理の制御、イベントハンドリング (ボタンクリック、検索クエリ変更など) を行います。
    *   オプションで `.streamlit/secrets.toml` ファイルを用いたパスワード認証機能を提供します (`check_password` 関数)。
    *   `app_ui.py`, `app_state_manager.py`, `app_progress_handler.py`, `app_action_handlers.py`, `app_area_handler.py` などのモジュールを連携させ、アプリケーション全体の機能を統合します。
    *   スクレイピング実行、進捗表示、エラーハンドリング、Excel出力、結果表示などの主要な処理フローを実装します。
*   **`app_action_handlers.py`**:
    *   StreamlitアプリケーションのUIアクション (ボタンクリック、検索クエリ変更など) を処理するハンドラー関数を定義します。
    *   `handle_start`: 「スクレイピング開始」ボタンクリック時の処理 (スクレイピング開始、状態更新)。
    *   `handle_stop`: 「処理を中断」ボタンクリック時の処理 (スクレイピング停止、状態更新)。
    *   `on_search_change`: 検索入力フィールドの変更時の処理 (フィルター状態更新)。
    *   状態管理モジュール (`app_state_manager.py`) の `update_processing_state`, `update_filter_state` 関数を呼び出し、アプリケーションの状態を更新します。
    *   進捗処理モジュール (`app_progress_handler.py`) の `progress_callback` 関数をコールバック関数として使用します。
*   **`app_area_handler.py`**:
    *   Streamlitアプリケーションのエリアデータ処理 (読み込み、フィルタリング、新規エリア追加) を行う関数を定義します。
    *   `load_area_data`: CSVファイル (`area.csv`) からエリアデータを読み込み、構造化された形式 (`Dict[str, Any]`) で返します。都道府県ごとのエリア情報、都道府県リスト、総エリア数、総サロン数などを算出します。
    *   `filter_areas`: エリアデータを検索クエリに基づいてフィルタリングします。検索クエリがエリア名に含まれるエリアのみを抽出します。
    *   `handle_add_new_area`: 新規エリア追加処理を行います。UIから入力された新規エリアデータを `area_manager.py` の `AreaManager` クラスを使用して `area.csv` に追加します。成功・失敗メッセージをStreamlit UIに表示し、成功時はページをリロードします。
    *   `process_area_data_and_render_selector`: エリアデータロード、フィルタリング、エリアセレクターUI (`app_ui.py` の `display_area_selector`) のレンダリング、新規エリア追加処理をまとめて行います。Streamlitアプリケーション (`app.py`) から呼び出され、エリア選択UIとデータ処理を統合します。
    *   UIコンポーネントモジュール (`app_ui.py`) の `display_area_selector` 関数を呼び出し、エリア選択UIをレンダリングします。
    *   エリア管理モジュール (`area_manager.py`) の `AreaManager` クラスを利用してエリアデータの読み書き、バリデーション、新規エリア追加を行います。
*   **`app_progress_handler.py`**:
    *   Streamlitアプリケーションのスクレイピング進捗処理を管理する関数を定義します。
    *   `progress_callback`: スクレイピング処理からの進捗コールバック関数です。並列スクレイパー (`parallel_scraper.py`) から定期的に呼び出され、進捗情報をセッション状態 (`app_state_manager.py`) に保存し、UI (`app_ui.py`) を更新します。プログレスバー、ステータスメッセージ、進捗メトリクスの更新を行います。
    *   `format_elapsed_time`: 経過秒数を人間が読みやすい形式 (例: "1時間30分") に変換します。進捗メトリクス (`app_ui.py` の `display_progress_metrics`) で残り時間や経過時間を表示する際に使用されます。
    *   UIコンポーネントモジュール (`app_ui.py`) の `display_progress_ui`, `display_progress_metrics` 関数を呼び出し、進捗UIを更新します。
*   **`app_state_manager.py`**:
    *   Streamlitアプリケーションの状態 (セッション状態) を一元管理します。
    *   `init_session_state`: セッション状態を初期化します。アプリケーション起動時に一度だけ呼び出されます。処理状態 (`processing_state`)、フィルター状態 (`filter_state`)、UI状態 (`ui_state`) などの初期値を設定し、コールバック関数 (`on_search_change_callback`, `handle_start_callback`, `handle_stop_callback`, `reset_processing_state_callback`) をセッションステートに登録します。
    *   `update_processing_state`: 処理状態 (`processing_state`) を更新します。スクレイピングの開始/停止、進捗状況の変化、ステータスメッセージの更新などに伴い、処理状態の各要素 (`is_processing`, `should_stop`, `status_message`, `progress`, `progress_info`, `is_complete`, `salon_data`) を更新します。
    *   `reset_processing_state`: 処理状態 (`processing_state`) を初期状態に戻します。スクレイピング完了後や中断後に呼び出され、状態をリセットします。
    *   `get_processing_state`: 現在の処理状態 (`processing_state`) を取得します。
    *   `get_filter_state`: 現在のフィルター状態 (`filter_state`) を取得します。
    *   `update_filter_state`: フィルター状態 (`filter_state`) を更新します。検索クエリの変更時に呼び出され、フィルター状態の `search_query` を更新します。
    *   `get_ui_state`: 現在のUI状態 (`ui_state`) を取得します。
    *   `get_new_area_data_from_ui_state`: UI状態 (`ui_state`) から新規エリアデータ (`new_area_data`) を取得します。新規エリア追加フォーム (`app_ui.py` の `display_add_new_area_form`) から入力されたデータを取得する際に使用されます。
    *   状態はStreamlitのセッションステート (`st.session_state`) を利用して永続化されます。
*   **`app_ui.py`**:
    *   StreamlitアプリケーションのUIコンポーネント (関数) を定義します。
    *   `display_area_selector`: 階層的なエリア選択UI (都道府県 -> エリア) を表示します。サイドバーのエキスパンダー内に配置され、都道府県とエリアのドロップダウンメニューを提供します。選択された都道府県とエリアを返します。
    *   `display_search_filters`: 検索・フィルタリングUI (エリア名検索) を表示します。サイドバーのエキスパンダー内に配置され、エリア名検索用のテキスト入力フィールドを提供します。入力された検索クエリを返します。
    *   `display_statistics`: 検索結果の統計情報 (全体統計、検索結果統計、サロン数トップ5エリア) を表示します。エキスパンダー内に配置され、表形式やリスト形式で統計情報を表示します。
    *   `display_progress_ui`: 進捗状況UI (プログレスバー、ステータスメッセージ、進捗メトリクス) を更新します。進捗情報 (`app_progress_handler.py` の `progress_callback` から渡される) を元に、UI要素を更新します。
    *   `display_progress_metrics`: 進捗情報をメトリクス形式で表示します。処理済み件数、成功件数、エラー件数、進捗率、平均処理時間、残り時間を数値とグラフで表示します。
    *   `display_salon_data`: スクレイピングしたサロンデータを表形式 (Streamlit DataFrame) で表示します。サロン名、電話番号、住所、スタッフ数、サロンURLなどの情報を列として表示し、ソート、ページネーション、レスポンシブ表示などの機能を提供します。総サロン数、平均スタッフ数、データ取得成功率などの基本統計情報も表示します。
    *   `display_main_ui`: メインエリアのUI要素 (使い方、開始/停止ボタン、進捗表示プレースホルダー) を表示します。アプリケーションのメインコンテンツ部分を構成します。
    *   `display_status_message`: ステータスメッセージ (情報、警告、エラー、成功など) を表示します。スクレイピング処理の状態や結果をユーザーに伝えるために使用されます。
    *   `display_app_header`: アプリケーションのヘッダー (タイトル、ページ設定) を表示します。アプリケーション名、ページアイコン、レイアウトなどを設定します。
    *   `display_sidebar_exit_button`: サイドバーにアプリケーション終了ボタンを表示します。
    *   状態管理モジュール (`app_state_manager.py`) のセッションステート (`st.session_state`) を参照し、UIの状態を制御します (例: ボタンのdisabled状態、エキスパンダーの初期表示状態など)。
    *   アクションハンドラーモジュール (`app_action_handlers.py`) のコールバック関数 (`on_search_change`, `handle_start`, `handle_stop`) をボタンや入力フィールドに登録し、UIアクションとバックエンド処理を連携させます。
*   **`area_manager.py`**:
    *   エリアデータ (CSVファイル `area.csv`) の管理 (読み込み、書き込み、バリデーション、新規エリア追加) を行うクラス `AreaManager` を定義します。
    *   `__init__`: `AreaManager` クラスのコンストラクタです。CSVファイルのパス (`csv_path`) を引数に取り、`_load_csv` メソッドを呼び出してCSVファイルを読み込み、データフレーム (`self.df`) を初期化します。
    *   `_load_csv`: CSVファイルからエリアデータを読み込み、Pandas DataFrameとして返します。ファイルが存在しない場合は、空のDataFrame (カラム定義のみ) を返します。CSV読み込み時にエラーが発生した場合は、ログ (`logging`) にエラー内容を出力し、空のDataFrameを返します。
    *   `validate_area_data`: 新規エリアデータのバリデーションを行います。入力データ (`Dict[str, Any]`) が必須フィールド (`prefecture`, `area`, `url`, `estimated_salons`) を含んでいるか、データ形式 (文字数制限、URL形式、サロン数形式) が正しいか、既存データとの重複がないかなどをチェックします。バリデーション結果 (`bool`) とエラーメッセージ (`str`) のタプルを返します。
    *   `is_duplicate`: 指定された県名 (`prefecture`) とエリア名 (`area`) の組み合わせが既存データ (`self.df`) に存在するかどうかをチェックします。重複している場合は `True`、そうでない場合は `False` を返します。
    *   `add_area`: 新規エリアデータを `area.csv` に追加します。入力データ (`Dict[str, Any]`) のバリデーション (`validate_area_data`) を行い、バリデーションに成功した場合のみ、データフレーム (`self.df`) に新しい行を追加し、`save_areas` メソッドを呼び出してCSVファイルに保存します。処理結果 (`bool`) とメッセージ (`str`) のタプルを返します。エラー発生時はログ (`logging`) にエラー内容を出力します。
    *   `save_areas`: エリアデータ (`self.df`) をCSVファイル (`self.csv_path`) に保存します。データフレームをCSVファイルに書き込む際にエラーが発生した場合は、ログ (`logging`) にエラー内容を出力し、例外 (`Exception`) を発生させます。
*   **`area_processor.py`**:
    *   エリアデータ (CSVファイル `area.csv`) を処理し、各エリアのホットペッパービューティーのページからサロン数をスクレイピングして `area.csv` (実際には `area_structured.csv` に出力) に書き込むスクリプトです。
    *   `AreaProcessor` クラス:
        *   `__init__`: `requests.Session` の初期化、`setup_logging` メソッドの呼び出しを行います。
        *   `setup_logging`: ロギング設定を行います。ログファイルは `area_processing.log` に出力されます。
        *   `get_salon_count`: ホットペッパービューティーのエリアページのURL (`str`) を引数に取り、そのページからサロン数をスクレイピングして整数値 (`int`) で返します。`requests` を使用してHTTPリクエストを送信し、`BeautifulSoup` でHTMLを解析します。複数のHTML構造に対応するため、複数のCSSセレクターを試行し、最初に見つかったサロン数を返します。サロン数が見つからない場合や、HTTPエラー、HTML解析エラーが発生した場合は、ログ (`logging`) にエラーまたは警告メッセージを出力し、`0` を返します。
        *   `process_areas`: エリアデータ処理のメイン関数です。入力CSVファイル (`input_csv`) をPandas DataFrameとして読み込み、各行のURLに対して `get_salon_count` メソッドを呼び出してサロン数を取得し、`estimated_salons` 列に書き込みます。進捗状況を `tqdm` で表示し、処理時間計測を行います。処理完了後、サロン数の統計情報 (合計、平均、最大、サロン数0のエリア数) をコンソールに出力し、結果を `output_csv` にCSVファイルとして保存します。処理中にエラーが発生した場合は、ログ (`logging`) にエラーメッセージを出力し、例外 (`Exception`) を発生させます。
    *   `main`: `AreaProcessor` クラスのインスタンスを作成し、`process_areas` メソッドを呼び出してエリアデータ処理を実行します。入力CSVファイルとして `area.csv`、出力CSVファイルとして `area_structured.csv` を指定します。スクリプトを直接実行 (`python area_processor.py`) した際に呼び出されます。
*   **`config.py`**:
    *   スクレイピングの設定値 (定数) を定義するモジュールです。
    *   `HEADERS`: HTTPリクエストヘッダー (`Dict[str, str]`)。`User-Agent` を設定します。
    *   `MAX_RETRIES`: 最大リトライ回数 (`int`)。HTTPリクエストが失敗した場合のリトライ回数を設定します。
    *   `RETRY_DELAY`: リトライ待機時間 (秒) (`int`)。リトライ時の待機時間 (秒) を設定します。エクスポネンシャルバックオフの基本遅延時間として使用されます。
    *   `MAX_BACKOFF`: 最大バックオフ時間 (秒) (`int`)。エクスポネンシャルバックオフによる最大待機時間を設定します。
    *   `RETRY_CODES`: リトライ対象ステータスコード (`List[int]`)。これらのステータスコードがHTTPレスポンスで返された場合にリトライを行います (例: 429, 500, 502, 503, 504)。
    *   `RETRY_EXCEPTIONS`: リトライ対象例外 (`Tuple[Exception, ...]`)。これらの例外が発生した場合にリトライを行います (例: `requests.exceptions.Timeout`, `requests.exceptions.ConnectionError`)。
    *   `REQUEST_TIMEOUT`: リクエストタイムアウト (秒) (`int`)。HTTPリクエストのタイムアウト時間を設定します。
    *   `SCRAPING_DELAY`: スクレイピング遅延時間 (秒) (`int`)。連続するスクレイピング処理間の待機時間を設定します (秒単位)。ウェブサイトへの負荷を軽減するために使用されます。
    *   `MAX_WORKERS`: 最大ワーカー数 (`int`)。並列スクレイピングで使用するワーカー (スレッド) の最大数を設定します。
    *   `CHUNK_SIZE`: チャンクサイズ (`int`)。並列処理で一度に処理するURLのチャンクサイズを設定します。
    *   `RATE_LIMIT`: レート制限 (秒) (`float`)。1リクエストあたりの最低待機時間 (秒) を設定します。リクエストレートを制限し、ウェブサイトへの過負荷を防ぎます。
    *   `LOG_FORMAT`: ログフォーマット (`str`)。ログ出力のフォーマット文字列を設定します。`logging.Formatter` に渡される形式です。
    *   `LOG_FILE`: ログファイル名 (`str`)。ログ出力先のファイル名を指定します (`scraping.log`)。
    *   `LOG_LEVEL`: ログレベル (`int`)。ログ出力レベルを設定します (`logging.DEBUG`, `logging.INFO`, `logging.WARNING`, `logging.ERROR`, `logging.CRITICAL` など)。
    *   `PHONE_SELECTORS`: 電話番号スクレイピングCSSセレクター (`List[str]`)。電話番号ページから電話番号を抽出するためのCSSセレクターのリストです。リストの順にセレクターを試し、最初に見つかった要素のテキストを電話番号として使用します。
    *   `SALON_SELECTORS`: サロン情報スクレイピングCSSセレクター (`Dict[str, str]`)。サロン詳細ページから各種サロン情報を抽出するためのCSSセレクターを辞書形式で定義します。キー (`name`, `staff_count`, `address`, `links`) ごとにCSSセレクターの文字列を設定します。
*   **`excel_exporter.py`**:
    *   スクレイピングしたサロンデータをExcelファイル (`.xlsx`) に出力する機能を提供するモジュールです。
    *   `ExcelExporter` クラス:
        *   `export_salon_data`: サロンデータ (`List[Dict]`) をExcelファイル (`.xlsx`) に出力します。ファイル名 (`file_name`) を指定できます (省略時は自動生成)。出力されたExcelファイルのパス (`str`) を返します。`openpyxl` ライブラリを使用してExcelファイルを作成し、ヘッダー行とデータ行を書き込みます。
        *   `get_excel_bytes`: サロンデータ (`List[Dict]`) をExcelファイルのバイトデータ (`bytes`) として返します。ファイルに保存せずに、メモリ上でExcelファイルを作成し、そのバイトデータを取得する場合に使用します (例: Streamlitのファイルダウンロード機能)。ファイル名 (`str`) とバイトデータ (`bytes`) のタプルを返します。
*   **`http_client.py`**:
    *   HTTPリクエスト (GET) を送信するクライアント機能を提供するモジュールです。リトライ処理、エラーハンドリング、バックオフ、タイムアウトなどの機能を備えています。
    *   `HTTPClient` クラス:
        *   `calculate_backoff`: リトライ時のバックオフ時間 (`float`) を計算します。試行回数 (`attempt`) に基づいてエクスポネンシャルバックオフを行い、さらにジッター (ランダムな遅延) を加えます。最大バックオフ時間 (`config.MAX_BACKOFF`) を超えないように調整します。
        *   `should_retry`: HTTPレスポンス (`requests.Response`) または例外 (`Exception`) を引数に取り、リトライを行うべきかどうかを判定 (`bool`) して返します。レスポンスが与えられた場合は、ステータスコード (`response.status_code`) がリトライ対象コード (`config.RETRY_CODES`) に含まれているかチェックします。例外が与えられた場合は、例外の型がリトライ対象例外 (`config.RETRY_EXCEPTIONS`) のいずれかに一致するかチェックします。
        *   `get`: 指定されたURL (`str`) にGETリクエストを送信し、`requests.Response` オブジェクトを返します。リクエストヘッダー (`custom_headers`) をカスタマイズできます (省略可)。リクエスト失敗時には、リトライ処理 (`should_retry`, `calculate_backoff`, `config.MAX_RETRIES`, `config.RETRY_DELAY`) を行います。リクエスト成功 (`response.ok`) 時は `response` を返し、リトライ回数超過またはリトライ不可能なエラーの場合は `None` を返します。リクエストタイムアウト (`config.REQUEST_TIMEOUT`) を設定します。リクエストごとのセッション (`requests.Session`) を作成し、接続プールを有効活用します。エラー発生時はログ (`logging`) にエラー情報 (URL、エラー内容、リトライ回数など) を出力します。
*   **`logging_setup.py`**:
    *   アプリケーション全体のロギング設定を初期化する機能を提供します。
    *   `setup_logging`: ロギングの初期設定を行います。ルートロガー (`logging.getLogger()`) に対して、ファイルハンドラー (`logging.FileHandler`) とコンソールハンドラー (`logging.StreamHandler`) を設定し、ログ出力先をファイル (`config.LOG_FILE`) とコンソール両方にします。ログフォーマット (`config.LOG_FORMAT`)、ログレベル (`config.LOG_LEVEL`) を設定ファイル (`config.py`) から取得します。ファイルハンドラーはログファイルを上書きモード (`mode='w'`) でオープンします。既存のルートロガーのハンドラーをクリアしてから、新しいハンドラーを追加します。初期化完了時にログ (`logging.info`) を出力します。
*   **`main.py`**:
    *   コマンドラインアプリケーションのエントリーポイントとなるスクリプトです。
    *   `main`: メインの実行関数です。`setup_logging` 関数を呼び出してロギングを設定し、コマンドラインアプリケーションを起動します。ユーザーにエリアページURLの入力を促し、`parallel_scraper.py` の `ParallelScraper` クラスを使用してスクレイピングを実行します。サロンURLの収集 (`scrape_salon_urls`)、サロン詳細情報のスクレイピング (`scrape_salon_details_parallel`) を行い、取得したサロンデータを `excel_exporter.py` の `ExcelExporter` クラスを使用してExcelファイル (`.xlsx`) に出力します。出力ファイルのパスをコンソールに表示します。スクレイピング処理中にエラーが発生した場合は、ログ (`logging.error`) にエラーメッセージを出力し、`None` を返します。Excelファイル出力に成功した場合は、出力ファイルパス (`str`) を返します。
*   **`parallel_scraper.py`**:
    *   並列スクレイピング処理機能 (`ParallelScraper` クラス) とレート制限機能 (`RateLimiter` クラス) を提供するモジュールです。
    *   `ParallelScraper` クラス:
        *   `__init__`: `ParallelScraper` クラスのコンストラクタです。レートリミッター (`RateLimiter`)、進捗ロック (`threading.Lock`)、停止イベント (`threading.Event`)、ThreadPoolExecutor (`concurrent.futures.ThreadPoolExecutor`) などを初期化します。`max_workers` は `config.MAX_WORKERS` から取得します。進捗コールバック関数 (`_progress_callback`) は初期値 `None` に設定されます。
        *   `__del__`: デストラクタです。`ThreadPoolExecutor` をシャットダウンし、リソースを解放します。実行中のタスクを待たずにシャットダウン (`wait=False`) します。
        *   `stop`: スクレイピング処理を中断します。停止イベント (`_stop_event`) をセットし、`_is_processing` フラグを `False` に設定します。
        *   `reset`: スクレイピングの状態をリセットします。停止イベント (`_stop_event`) をクリアし、各種カウンター (`_total_urls`, `_processed_urls`, `_success_count`, `_error_count`) を初期化し、開始時刻 (`_start_time`) をリセットします。
        *   `set_progress_callback`: 進捗コールバック関数 (`Callable`) を設定します。`progress_callback` 関数は、スクレイピングの進捗状況をUIに通知するために使用されます (`app_progress_handler.py` の `progress_callback` 関数など)。
        *   `_should_stop`: スクレイピングを中断すべきかどうかを判定します (`bool`)。停止イベント (`_stop_event`) がセットされているか、`_is_processing` フラグが `False` になっている場合に `True` を返します。
        *   `_calculate_eta`: 残り時間 (ETA: Estimated Time of Arrival) を計算します (`str`)。開始時刻 (`_start_time`)、処理済みURL数 (`_processed_urls`)、総URL数 (`_total_urls`) から、平均処理時間を算出し、残り時間を推定します。計算不能な場合は `"計算不能"` を返します。エラー発生時はログ (`logging.error`) にエラー内容を出力します。
        *   `_get_progress_info`: 進捗情報 (`Dict`) を取得します。総URL数、処理済みURL数、成功件数、エラー件数、進捗率、平均処理時間、残り時間などの進捗状況を辞書形式で返します。進捗率は `0`〜`100` の範囲で返します。エラー発生時はログ (`logging.error`) にエラー内容を出力し、空の辞書 (`{}`) を返します。
        *   `_update_progress`: 進捗状況を更新します。処理済みURL数、成功/エラー件数をインクリメントし、進捗バー (`tqdm`) を更新し、進捗コールバック関数 (`_progress_callback`) を呼び出します。進捗ロック (`_progress_lock`) を使用してスレッドセーフな更新を行います。進捗コールバック関数呼び出し時にエラーが発生した場合は、ログ (`logging.error`) にエラー内容を出力します。
        *   `scrape_salon_urls`: エリアページのURL (`str`) を引数に取り、そのエリアページからサロンURLのリスト (`List[str]`) をスクレイピングして返します。`scraper.py` の `BeautyScraper.scrape_salon_urls` メソッドを呼び出してURLリストを取得します。処理開始前に状態をリセット (`reset`) し、処理中フラグ (`_is_processing`) を `True` に設定します。中断 (`_should_stop`) が必要な場合は、スクレイピングを中断し、空のリスト (`[]`) を返します。URL収集時にエラーが発生した場合は、ログ (`logging.error`) にエラー内容を出力し、空のリスト (`[]`) を返します。
        *   `_scrape_salon_with_retry`: 単一のサロンURL (`str`) を引数に取り、サロン情報をスクレイピング (`scraper.py` の `BeautyScraper.scrape_salon_details` メソッドを使用) します。レート制限 (`RateLimiter.wait`) を適用し、リトライ処理 (`_scrape_salon_with_retry`) を実装します (最大3回リトライ、指数バックオフ)。スクレイピング成功時はサロン情報 (`Dict`) を返し、失敗時 (リトライ回数超過、中断) は `None` を返します。エラー発生時はログ (`logging.warning`, `logging.error`) にエラー内容を出力します。
        *   `scrape_salon_details_parallel`: サロンURLのリスト (`List[str]`) を引数に取り、それらのURLからサロン情報を並列でスクレイピングします。`ThreadPoolExecutor` を使用して並列処理を行い、`_scrape_salon_with_retry` メソッドをワーカーとして実行します。進捗バー (`tqdm`) で進捗状況を表示し、進捗更新 (`_update_progress`) を行います。中断 (`_should_stop`) が必要な場合は、スクレイピングを中断します。スクレイピング結果のサロン情報リスト (`List[Dict]`) を返します。エラー発生時はログ (`logging.error`) にエラー内容を出力します。処理開始前に処理中フラグ (`_is_processing`) を `True` に設定し、終了時に `False` に戻します。
    *   `RateLimiter` クラス:
        *   `__init__`: `RateLimiter` クラスのコンストラクタです。レート制限値 (`rate_limit`) (1秒あたりのリクエスト数、`float`) を引数に取り、レート制限値を設定します。最後にリクエストを送信した時刻 (`last_request_time`) を初期化します。ロック (`threading.Lock`) を初期化します。レート制限値は最小値 (`0.1秒`) を保証します。
        *   `wait`: レート制限に従って待機します。前回のリクエストからの経過時間 (`elapsed`) を計算し、必要な待機時間 (`wait_time`) を算出し、`time.sleep` で待機します。ロック (`_lock`) を使用してスレッドセーフな待機処理を行います。待機後、最後にリクエストを送信した時刻 (`last_request_time`) を現在時刻で更新します。
*   **`scraper.py`**:
    *   個別のWebページ (サロン詳細ページ、電話番号ページ、エリアページ) から情報をスクレイピングする機能を提供するモジュールです。`BeautyScraper` クラス (静的メソッドのみ) を定義します。
    *   `BeautyScraper` クラス:
        *   `scrape_phone_number`: 電話番号ページのURL (`str`) を引数に取り、そのページから電話番号をスクレイピングして文字列 (`str`) で返します。`http_client.py` の `HTTPClient.get` メソッドを使用してHTTPリクエストを送信し、`BeautifulSoup` でHTMLを解析します。複数のCSSセレクター (`config.PHONE_SELECTORS`) を試行し、最初に見つかった要素のテキストを電話番号として使用します。電話番号が見つからない場合や、スクレイピングエラーが発生した場合は、エラーメッセージ (`"電話番号情報なし"`, `"電話番号スクレイピングエラー"`) を返します。エラー発生時はログ (`logging.warning`, `logging.error`) にエラー内容を出力します。
        *   `scrape_salon_details`: サロン詳細ページのURL (`str`) を引数に取り、そのページからサロン詳細情報 (`Dict`) をスクレイピングして返します。`http_client.py` の `HTTPClient.get` メソッドを使用してHTTPリクエストを送信し、`BeautifulSoup` でHTMLを解析します。サロン名、電話番号、住所、スタッフ数、関連リンク (リスト形式)、関連リンク数、サロンURL などをスクレイピングし、辞書形式で返します。電話番号は `scrape_phone_number` メソッドを呼び出して取得します。情報が見つからない場合は、デフォルト値 (`"店名情報なし"`, `"電話番号情報なし"`, `"住所情報なし"`, `"スタッフ数情報なし"`) を設定します。スクレイピングエラーが発生した場合は、`None` を返します。エラー発生時はログ (`logging.error`) にエラー内容を出力します。
        *   `scrape_salon_urls`: エリアページのURL (`str`) を引数に取り、そのエリアページに掲載されているサロンURLのリスト (`List[str]`) をスクレイピングして返します。`http_client.py` の `HTTPClient.get` メソッドを使用してHTTPリクエストを送信し、`BeautifulSoup` でHTMLを解析します。ページネーションを処理し、複数ページにわたるサロンURLを収集します。中断 (`should_stop` コールバック関数) が必要な場合は、スクレイピングを中断し、それまでに収集したURLリストを返します。URLの正規化 (`url_utils.normalize_url`) を行い、重複URLを排除します。スクレイピングエラーが発生した場合は、空のリスト (`[]`) を返します。エラー発生時はログ (`logging.error`, `logging.exception`) にエラー内容を出力します。
*   **`url_utils.py`**:
    *   URL処理ユーティリティ関数を提供するモジュールです。
    *   `normalize_url`: URL文字列 (`str`) を引数に取り、正規化されたURL文字列 (`str`) を返します。URLを `urllib.parse.urlparse` でパースし、不要なパラメータ (params, query, fragment) を削除し、パス部分を正規化 (`parsed_url.path`) します。正規化後、`urllib.parse.urlunparse` でURL文字列を再構築します。URLパースエラーが発生した場合は、ログ (`logging.error`) にエラー内容を出力し、入力URLをそのまま返します。

## 設定ファイル (`config.py`) の調整

`config.py` ファイルを編集することで、スクレイピングの動作を細かく制御できます。

*   **`HEADERS`**: HTTPリクエストヘッダー。`User-Agent` を変更して、スクレイピングの検出を回避できます。複数の `User-Agent` を設定し、ランダムに切り替えることも有効です。
*   **`MAX_RETRIES`, `RETRY_DELAY`, `RETRY_CODES`, `RETRY_EXCEPTIONS`, `MAX_BACKOFF`**: リトライ設定。ネットワーク環境に合わせてリトライ回数、待機時間、対象ステータスコード、対象例外を調整します。
*   **`REQUEST_TIMEOUT`**: リクエストタイムアウト時間。ウェブサイトの応答速度に合わせて調整します。
*   **`SCRAPING_DELAY`, `RATE_LIMIT`**: スクレイピング遅延、レート制限。ウェブサイトへの負荷を軽減するために調整します。`RATE_LIMIT` は秒単位の最小待機時間、`SCRAPING_DELAY` は連続リクエスト間の追加遅延です。
*   **`MAX_WORKERS`**: 並列処理のワーカー数。CPUリソースやネットワーク帯域に合わせて調整します。ワーカー数を増やすと高速化しますが、ウェブサイトへの負荷も増加します。
*   **`LOG_LEVEL`**: ログ出力レベル。デバッグ時は `logging.DEBUG`、通常時は `logging.INFO` など、必要に応じて変更します。
*   **`PHONE_SELECTORS`, `SALON_SELECTORS`**: CSSセレクター。ウェブサイトの構造変更に合わせて修正します。セレクターが古い場合、スクレイピングが正常に動作しません。

## 注意点

*   **利用規約の遵守**: ホットペッパービューティーの利用規約、robots.txt を遵守し、ウェブサイトに過度な負荷をかけないように注意してください。
*   **スクレイピング頻度**: 短時間での大量アクセスはアクセス制限の原因となります。`config.py` の `SCRAPING_DELAY`, `RATE_LIMIT` を適切に設定してください。
*   **ウェブサイト構造の変更**: ホットペッパービューティーのウェブサイト構造が変更された場合、スクレイピングツールが動作しなくなる可能性があります。定期的に動作確認を行い、必要に応じて `config.py` の CSSセレクター (`PHONE_SELECTORS`, `SALON_SELECTORS`) を修正してください。
*   **エラーログの確認**: エラーが発生した場合は、ログファイル (`scraping.log`, `area_processing.log`) を確認し、原因を特定してください。
*   **個人情報の取り扱い**: スクレイピングによって電話番号などの個人情報を取得する可能性があります。個人情報保護法などの関連法規を遵守し、適切に取り扱ってください。
*   **`secrets.toml` の管理**: Streamlitアプリケーションのパスワード認証を使用する場合、`.streamlit/secrets.toml` ファイルに実際のパスワードを記述します。このファイルは `.gitignore` によってGitの管理対象外となっていますが、誤って公開しないよう注意してください。サンプルとして `.streamlit/secrets.toml.example` が用意されています。
*   **CAPTCHA**: ウェブサイトがCAPTCHAを導入した場合、自動スクレイピングは困難になります。

## 既知の問題点

*   **ウェブサイト構造変更への依存**: ウェブサイトのデザインやHTML構造が変更されると、CSSセレクターの見直しが必要になります。
*   **情報取得の完全性**: ウェブサイトのデータ構造や表示方法によっては、すべての情報を完全に取得できるわけではありません。
*   **CAPTCHA**: CAPTCHA認証が導入された場合、自動スクレイピングが困難になります。
*   **並列処理**: 極端に高い並列度で実行した場合、ウェブサイトへの負荷が高まり、アクセス制限やエラーの原因となる可能性があります。`config.py` の `MAX_WORKERS` を調整してください。
*   **進捗表示の精度**: 残り時間 (ETA) はあくまで推定値であり、実際の処理時間と誤差が生じる場合があります。

## 今後の改善点 (ロードマップ)

*   **User-Agentローテーション**: `config.py` にUser-Agentリストを定義し、リクエストごとにランダムに選択する機能を追加し、検出回避率を向上させます。
*   **プロキシサポート**: プロキシサーバー経由でのリクエスト送信をサポートし、アクセス制限を回避するオプションを追加します。
*   **CAPTCHA自動回避**: CAPTCHA自動回避機能 (API連携など) の導入を検討します。
*   **スクレイピング対象拡張**: メニュー情報、口コミ情報など、サロン詳細ページ以外の情報もスクレイピングできるように拡張します。
*   **データ整形機能**: 住所分割 (都道府県、市区町村、番地など)、データクリーニング機能を追加し、データ品質を向上させます。
*   **データ出力先の拡張**: CSV、データベース (MySQL, PostgreSQL など) への出力オプションを追加します。
*   **GUI機能強化**:
    *   スクレイピング設定 (並列度、遅延時間など) をGUIから変更できるようにします。
    *   スクレイピング実行ログをGUIに表示する機能を追加します。
    *   エリア追加フォームのバリデーションエラーをGUIにリアルタイム表示します。
*   **エラーハンドリングの強化**: より詳細なエラーログの記録、エラー発生時の処理継続、リトライロジックの改善を行います。

## 免責事項

このツールは、学習・研究目的で開発されたものであり、商用利用や違法行為を推奨するものではありません。ツールの利用は自己責任で行ってください。作者は、このツールの利用によって生じたいかなる損害についても責任を負いません。利用規約・法令を遵守し、倫理的な範囲内でご利用ください。
