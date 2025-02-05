"""
ロギング設定モジュール
アプリケーション全体のロギング設定を管理
"""
import logging
from config import LOG_FORMAT, LOG_FILE, LOG_LEVEL

def setup_logging() -> None:
    """
    ロギングの初期設定を行う
    グローバルなロギング設定を構成し、ファイルとコンソール出力を設定
    """
    # ハンドラーを作成（filemode='w'で上書きモード）
    file_handler = logging.FileHandler(
        LOG_FILE,
        mode='w',  # 'w'モードで上書き
        encoding='utf-8'
    )
    console_handler = logging.StreamHandler()

    # 各ハンドラーのフォーマットを設定
    formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # ルートロガーの設定
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)

    # 既存のハンドラーをクリア
    root_logger.handlers = []

    # 新しいハンドラーを追加
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # 初期化完了ログ
    logging.info('ログシステムを初期化しました')