"""
app_action_handlers.py - Streamlitアプリケーションのアクションハンドラーモジュール

このモジュールは、UIからのアクション（開始、停止ボタンのクリックなど）を処理する機能を提供します。
スクレイピング開始、停止、検索クエリ変更などのアクションに対するハンドラー関数を定義します。
"""

import streamlit as st
import logging
from typing import Dict, Any
from app_state_manager import update_processing_state, update_filter_state # 状態管理モジュールから関数をimport
from app_progress_handler import progress_callback # 進捗処理モジュールからコールバック関数をimport

def handle_start() -> None:
    """
    スクレイピング処理の開始ハンドラー。
    処理状態を更新し、UIを再描画します。
    中断中または中断直後は処理を開始しないよう制御します。
    """
    # 現在の処理状態を取得
    current_state = st.session_state.processing_state
    
    # 中断中または中断直後（should_stopがTrueの状態）の場合は処理を開始しない
    if current_state.get('should_stop', False):
        st.warning('処理中断中または中断直後です。しばらく待ってから開始ボタンを押してください。')
        return
        
    # 処理中の場合も二重実行を防ぐ
    if current_state.get('is_processing', False):
        st.warning('すでに処理が実行中です')
        return
    
    # 既存のスクレイパーインスタンスが存在する場合は削除して新しいインスタンスを作成
    # これにより、以前の状態が残ることによる問題を防ぐ
    from parallel_scraper import ParallelScraper
    from app_progress_handler import progress_callback
    
    if hasattr(st.session_state, 'scraper'):
        logging.info("既存のスクレイパーインスタンスを削除し、新しいインスタンスを作成します")
        # 明示的に参照を削除
        del st.session_state.scraper
        import gc
        gc.collect()  # ガベージコレクションを実行
        
    # 新しいスクレイパーインスタンスを作成
    st.session_state.scraper = ParallelScraper()
    st.session_state.scraper.set_progress_callback(progress_callback)
    logging.info("新しいスクレイパーインスタンスを作成しました")
        
    update_processing_state(is_processing=True, should_stop=False, status_message='処理を開始します...')

def handle_stop() -> None:
    """
    スクレイピング処理の停止ハンドラー。
    スクレイパーを停止させ、処理状態を更新します。
    確実な中断のために処理の終了を待機します。
    """
    if st.session_state.processing_state['is_processing']:
        try:
            # 中断処理開始を表示
            logging.info("スクレイピング処理の中断を開始します")
            update_processing_state(
                is_processing=True,  # まだ処理中だが中断フラグをセット
                should_stop=True,
                status_message='処理を中断中...',
                progress=st.session_state.processing_state.get('progress', 0)
            )
            
            # スクレイパーの中断メソッド呼び出し
            if hasattr(st.session_state, 'scraper'):
                logging.info("スクレイパーのstopメソッドを呼び出します")
                st.session_state.scraper.stop()
                
                # 中断が確実に完了するまで少し待機（必要に応じて調整）
                import time
                time.sleep(0.5)
            else:
                logging.warning("セッションにスクレイパーが存在しません。中断処理をスキップします。")
                
            # 中断完了後に状態を更新
            update_processing_state(
                is_processing=False,
                should_stop=False,  # 中断完了後はshould_stopフラグをFalseにリセット
                status_message='処理を中断しました',
                progress=0
            )
            
            logging.info("スクレイピング処理が正常に中断されました")
            
            # st.rerun()を使わずに状態更新のみ行う（Streamlitが自動的に再描画する）
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logging.error(f"中断処理中にエラーが発生: {str(e)}\n{error_details}")
            
            # エラー発生時も処理状態を中断完了に設定し、ボタンを有効化
            update_processing_state(
                is_processing=False, 
                should_stop=False,  # エラー発生時もshould_stopフラグをFalseにリセット
                status_message=f'中断処理中にエラーが発生: {str(e)}',
                progress=0
            )

def on_search_change() -> None:
    """
    検索入力変更時のコールバック処理。
    フィルター状態を更新します。
    """
    update_filter_state(search_query=st.session_state.search_input)