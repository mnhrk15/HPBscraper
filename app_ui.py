"""
app_ui.py - StreamlitアプリケーションのUIコンポーネントモジュール

このモジュールは、Streamlitアプリケーションのユーザーインターフェースコンポーネントを提供します。
エリアセレクター、検索フィルター、統計情報表示、進捗表示、サロンデータ表示などのUI要素を定義します。
"""

import streamlit as st
from typing import Dict, List, Tuple, Any
import pandas as pd


def display_area_selector(area_data: Dict[str, Any], is_processing: bool) -> Tuple[str, str]:
    """
    階層的なエリア選択UIを表示します。

    Args:
        area_data: エリアデータ辞書
        is_processing: 処理中フラグ

    Returns:
        Tuple[str, str]: 選択された都道府県とエリア
    """
    selected_prefecture = None
    selected_area = None

    # エリア選択UI
    with st.sidebar.expander("エリアを選択", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            selected_prefecture = st.selectbox(
                "都道府県を選択",
                options=area_data['prefectures'],
                key="prefecture_selector",
                disabled=is_processing
            )
            
            # 都道府県の統計情報を表示
            if selected_prefecture:
                prefecture_data = area_data['area_data'][selected_prefecture]
                st.info(f"""
                    {selected_prefecture}の統計:
                    - エリア数: {len(prefecture_data['areas'])}
                    - 総サロン数: {prefecture_data['total_salons']:,}
                """)
        
        with col2:
            # 選択された都道府県のエリアリストを取得
            available_areas = []
            if selected_prefecture:
                available_areas = [
                    area['area'] for area in area_data['area_data'][selected_prefecture]['areas']
                ]
            
            selected_area = st.selectbox(
                "エリアを選択",
                options=available_areas,
                key="area_selector",
                disabled=is_processing
            )
            
            # エリアの詳細情報を表示
            if selected_area and selected_prefecture:
                area_info = next(
                    (area for area in area_data['area_data'][selected_prefecture]['areas'] 
                    if area['area'] == selected_area),
                    None
                )
                if area_info:
                    st.info(f"""
                        {selected_area}の統計:
                        - サロン数: {area_info['estimated_salons']:,}
                    """)
                    
    return selected_prefecture, selected_area

def display_search_filters() -> str:
    """
    検索・フィルタリングUIを表示します。

    Returns:
        str: 入力された検索クエリ
    """
    with st.sidebar.expander("検索フィルター", expanded=st.session_state.ui_state['show_filters']):
        st.text_input(
            "エリア名で検索",
            value=st.session_state.filter_state['search_query'],
            placeholder="エリア名を入力...",
            key="search_input",
            on_change=st.session_state.on_search_change_callback # コールバック関数を使用
        )
        
        st.session_state.ui_state['show_filters'] = True
        
        return st.session_state.filter_state['search_query']

def display_statistics(original_data: Dict[str, Any], filtered_data: Dict[str, Any]) -> None:
    """
    検索結果の統計情報を表示します。

    Args:
        original_data: フィルタリング前のエリアデータ
        filtered_data: フィルタリング後のエリアデータ
    """
    with st.expander("統計情報", expanded=st.session_state.ui_state['show_statistics']):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("全体")
            st.write(f"""
                - 都道府県数: {len(original_data['prefectures']):,}
                - エリア総数: {original_data['total_areas']:,}
                - サロン総数: {original_data['total_salons']:,}
            """)
        
        with col2:
            st.subheader("検索結果")
            st.write(f"""
                - 該当都道府県数: {len(filtered_data['prefectures']):,}
                - 該当エリア数: {filtered_data['total_areas']:,}
                - 該当サロン数: {filtered_data['total_salons']:,}
            """)
        
        if filtered_data['total_areas'] > 0:
            st.subheader("サロン数トップ5エリア")
            top_areas = []
            for prefecture in filtered_data['prefectures']:
                for area in filtered_data['area_data'][prefecture]['areas']:
                    top_areas.append({
                        'prefecture': prefecture,
                        'area': area['area'],
                        'salons': area['estimated_salons']
                    })
            
            top_areas.sort(key=lambda x: x['salons'], reverse=True)
            for i, area in enumerate(top_areas[:5], 1):
                st.write(f"{i}. {area['prefecture']} {area['area']}: {area['salons']:,}サロン")

def display_progress_ui() -> None:
    """
    進捗状況のUIを更新します。
    - プログレスバーの更新
    - ステータスメッセージの更新
    - 進捗メトリクスの更新
    """
    if st.session_state.progress_placeholder is not None:
        progress = st.session_state.processing_state['progress'] / 100
        st.session_state.progress_placeholder.progress(progress)
    
    if st.session_state.status_placeholder is not None:
        st.session_state.status_placeholder.write(st.session_state.processing_state['status_message'])
    
    if st.session_state.metrics_placeholder is not None and st.session_state.processing_state['progress_info']:
        with st.session_state.metrics_placeholder:
            st.empty()
            display_progress_metrics(st.session_state.processing_state['progress_info'])

def display_progress_metrics(progress_info: Dict[str, Any]) -> None:
    """
    進捗情報をメトリクスとして表示します。

    Args:
        progress_info: 進捗情報を含む辞書
    """
    if not progress_info:
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("処理済み", f"{progress_info['processed']}/{progress_info['total']}")
    with col2:
        st.metric("成功", progress_info['success'])
    with col3:
        st.metric("エラー", progress_info['error'])
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.metric("進捗率", f"{progress_info['progress']:.1f}%")
    with col5:
        st.metric("平均処理時間", f"{progress_info['avg_time']:.1f}秒/件")
    with col6:
        st.metric("残り時間", progress_info['eta'])

def display_salon_data(salon_details: List[Dict]) -> None:
    """
    スクレイピングしたサロンデータを表形式で表示
    """
    if not salon_details:
        return

    # DataFrame作成
    df = st.session_state.salon_data_df =  pd.DataFrame(salon_details) # DataFrameをセッションステートに保存

    # 表示する固定列を指定
    columns = ["サロン名", "電話番号", "住所", "スタッフ数", "サロンURL"]

    # データの表示
    st.dataframe(
        df[columns],
        use_container_width=True,
        height=400,
        column_config={
            "サロンURL": st.column_config.LinkColumn("サロンURL")
        }
    )

    # 基本統計情報の表示
    st.subheader("基本統計情報")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("総サロン数", len(df))
    
    with col2:
        staff_counts = df["スタッフ数"].str.extract(r'(\d+)').astype(float)
        avg_staff = staff_counts[0].mean()
        st.metric("平均スタッフ数", f"{avg_staff:.1f}")
    
    with col3:
        success_rate = (len(df) / len(salon_details)) * 100
        st.metric("データ取得成功率", f"{success_rate:.1f}%")

def display_main_ui(is_processing: bool, should_stop: bool) -> None:
    """
    メインエリアのUI要素を表示します（ボタン、使い方など）。

    Args:
        is_processing: 処理中フラグ
        should_stop: 停止フラグ
    """
    st.markdown("""
    ### 使い方
    1. サイドバーでスクレイピングしたいエリアを選択
    2. 「スクレイピング開始」ボタンをクリック
    """)
    
    # ボタンのレイアウト
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button(
            "スクレイピング開始",
            type="primary",
            disabled=is_processing,
            key="start_button",
            use_container_width=True,
            on_click=st.session_state.handle_start_callback # コールバック関数を使用
        ):
            pass # コールバックで処理

    with col2:
        if st.button(
            "処理を中断",
            type="secondary",
            disabled=not is_processing or should_stop,
            key="stop_button",
            use_container_width=True,
            on_click=st.session_state.handle_stop_callback # コールバック関数を使用
        ):
            pass # コールバックで処理

    # 進捗バーとステータス表示のプレースホルダーを作成
    st.session_state.progress_placeholder = st.empty()
    st.session_state.status_placeholder = st.empty()
    st.session_state.metrics_placeholder = st.empty()

def display_status_message(status_message: str, should_stop: bool, is_processing: bool) -> None:
    """
    ステータスメッセージを表示します。

    Args:
        status_message: 表示するメッセージ
        should_stop: 停止フラグ
        is_processing: 処理中フラグ
    """
    if status_message:
        if should_stop:
            st.warning(status_message)
            # 中断完了後、状態をリセット (app_state_managerに移動)
            if not is_processing:
                st.session_state.reset_processing_state_callback() # コールバック関数を使用
        elif is_processing:
            st.info(status_message)
        else:
            st.success(status_message)

def display_app_header() -> None:
    """
    アプリケーションのヘッダーを表示します。
    """
    st.title("サロンスクレイピングアプリ")
    st.markdown("""
        このアプリは、指定されたエリアの美容室情報を自動的に収集します。
        サイドバーからエリアを選択し、「スクレイピング開始」ボタンをクリックしてください。
    """)
