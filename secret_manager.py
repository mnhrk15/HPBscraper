"""
secret_manager.py - シークレット管理モジュール

アプリケーションで使用するシークレット情報の管理と安全な取得を行います。
"""
import streamlit as st
import logging
from typing import Any, Dict, Optional

# デフォルト値
DEFAULT_CONFIG = {
    "rate_limit": 1.0,
    "max_workers": 4,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def get_secret(key: str, default: Any = None) -> Any:
    """
    シークレット値を安全に取得します。

    Args:
        key: 取得するシークレットのキー
        default: キーが存在しない場合のデフォルト値

    Returns:
        Any: 取得したシークレット値またはデフォルト値
    """
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception as e:
        logging.warning(f"シークレット '{key}' の取得に失敗しました: {e}")
    
    # デフォルト値があればそれを返す
    if default is not None:
        return default
    
    # デフォルト設定から取得を試みる
    if key in DEFAULT_CONFIG:
        return DEFAULT_CONFIG[key]
    
    # 何も見つからない場合はNone
    return None

def get_all_config() -> Dict[str, Any]:
    """
    全ての設定値を取得します。シークレットにある値が優先され、
    ない場合はデフォルト値が使用されます。

    Returns:
        Dict[str, Any]: 設定値の辞書
    """
    config = DEFAULT_CONFIG.copy()
    
    # シークレットの値で上書き
    try:
        for key in DEFAULT_CONFIG:
            if key in st.secrets:
                config[key] = st.secrets[key]
    except Exception as e:
        logging.error(f"シークレット設定の読み込み中にエラーが発生しました: {e}")
    
    return config

def validate_secrets() -> Dict[str, str]:
    """
    必須のシークレット設定が正しく設定されているかを検証します。

    Returns:
        Dict[str, str]: エラーメッセージの辞書（キー: エラーID, 値: エラーメッセージ）
    """
    errors = {}
    
    # パスワードの検証
    try:
        if "password" not in st.secrets:
            errors["missing_password"] = "パスワードが設定されていません。.streamlit/secrets.tomlファイルを確認してください。"
        elif not st.secrets["password"] or st.secrets["password"] == "YOUR_PASSWORD_HERE":
            errors["invalid_password"] = "デフォルトまたは空のパスワードが設定されています。セキュリティのため変更してください。"
    except Exception:
        errors["secrets_error"] = "シークレット設定の読み込みに失敗しました。Streamlit Cloudの設定を確認してください。"
    
    return errors

def is_development_environment() -> bool:
    """
    開発環境かどうかを判定します。

    Returns:
        bool: 開発環境の場合はTrue
    """
    try:
        return bool(st.secrets.get("environment") == "development")
    except:
        # シークレットにアクセスできない場合は本番環境と見なす
        return False
