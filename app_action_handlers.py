"""
app_action_handlers.py - Streamlitアプリケーションのアクションハンドラーモジュール

このモジュールは、UIからのアクション（開始、停止ボタンのクリックなど）を処理する機能を提供します。
スクレイピング開始、停止、検索クエリ変更などのアクションに対するハンドラー関数を定義します。
"""

import streamlit as st
from typing import Dict, Any
from app_state_manager import update_processing_state, update_filter_state # 状態管理モジュールから関数をimport
from app_progress_handler import progress_callback # 進捗処理モジュールからコールバック関数をimport

def handle_start() -> None:
    """
    スクレイピング処理の開始ハンドラー。
    処理状態を更新し、UIを再描画します。
    """
    update_processing_state(is_processing=True, should_stop=False, status_message='処理を開始します...')
    # st.rerun() # コールバック関数内での st.rerun() は削除

def handle_stop() -> None:
    """
    スクレイピング処理の停止ハンドラー。
    スクレイパーを停止させ、処理状態を更新し、UIを再描画します。
    """
    if st.session_state.processing_state['is_processing']:
        if hasattr(st.session_state, 'scraper'):
            st.session_state.scraper.stop()
        update_processing_state(
            is_processing=False,
            should_stop=True,
            status_message='処理を中断しました',
            progress=0
        )
    # st.rerun() # コールバック関数内での st.rerun() は削除

def on_search_change() -> None:
    """
    検索入力変更時のコールバック処理。
    フィルター状態を更新します。
    """
    update_filter_state(search_query=st.session_state.search_input)