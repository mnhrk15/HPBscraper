"""
app_area_handler.py - Streamlitアプリケーションのエリアデータ処理モジュール

このモジュールは、エリアデータの読み込み、フィルタリング、新規エリア追加などの処理機能を提供します。
CSVファイルからのエリアデータ読み込み、検索クエリによるフィルタリング、AreaManagerを使用した新規エリア追加などを担当します。
"""

import streamlit as st
from typing import Dict, Any, Tuple
from app_ui import display_area_selector # app_ui.py から display_area_selector をインポート
from area_manager import AreaManager
import time
import logging

DEFAULT_CSV_PATH = 'area.csv'

def load_area_data() -> Dict[str, Any]:
    """
    CSVファイルからエリアデータを読み込み、構造化されたデータを返します。

    Returns:
        Dict[str, Any]: {
            'area_data': Dict[str, Dict] - 都道府県ごとのエリア情報,
            'prefectures': List[str] - 都道府県リスト,
            'total_areas': int - 総エリア数,
            'total_salons': int - 総サロン数
        }
    """
    try:
        if 'area_manager' not in st.session_state: # AreaManagerの初期化をここで行う
            st.session_state.area_manager = AreaManager(DEFAULT_CSV_PATH)
        df = st.session_state.area_manager.df

        if df.empty:
            return {
                'area_data': {},
                'prefectures': [],
                'total_areas': 0,
                'total_salons': 0
            }

        # 都道府県でグループ化したデータを作成
        prefecture_groups = df.groupby('prefecture')
        # 都道府県ごとのエリアデータを辞書形式で保持
        area_data = {
            prefecture: {
                'areas': group[['area', 'url', 'estimated_salons']].to_dict('records'),
                'total_salons': group['estimated_salons'].sum()
            }
            for prefecture, group in prefecture_groups
        }
        return {
            'area_data': area_data,
            'prefectures': sorted(area_data.keys()),
            'total_areas': len(df),
            'total_salons': df['estimated_salons'].sum()
        }
    except Exception as e:
        logging.error(f"エリアデータの読み込みに失敗: {str(e)}")
        return {
            'area_data': {},
            'prefectures': [],
            'total_areas': 0,
            'total_salons': 0
        }

def filter_areas(area_data: Dict[str, Any], search_query: str) -> Dict[str, Any]:
    """
    エリアデータを検索条件でフィルタリングします。

    Args:
        area_data: エリアデータ辞書
        search_query: 検索クエリ文字列

    Returns:
        Dict[str, Any]: フィルタリングされたエリアデータ
    """
    if not search_query:
        return area_data

    filtered_data = {
        'area_data': {},
        'prefectures': [],
        'total_areas': 0,
        'total_salons': 0
    }

    for prefecture, data in area_data['area_data'].items():
        matching_areas = [
            area for area in data['areas']
            if search_query.lower() in area['area'].lower()
        ]
        
        if matching_areas:
            filtered_data['area_data'][prefecture] = {
                'areas': matching_areas,
                'total_salons': sum(area['estimated_salons'] for area in matching_areas)
            }
            filtered_data['total_salons'] += filtered_data['area_data'][prefecture]['total_salons']
            filtered_data['total_areas'] += len(matching_areas)

    filtered_data['prefectures'] = sorted(filtered_data['area_data'].keys())
    return filtered_data

def handle_add_new_area(new_area_data: Dict[str, Any]) -> None:
    """
    新規エリア追加処理を行います。
    UIからの入力データを受け取り、AreaManagerを使ってエリアを追加し、結果をUIにフィードバックします。

    Args:
        new_area_data: 新規エリアデータ (UI state から取得)
    """
    if not new_area_data['prefecture'] or not new_area_data['area'] or not new_area_data['url']:
        st.error("すべての項目を入力してください")
        return

    with st.spinner("エリアを追加中..."):
        area_manager = st.session_state.area_manager # AreaManagerをセッションステートから取得
        success, message = area_manager.add_area(new_area_data)

        # 処理結果に応じてフィードバックを表示
        if success:
            # 成功メッセージを表示
            st.success(f"""
            ✨ 新しいエリアが追加されました！

            **追加されたエリア情報**
            - 県名: {new_area_data['prefecture']}
            - エリア: {new_area_data['area']}
            - 推定サロン数: {new_area_data['estimated_salons']:,}件
            """)

            # 少し待ってからリロード (コールバック関数内ではなく、メインスクリプトでrerun)
            time.sleep(2)
            st.rerun() # コールバック関数内での st.rerun() を削除し、app.py の main 関数で rerun を呼び出すように変更する

        else:
            st.error(message)

def process_area_data_and_render_selector(is_processing: bool) -> Tuple[str, str, Dict[str, Any]]:
    """
    エリアデータをロードし、フィルタリング、エリアセレクターUIのレンダリング、
    新規エリア追加処理を行います。

    Args:
        is_processing: 処理中フラグ

    Returns:
        Tuple[str, str, Dict[str, Any]]: 選択された都道府県、エリア、フィルタリング済みエリアデータ
    """
    # エリアデータのロード
    area_data = load_area_data()
    if not area_data['area_data']:
        st.error("エリアデータの読み込みに失敗しました")
        return None, None, area_data # エラー時は None, None を返す

    # 検索フィルタリング
    filter_state = st.session_state.filter_state # filter_stateをstate managerから取得
    filtered_data = filter_areas(area_data, filter_state['search_query'])

    # エリアセレクターUIの表示
    selected_prefecture, selected_area = display_area_selector(filtered_data, is_processing)

    # 新規エリア追加処理
    ui_state = st.session_state.ui_state
    if ui_state['new_area_data']['add_button_clicked']: # ボタンがクリックされたか確認
        handle_add_new_area(ui_state['new_area_data'])
        ui_state['new_area_data']['add_button_clicked'] = False # ボタンクリック状態をリセット

    return selected_prefecture, selected_area, filtered_data