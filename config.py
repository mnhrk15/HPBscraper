"""
設定ファイル
スクレイピングの設定や定数を管理するモジュール
"""
import logging
import requests
import os
import platform
import psutil
from typing import Dict, List, Any, Optional

# システムリソース検出
def get_system_resources() -> Dict[str, Any]:
    """
    システムリソース情報を取得します。
    
    Returns:
        Dict[str, Any]: CPU数、メモリ容量、OSの種類などの情報
    """
    try:
        return {
            "cpu_count": os.cpu_count() or 2,
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "platform": platform.system(),
            "is_64bit": platform.architecture()[0] == "64bit"
        }
    except Exception as e:
        logging.warning(f"システムリソース情報の取得に失敗しました: {e}")
        return {"cpu_count": 2, "memory_gb": 4.0, "platform": "Unknown", "is_64bit": True}


# システムリソースに基づく最適な並列ワーカー数の計算
def calculate_optimal_workers() -> int:
    """
    システムリソースに基づいて最適なワーカー数を計算します。
    
    Returns:
        int: 推奨ワーカー数
    """
    try:
        resources = get_system_resources()
        cpu_count = resources["cpu_count"]
        memory_gb = resources["memory_gb"]
        
        # CPUコア数と利用可能メモリを考慮して最適値を計算
        if memory_gb < 2:
            return max(1, cpu_count // 4)  # 低メモリ環境
        elif memory_gb < 4:
            return max(2, cpu_count // 2)  # 中メモリ環境
        else:
            return max(4, min(cpu_count - 1, 8))  # 高メモリ環境（最大8）
    except Exception as e:
        logging.warning(f"最適ワーカー数の計算に失敗しました: {e}")
        return 4  # デフォルト値

# HTTPリクエストヘッダー
HEADERS: Dict[str, str] = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
}

# リトライ設定
MAX_RETRIES: int = 3
RETRY_DELAY: int = 1
MAX_BACKOFF: int = 60  # 最大バックオフ時間（秒）
RETRY_CODES: List[int] = [429, 500, 502, 503, 504]  # リトライ対象のステータスコード
RETRY_EXCEPTIONS = (
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
    requests.exceptions.RequestException
)

# スクレイピング設定
REQUEST_TIMEOUT: int = 30
SCRAPING_DELAY: int = 1

# 並列処理設定 - 動的に最適化
MAX_WORKERS: int = calculate_optimal_workers()  # 同時実行するワーカー数を最適化
CHUNK_SIZE: int = 20  # 一度に処理するURLの数を増加
RATE_LIMIT: float = 0.5  # リクエスト間隔（秒）を短縮

# メモリ最適化設定
MEMORY_EFFICIENT_MODE: bool = False  # 大量データ処理時に有効化
MAX_CACHE_SIZE: int = 1000  # キャッシュする最大アイテム数
GC_THRESHOLD: int = 5000  # ガベージコレクションのトリガー閾値

# 設定のオーバーライド（シークレットからの読み込み）
try:
    import streamlit as st
    # シークレットから設定を読み込み
    if hasattr(st, "secrets"):
        if "max_workers" in st.secrets:
            try:
                MAX_WORKERS = int(st.secrets["max_workers"])
                logging.info(f"ワーカー数を設定から読み込み: {MAX_WORKERS}")
            except:
                pass
        
        if "rate_limit" in st.secrets:
            try:
                RATE_LIMIT = float(st.secrets["rate_limit"])
                logging.info(f"レート制限を設定から読み込み: {RATE_LIMIT}")
            except:
                pass
        
        if "memory_efficient" in st.secrets:
            try:
                MEMORY_EFFICIENT_MODE = bool(st.secrets["memory_efficient"])
                logging.info(f"メモリ効率モード: {MEMORY_EFFICIENT_MODE}")
            except:
                pass
except ImportError:
    # streamlitが利用できない環境（CLIモードなど）
    pass

# ロギング設定
LOG_FORMAT: str = '%(asctime)s - %(levelname)s - %(message)s'
LOG_FILE: str = 'scraping.log'
LOG_LEVEL: int = logging.DEBUG

# 電話番号スクレイピングセレクター
PHONE_SELECTORS: List[str] = [
    'td.fs16.b',
    '#mainContents table tbody tr td',
    'td[class*="fs16"]',
    'tr td:not([class])'
]

# サロン情報セレクター
SALON_SELECTORS = {
    'name': '#headSummary',
    'staff_count': 'td.w208.vaT',
    'address': 'td[colspan="3"]',
    'links': '#mainContents > div.mT30.mB20 ul.mT10 a'
}


def get_memory_limit() -> int:
    """
    現在の環境に適したメモリ制限を取得します。
    
    Returns:
        int: バイト単位のメモリ制限
    """
    try:
        mem = psutil.virtual_memory()
        # 利用可能メモリの80%を上限とする
        return int(mem.available * 0.8)
    except Exception:
        # デフォルト値（1GB）
        return 1024 * 1024 * 1024