"""
app_progress_handler.py - Streamlitアプリケーションの進捗処理モジュール

このモジュールは、スクレイピング処理の進捗状況を管理し、UIに表示する機能を提供します。
進捗情報の更新、UIへの反映、経過時間計算などを担当します。
"""

import streamlit as st
from typing import Dict, Any

def progress_callback(progress_info: Dict[str, Any]) -> None:
    """
    スクレイピング処理からの進捗コールバック関数。
    進捗情報をセッションステートに保存し、UIを更新します。

    Args:
        progress_info: 進捗情報を含む辞書
    """
    st.session_state.processing_state['progress'] = progress_info['progress']
    st.session_state.processing_state['progress_info'] = progress_info
    from app_ui import display_progress_ui # 循環インポートを避けるためここでインポート
    display_progress_ui()

def format_elapsed_time(seconds: float) -> str:
    """
    経過時間を人間が読みやすい形式に変換します。

    Args:
        seconds: 経過秒数

    Returns:
        str: フォーマットされた時間文字列（例: "1時間30分"）
    """
    if seconds < 60:
        return f"{int(seconds)}秒"
    elif seconds < 3600:
        return f"{int(seconds / 60)}分{int(seconds % 60)}秒"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}時間{minutes}分"