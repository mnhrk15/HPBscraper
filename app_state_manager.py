"""
app_state_manager.py - Streamlitアプリケーションの状態管理モジュール

このモジュールは、Streamlitアプリケーションのセッション状態を初期化し、管理する機能を提供します。
処理状態、フィルター状態、UI状態などのアプリケーション全体の状態を保持し、更新します。
"""

import streamlit as st
from typing import Optional, Dict, Any, Callable # Optional, Dict, Any, Callable をインポート

# 定数定義
PROGRESS_INITIAL_STATE = {
    'is_processing': False,
    'should_stop': False,
    'status_message': '',
    'progress': 0,
    'progress_info': {}
}

def init_session_state(on_search_change_callback: Callable, handle_start_callback: Callable, handle_stop_callback: Callable, reset_processing_state_callback: Callable) -> None:
    """
    Streamlitのセッション状態を初期化します。
    コールバック関数を登録します。
    """
    if 'processing_state' not in st.session_state:
        st.session_state.processing_state = PROGRESS_INITIAL_STATE
    
    # 検索とフィルタリングの状態管理
    if 'filter_state' not in st.session_state:
        st.session_state.filter_state = {
            'search_query': '',
            'selected_prefectures': set(),
            'selected_areas': set()
        }
    
    # UI状態の管理
    if 'ui_state' not in st.session_state:
        st.session_state.ui_state = {
            'show_filters': False,
            'show_statistics': False,
            'show_add_area': False,
            'new_area_data': { # 新規エリア追加フォームのデータ
                'prefecture': '',
                'area': '',
                'url': '',
                'estimated_salons': 1,
                'add_button_clicked': False
            }
        }
    
    # 進捗状態の管理用プレースホルダー (app_ui.py で初期化)
    if 'progress_placeholder' not in st.session_state:
        st.session_state.progress_placeholder = None
    if 'status_placeholder' not in st.session_state:
        st.session_state.status_placeholder = None
    if 'metrics_placeholder' not in st.session_state:
        st.session_state.metrics_placeholder = None

    # DataFrameを格納するstate
    if 'salon_data_df' not in st.session_state:
        st.session_state.salon_data_df = None

    # コールバック関数をセッションステートに登録
    st.session_state.on_search_change_callback = on_search_change_callback
    st.session_state.handle_start_callback = handle_start_callback
    st.session_state.handle_stop_callback = handle_stop_callback
    st.session_state.reset_processing_state_callback = reset_processing_state_callback

def update_processing_state(
    is_processing: Optional[bool] = None,
    should_stop: Optional[bool] = None,
    status_message: Optional[str] = None,
    progress: Optional[float] = None,
    progress_info: Optional[Dict[str, Any]] = None
) -> None:
    """
    処理状態を更新します。

    Args:
        is_processing: 処理中フラグ
        should_stop: 停止フラグ
        status_message: ステータスメッセージ
        progress: 進捗率（0-100）
        progress_info: 詳細な進捗情報
    """
    if 'processing_state' not in st.session_state:
        st.session_state.processing_state = PROGRESS_INITIAL_STATE
    
    if is_processing is not None:
        st.session_state.processing_state['is_processing'] = is_processing
    if should_stop is not None:
        st.session_state.processing_state['should_stop'] = should_stop
    if status_message is not None:
        st.session_state.processing_state['status_message'] = status_message
    if progress is not None:
        st.session_state.processing_state['progress'] = progress
    if progress_info is not None:
        st.session_state.processing_state['progress_info'] = progress_info

def reset_processing_state() -> None:
    """
    処理状態を初期状態に戻します。
    """
    st.session_state.processing_state = PROGRESS_INITIAL_STATE

def get_processing_state() -> Dict[str, Any]:
    """
    処理状態を取得します。

    Returns:
        Dict[str, Any]: 処理状態
    """
    return st.session_state.processing_state

def get_filter_state() -> Dict[str, Any]:
    """
    フィルター状態を取得します。

    Returns:
        Dict[str, Any]: フィルター状態
    """
    return st.session_state.filter_state

def update_filter_state(search_query: Optional[str] = None) -> None:
    """
    フィルター状態を更新します。

    Args:
        search_query: 検索クエリ
    """
    if 'filter_state' not in st.session_state:
        st.session_state.filter_state = {
            'search_query': '',
            'selected_prefectures': set(),
            'selected_areas': set()
        }
    if search_query is not None:
        st.session_state.filter_state['search_query'] = search_query

def get_ui_state() -> Dict[str, Any]:
    """
    UI状態を取得します。

    Returns:
        Dict[str, Any]: UI状態
    """
    return st.session_state.ui_state

def get_new_area_data_from_ui_state() -> Dict[str, Any]:
    """
    UI状態から新規エリアデータを取得します。

    Returns:
        Dict[str, Any]: 新規エリアデータ
    """
    return st.session_state.ui_state['new_area_data']