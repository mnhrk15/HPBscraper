"""
美容室情報スクレイピングアプリケーション

このモジュールはStreamlitを使用して、美容室情報をスクレイピングするためのWebインターフェースを提供します。
主な機能：
- エリアごとの美容室情報の収集
- 並列スクレイピング処理
- 進捗状況のリアルタイム表示
- 結果のExcel出力
"""

import streamlit as st
import logging
import pandas as pd
from typing import Dict, List, Set, Optional, Any, Tuple
from logging_setup import setup_logging
from parallel_scraper import ParallelScraper
from excel_exporter import ExcelExporter
from pathlib import Path
from datetime import datetime
from area_manager import AreaManager
import time

# 定数定義
DEFAULT_CSV_PATH = 'area.csv'
PROGRESS_INITIAL_STATE = {
    'is_processing': False,
    'should_stop': False,
    'status_message': '',
    'progress': 0,
    'progress_info': {}
}

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

def init_session_state() -> None:
    """
    Streamlitのセッション状態を初期化します。
    以下の状態を管理します：
    - processing_state: スクレイピング処理の状態
    - filter_state: 検索・フィルタリングの状態
    - ui_state: UIコンポーネントの表示状態
    - 進捗表示用のプレースホルダー
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
            'show_add_area': False
        }
    
    # 進捗状態の管理用
    if 'progress_placeholder' not in st.session_state:
        st.session_state.progress_placeholder = None
    if 'status_placeholder' not in st.session_state:
        st.session_state.status_placeholder = None
    if 'metrics_placeholder' not in st.session_state:
        st.session_state.metrics_placeholder = None

    # エリアマネージャーの初期化
    if 'area_manager' not in st.session_state:
        st.session_state.area_manager = AreaManager(DEFAULT_CSV_PATH)

def update_progress_ui() -> None:
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

def display_progress_metrics(progress_info: Dict[str, Any]) -> None:
    """
    進捗情報をメトリクスとして表示します。

    Args:
        progress_info: 進捗情報を含む辞書
            - processed: 処理済み件数
            - total: 総件数
            - success: 成功件数
            - error: エラー件数
            - progress: 進捗率
            - avg_time: 平均処理時間
            - eta: 推定残り時間
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

def progress_callback(progress_info: Dict[str, Any]) -> None:
    """
    スクレイピング処理からの進捗コールバック関数。

    Args:
        progress_info: 進捗情報を含む辞書
    """
    st.session_state.processing_state['progress'] = progress_info['progress']
    st.session_state.processing_state['progress_info'] = progress_info
    update_progress_ui()

def handle_start() -> None:
    """スクレイピング処理の開始ハンドラー"""
    update_processing_state(is_processing=True, should_stop=False, status_message='処理を開始します...')
    st.rerun()

def handle_stop() -> None:
    """スクレイピング処理の停止ハンドラー"""
    if st.session_state.processing_state['is_processing']:
        if hasattr(st.session_state, 'scraper'):
            st.session_state.scraper.stop()
        update_processing_state(
            is_processing=False,
            should_stop=True,
            status_message='処理を中断しました',
            progress=0
        )
        st.rerun()

def display_area_selector(area_data: Dict[str, Any], is_processing: bool) -> Tuple[str, List[Dict[str, Any]]]:
    """
    階層的なエリア選択UIを表示します。

    Args:
        area_data: エリアデータ辞書
        is_processing: 処理中フラグ

    Returns:
        Tuple[str, List[Dict[str, Any]]]: 選択された都道府県とエリアのリスト
    """
    selected_prefecture = None
    selected_area = None

    # 新規エリア追加セクション
    with st.sidebar.expander("新規エリアを追加", expanded=st.session_state.ui_state['show_add_area']):
        st.session_state.ui_state['show_add_area'] = True
        
        st.markdown("""
        #### 新規エリアの追加方法
        1. Hot Pepper Beautyで対象エリアのページを開く
        2. URLをコピーして下記フォームに入力
        3. 必要な情報を入力して「エリアを追加」をクリック
        """)
        
        # 県名入力（既存の県名をドロップダウンで表示）
        existing_prefectures = sorted(area_data['prefectures'])
        prefecture_input = st.selectbox(
            "県名",
            options=existing_prefectures,
            key='new_prefecture',
            help="エリアを追加する都道府県を選択してください"
        )

        # エリア名入力
        area_input = st.text_input(
            "エリア名",
            key='new_area',
            placeholder="例: 渋谷",
            help="エリア名を入力してください（30文字以内）"
        )
        
        # URL入力
        url_input = st.text_input(
            "URL",
            key='new_url',
            placeholder="https://beauty.hotpepper.jp/...",
            help="Hot Pepper Beautyのエリアページ（SA...）のURLを入力してください"
        )
        
        # サロン数入力
        salon_count = st.number_input(
            "推定サロン数",
            min_value=1,
            max_value=10000,
            value=1,
            step=1,
            key='new_salon_count',
            help="エリア内の推定サロン数を入力してください（1〜10,000）"
        )

        # 追加ボタン
        add_button = st.button(
            "エリアを追加",
            key='add_area_button',
            type="primary",
            use_container_width=True
        )

        # エリア追加処理
        if add_button:
            if not prefecture_input or not area_input or not url_input:
                st.error("すべての項目を入力してください")
            else:
                with st.spinner("エリアを追加中..."):
                    new_area_data = {
                        'prefecture': prefecture_input,
                        'area': area_input,
                        'url': url_input,
                        'estimated_salons': salon_count
                    }
                    
                    success, message = st.session_state.area_manager.add_area(new_area_data)
                    
                    # 処理結果に応じてフィードバックを表示
                    if success:
                        # 成功メッセージを表示
                        st.success(f"""
                        ✨ 新しいエリアが追加されました！

                        **追加されたエリア情報**
                        - 県名: {prefecture_input}
                        - エリア: {area_input}
                        - 推定サロン数: {salon_count}件
                        """)
                        
                        # 少し待ってからリロード
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(message)

    # 既存のエリア選択UI
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

def on_search_change() -> None:
    """検索入力変更時のコールバック処理"""
    st.session_state.filter_state['search_query'] = st.session_state.search_input

def display_search_filters() -> str:
    """
    検索・フィルタリングUIを表示します。

    Returns:
        str: 入力された検索クエリ
    """
    with st.expander("検索フィルター", expanded=st.session_state.ui_state['show_filters']):
        st.text_input(
            "エリア名で検索",
            value=st.session_state.filter_state['search_query'],
            placeholder="エリア名を入力...",
            key="search_input",
            on_change=on_search_change
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

def display_salon_data(salon_details: List[Dict]) -> None:
    """
    スクレイピングしたサロンデータを表形式で表示
    """
    if not salon_details:
        return

    # DataFrame作成
    df = pd.DataFrame(salon_details)

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

def main() -> None:
    """
    アプリケーションのメインエントリーポイント。
    - ログ設定の初期化
    - セッション状態の初期化
    - UIの構築と表示
    - スクレイピング処理の制御
    """
    # セッションステートの初期化
    init_session_state()
    
    # スクレイパーの初期化
    if 'scraper' not in st.session_state:
        st.session_state.scraper = ParallelScraper()
        st.session_state.scraper.set_progress_callback(progress_callback)
    
    # ページの設定
    st.set_page_config(
        page_title="HPBスクレイピングアプリ",
        page_icon="./assets/icon.ico",
        layout="wide"
    )
    setup_logging()
    
    st.title("HPBスクレイピングアプリ")
    
    # 処理状態の取得
    state = st.session_state.processing_state
    is_processing = state['is_processing']
    should_stop = state['should_stop']
    
    # サイドバーの設定
    with st.sidebar:
        st.markdown("### 設定")
        # 検索フィルターの表示
        search_query = display_search_filters()
        
        # エリアデータの読み込み
        area_data = load_area_data()
        if not area_data['area_data']:
            st.error("エリアデータの読み込みに失敗しました")
            return
        
        # 検索フィルタリング
        filtered_data = filter_areas(area_data, search_query)
        
        # 統計情報の表示
        display_statistics(area_data, filtered_data)
        
        # エリア選択
        selected_prefecture, selected_area = display_area_selector(filtered_data, is_processing)

        if st.sidebar.button(
            "アプリを終了",
            type="primary",
            use_container_width=True
        ):
            import os
            os._exit(0)
    
    # メインエリアのコンテンツ
    # 処理状態の表示
    if state['status_message']:
        if should_stop:
            st.warning(state['status_message'])
            # 中断完了後、状態をリセット
            if not is_processing:
                update_processing_state(
                    should_stop=False,
                    status_message='',
                    progress=0
                )
                st.rerun()
        elif is_processing:
            st.info(state['status_message'])
        else:
            st.success(state['status_message'])
    
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
            use_container_width=True
        ):
            handle_start()

    with col2:
        if st.button(
            "処理を中断",
            type="secondary",
            disabled=not is_processing or should_stop,
            key="stop_button",
            use_container_width=True
        ):
            handle_stop()

    # 進捗バーとステータス表示のプレースホルダーを作成
    st.session_state.progress_placeholder = st.empty()
    st.session_state.status_placeholder = st.empty()
    st.session_state.metrics_placeholder = st.empty()
    
    # 初期表示
    update_progress_ui()
    
    # メイン処理
    if is_processing and not should_stop:
        try:
            # エリア情報の取得と検証
            area_info = next(
                (area for area in filtered_data['area_data'][selected_prefecture]['areas'] 
                if area['area'] == selected_area),
                None
            )
            
            if not area_info:
                st.error("選択されたエリアの情報が見つかりません。")
                update_processing_state(is_processing=False)
                return
            
            area_url = area_info['url']
            scraper = st.session_state.scraper
            scraper.set_progress_callback(progress_callback)
            
            # 処理状態の更新
            update_processing_state(
                status_message=f"サロン情報収集中... ({selected_prefecture} {selected_area})",
                progress=0
            )
            
            # サロンURL収集
            salon_urls = scraper.scrape_salon_urls(area_url)
            
            if not salon_urls:
                st.warning("このエリアで有効なサロンURLが見つかりませんでした。")
                update_processing_state(is_processing=False)
                return
            
            # 以降の処理は変更なし
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
                    
                    # 完了メッセージ
                    st.success(f"""
                        スクレイピングが完了しました！
                        - 対象エリア: {selected_prefecture} {selected_area}
                        - 取得件数: {len(salon_details):,}件
                        - 保存先: output/{filename}
                    """)

                    # スクレイピング結果の表示
                    st.subheader("スクレイピング結果")
                    display_salon_data(salon_details)

                    # スクレイパーの状態をリセット
                    st.session_state.scraper.reset()
                    
                    # 処理状態をリセット
                    update_processing_state(
                        is_processing=False,
                        status_message='スクレイピングが完了しました。新しいエリアを選択して再度スクレイピングを開始できます。',
                        progress=0,
                        progress_info={}
                    )

                else:
                    st.warning("サロンが見つかりませんでした。")
        except Exception as e:
            error_message = f"エラーが発生しました: {str(e)}"
            update_processing_state(
                is_processing=False,
                status_message=error_message,
                progress=0
            )
            logging.error(f"Error during scraping: {str(e)}")
            st.error(error_message)
            st.rerun()

if __name__ == "__main__":
    main()