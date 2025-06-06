"""
app.py - モジュール化されたStreamlit美容室情報スクレイピングアプリケーション

このスクリプトは、モジュール化されたStreamlitアプリケーションのエントリーポイントです。
各機能モジュールを連携させ、アプリケーション全体の制御とUI表示を行います。
"""

import streamlit as st
import logging
import hmac
import os
from pathlib import Path
from datetime import datetime

# モジュールのインポート
from logging_setup import setup_logging
from parallel_scraper import ParallelScraper
from excel_exporter import ExcelExporter
from secret_manager import get_secret, validate_secrets, is_development_environment

# モジュールをimport
from app_ui import (
    display_app_header, display_search_filters,
    display_statistics, display_area_selector, display_main_ui,
    display_status_message, display_salon_data, display_progress_ui
)
from app_state_manager import init_session_state, get_processing_state, get_filter_state, get_ui_state, reset_processing_state, update_processing_state # 状態管理module
from app_area_handler import load_area_data, process_area_data_and_render_selector # エリアデータ処理module
from app_progress_handler import progress_callback # 進捗処理module
from app_action_handlers import handle_start, handle_stop, on_search_change # アクションハンドラーmodule

# ページ設定
# アイコンパスを相対パスから絶対パスに変換
_icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
_icon = _icon_path if os.path.exists(_icon_path) else None

st.set_page_config(
    page_title="HPBスクレイピングアプリ",
    page_icon=_icon,
    layout="wide"
)

def check_password():
    """ユーザーのパスワードが正しい場合は `True` を返します。"""
    
    # 開発環境ではパスワード認証をスキップするオプション
    if is_development_environment() and get_secret("skip_password", False):
        return True

    def password_entered():
        """ユーザーが入力したパスワードが正しいか確認します。"""
        # キーの存在確認
        if "password" not in st.session_state:
            st.session_state["password_correct"] = False
            return
        
        # パスワードの取得と検証
        stored_password = get_secret("password")
        if not stored_password:
            st.error("システム設定エラー: パスワードが設定されていません。")
            st.info("管理者は「.streamlit/secrets.toml」ファイルまたはStreamlit Cloudのシークレット設定を確認してください。")
            st.session_state["password_correct"] = False
            logging.error("シークレット設定にパスワードが見つかりません。")
            return
        
        # パスワードの比較
        try:
            if hmac.compare_digest(st.session_state["password"], stored_password):
                st.session_state["password_correct"] = True
                del st.session_state["password"]  # パスワードをセッションに保存しない
            else:
                st.session_state["password_correct"] = False
        except Exception as e:
            logging.error(f"パスワード認証中にエラーが発生: {str(e)}")
            st.session_state["password_correct"] = False

    # パスワードが検証されている場合はTrueを返す
    if st.session_state.get("password_correct", False):
        return True

    # シークレット設定の検証
    errors = validate_secrets()
    if errors:
        for error_msg in errors.values():
            st.error(error_msg)
        if "secrets_error" in errors:
            st.stop()
    
    # パスワード入力フォームを表示
    st.text_input(
        "パスワード", type="password", on_change=password_entered, key="password"
    )
    
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 パスワードが正しくありません")
    
    return False

def main() -> None:
    """
    アプリケーションのメインエントリーポイント。
    モジュール化されたStreamlitアプリケーションの各機能を呼び出し、連携させます。
    """
    # ロギング設定
    setup_logging()
    
    # パスワード認証のチェック
    if not check_password():
        st.stop()  # 認証が成功しない場合は処理を続行しない

    # セッションステートの初期化 (コールバック関数を登録)
    init_session_state(
        on_search_change_callback=on_search_change,
        handle_start_callback=handle_start,
        handle_stop_callback=handle_stop,
        reset_processing_state_callback=reset_processing_state
    )

    # スクレイパーの初期化
    if 'scraper' not in st.session_state:
        st.session_state.scraper = ParallelScraper()
        st.session_state.scraper.set_progress_callback(progress_callback)

    # 設定情報のログ出力（開発環境のみ）
    if is_development_environment():
        logging.info("アプリケーション設定が正常に読み込まれました")

    # UIの表示 (ヘッダー)
    display_app_header()

    # 処理状態の取得
    state = get_processing_state()
    is_processing = state['is_processing']
    should_stop = state['should_stop']
    status_message = state['status_message']

    # サイドバーのUI要素表示 (検索フィルター、統計情報、エリアセレクター)
    with st.sidebar:
        st.markdown("### 設定")
        search_query = display_search_filters() # 検索フィルターUI表示
        selected_prefecture, selected_area, filtered_data = process_area_data_and_render_selector(is_processing) # エリアデータ処理、エリアセレクターUI表示
        display_statistics(load_area_data(), filtered_data) # 統計情報UI表示

    # メインエリアのUI要素表示 (使い方、開始/停止ボタン、進捗表示、ステータスメッセージ)
    display_status_message(status_message, should_stop, is_processing) # ステータスメッセージ表示
    display_main_ui(is_processing, should_stop) # メインUI (ボタン、プレースホルダー) 表示
    display_progress_ui() # 進捗UIの初期表示


    # メイン処理 (スクレイピング実行部分)
    if is_processing and not should_stop:
        # 新しい処理の開始前に必ずスクレイパーの状態をリセット
        st.session_state.scraper.reset()
        
        try:
            if not selected_area or not selected_prefecture:
                st.error("都道府県とエリアを選択してください。")
                update_processing_state(is_processing=False) # 状態管理moduleの関数を使用
                return

            # エリア情報の取得と検証 (app_area_handler.py に移動しても良い)
            area_info = next(
                (area for area in filtered_data['area_data'][selected_prefecture]['areas']
                if area['area'] == selected_area),
                None
            )

            if not area_info:
                st.error("選択されたエリアの情報が見つかりません。")
                update_processing_state(is_processing=False) # 状態管理moduleの関数を使用
                return

            area_url = area_info['url']
            scraper = st.session_state.scraper
            scraper.set_progress_callback(progress_callback) # 進捗コールバック関数設定 (app_progress_handler.py)

            # 処理状態の更新 (app_state_manager.py)
            update_processing_state(
                status_message=f"サロン情報収集中... ({selected_prefecture} {selected_area})",
                progress=0
            )

            # サロンURL収集
            salon_urls = scraper.scrape_salon_urls(area_url)

            if not salon_urls:
                st.warning("このエリアで有効なサロンURLが見つかりませんでした。")
                update_processing_state(is_processing=False) # 状態管理moduleの関数を使用
                return

            if salon_urls:
                # サロン情報のスクレイピング
                salon_details = scraper.scrape_salon_details_parallel(salon_urls)

                if salon_details:
                    # 出力ディレクトリの作成
                    output_dir = Path("output")
                    output_dir.mkdir(exist_ok=True)

                    # ファイル名に都道府県とエリアを含める
                    filename = f"{selected_prefecture}_{selected_area}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    output_path = output_dir / filename

                    # Excelの保存
                    exporter = ExcelExporter()
                    exporter.export_salon_data(salon_details, str(output_path))

                    # スクレイピング完了時の処理
                    logging.info(f"スクレイピング完了: 成功={len(salon_details)}件, エラー=0件")
                    
                    # 処理状態を更新
                    update_processing_state(
                        is_processing=False,
                        status_message=f"スクレイピング完了: 成功={len(salon_details)}件, エラー=0件",
                        progress=100,
                        is_complete=True,
                        salon_data=salon_details
                    )

                    # スクレイピング結果の表示
                    st.subheader("スクレイピング結果")
                    display_salon_data(salon_details)  # サロンデータ表示 (app_ui.py)

                    # ダウンロードボタンを表示
                    if salon_details:  # サロンデータが存在する場合のみ表示
                        excel_bytes, file_name = ExcelExporter.get_excel_bytes(salon_details)
                        st.download_button(
                            label="Excelファイルをダウンロード",
                            data=excel_bytes,
                            file_name=file_name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

                    # 完了メッセージ
                    st.success(f"""
                        スクレイピングが完了しました！
                        - 対象エリア: {selected_prefecture} {selected_area}
                        - 取得件数: {len(salon_details):,}件
                    """)

                    # 処理状態をリセット（ただし、サロンデータと完了フラグは保持）
                    update_processing_state(
                        is_processing=False,
                        should_stop=False,
                        status_message="",
                        progress=0,
                        progress_info={},
                        is_complete=True,  # 完了フラグは保持
                        salon_data=salon_details  # サロンデータは保持
                    )
                else:
                    st.warning("サロンが見つかりませんでした。")
        except Exception as e:
            error_message = f"エラーが発生しました: {str(e)}"
            update_processing_state(
                is_processing=False,
                status_message=error_message,
                progress=0
            ) # 状態管理moduleの関数を使用
            logging.error(f"Error during scraping: {str(e)}")
            st.error(error_message)
            st.rerun()

    if 'processing_state' in st.session_state and st.session_state.processing_state['is_complete']:
        salon_data = st.session_state.processing_state['salon_data']
        if salon_data:
            st.subheader("前回のスクレイピング結果")
            display_salon_data(salon_data)
            excel_bytes, file_name = ExcelExporter.get_excel_bytes(salon_data)
            st.download_button(
                label="Excelファイルをダウンロード",
                data=excel_bytes,
                file_name=file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_button_rerun" # ダウンロードボタンにユニークなキーを設定
            )


if __name__ == "__main__":
    main()