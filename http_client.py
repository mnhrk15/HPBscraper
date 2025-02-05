"""
HTTPクライアントモジュール
リトライ機能付きのHTTPリクエスト処理を提供
"""
import time
import logging
import random
import requests
from typing import Optional, Union, Dict
from config import (
    HEADERS, MAX_RETRIES, RETRY_DELAY, REQUEST_TIMEOUT,
    MAX_BACKOFF, RETRY_CODES, RETRY_EXCEPTIONS
)

class HTTPClient:
    @staticmethod
    def calculate_backoff(attempt: int, base_delay: int = RETRY_DELAY) -> float:
        """
        エクスポネンシャルバックオフ時間を計算

        Args:
            attempt (int): リトライ試行回数
            base_delay (int): 基本待機時間

        Returns:
            float: 待機時間（秒）
        """
        # エクスポネンシャルバックオフ + ジッター
        delay = min(MAX_BACKOFF, base_delay * (2 ** attempt))
        jitter = random.uniform(0, 0.1 * delay)  # 10%のジッター
        return delay + jitter

    @staticmethod
    def should_retry(response: Optional[requests.Response], exception: Optional[Exception]) -> bool:
        """
        リトライすべきかどうかを判断

        Args:
            response (Optional[requests.Response]): レスポンスオブジェクト
            exception (Optional[Exception]): 発生した例外

        Returns:
            bool: リトライすべきかどうか
        """
        if exception and isinstance(exception, RETRY_EXCEPTIONS):
            return True
        
        if response:
            return response.status_code in RETRY_CODES
        
        return False

    @staticmethod
    def get(url: str, custom_headers: Dict = None) -> Optional[requests.Response]:
        """
        リトライ機能付きのGETリクエストを実行

        Args:
            url (str): リクエスト先URL
            custom_headers (Dict, optional): カスタムヘッダー

        Returns:
            Optional[requests.Response]: レスポンスオブジェクト、エラー時はNone
        """
        headers = {**HEADERS, **(custom_headers or {})}
        session = requests.Session()
        
        for attempt in range(MAX_RETRIES):
            response = None
            exception = None
            
            try:
                response = session.get(
                    url,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT
                )
                
                if response.ok:
                    return response
                
                response.raise_for_status()
                
            except Exception as e:
                exception = e
                logging.debug(f"リクエストエラー (試行 {attempt + 1}/{MAX_RETRIES}): {url} - {str(e)}")
            
            if not HTTPClient.should_retry(response, exception):
                error_msg = str(exception) if exception else f"ステータスコード: {response.status_code}"
                logging.error(f"リトライ不可能なエラー: {url} - {error_msg}")
                return response if response else None
            
            if attempt < MAX_RETRIES - 1:
                backoff = HTTPClient.calculate_backoff(attempt)
                logging.info(f"リトライ待機 {backoff:.2f}秒 (試行 {attempt + 1}/{MAX_RETRIES}): {url}")
                time.sleep(backoff)
            else:
                logging.error(f"最大リトライ回数に達しました: {url}")
        
        return None