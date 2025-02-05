"""
設定ファイル
スクレイピングの設定や定数を管理するモジュール
"""
import logging
import requests
from typing import Dict, List

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

# 並列処理設定
MAX_WORKERS: int = 4  # 同時実行するワーカー数
CHUNK_SIZE: int = 10  # 一度に処理するURLの数
RATE_LIMIT: float = 1.0  # リクエスト間隔（秒）

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