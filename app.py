"""
app.py - モジュール化されたStreamlit美容室情報スクレイピングアプリケーション

このスクリプトは、モジュール化されたStreamlitアプリケーションのエントリーポイントです。
各機能モジュールを連携させ、アプリケーション全体の制御とUI表示を行います。
"""

import streamlit as st
import logging
from logging_setup import setup_logging
from parallel_scraper import ParallelScraper
from excel_exporter import ExcelExporter
from pathlib import Path
from datetime import datetime

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


def main() -> None:
    """
    アプリケーションのメインエントリーポイント。
    モジュール化されたStreamlitアプリケーションの各機能を呼び出し、連携させます。
    """
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

    # ロギング設定
    setup_logging()

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

                    # スクレイパーの状態をリセット
                    st.session_state.scraper.reset()

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


if __name__ == "__main__":
    main()