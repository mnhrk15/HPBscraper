"""
URL処理ユーティリティモジュール
URL関連の処理機能を提供
"""
import logging
from urllib.parse import urlparse, urlunparse
from typing import Optional

def normalize_url(url: str) -> str:
    """
    URLから不要なパラメータを削除し正規化する

    Args:
        url (str): 正規化するURL

    Returns:
        str: 正規化されたURL
    """
    try:
        parsed_url = urlparse(url)
        normalized_path = parsed_url.path
        return urlunparse(parsed_url._replace(
            path=normalized_path,
            params='',
            query='',
            fragment=''
        ))
    except Exception as e:
        logging.error(f"URL正規化エラー: {url} - {e}")
        return url