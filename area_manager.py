"""
エリアデータ管理モジュール

このモジュールは、エリアデータの読み込み、検証、保存を管理します。
主な機能：
- CSVファイルからのエリアデータの読み込み
- 新規エリアデータの検証
- エリアデータのCSVファイルへの保存
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlparse

class AreaManager:
    def __init__(self, csv_path: str = 'area.csv'):
        """
        エリアマネージャーの初期化

        Args:
            csv_path: エリアデータを保存するCSVファイルのパス
        """
        self.csv_path = csv_path
        self.df = self._load_csv()

    def _load_csv(self) -> pd.DataFrame:
        """
        CSVファイルからデータを読み込む

        Returns:
            pd.DataFrame: 読み込んだデータフレーム
        """
        try:
            if Path(self.csv_path).exists():
                return pd.read_csv(self.csv_path)
            return pd.DataFrame(columns=['prefecture', 'area', 'url', 'estimated_salons'])
        except Exception as e:
            logging.error(f"CSVファイルの読み込みに失敗: {str(e)}")
            return pd.DataFrame(columns=['prefecture', 'area', 'url', 'estimated_salons'])

    def validate_area_data(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """
        エリアデータのバリデーション

        Args:
            data: 検証するエリアデータ

        Returns:
            tuple[bool, str]: (検証結果, エラーメッセージ)
        """
        # 必須フィールドの確認
        required_fields = ['prefecture', 'area', 'url', 'estimated_salons']
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return False, f"{field}は必須項目です"

        # 県名とエリア名の文字数制限
        if len(data['prefecture']) > 10:
            return False, "県名は10文字以内で入力してください"
        if len(data['area']) > 30:
            return False, "エリア名は30文字以内で入力してください"

        # URLの形式確認
        try:
            result = urlparse(data['url'])
            if not all([result.scheme, result.netloc]):
                return False, "URLの形式が正しくありません"
            
            # HPBのURLであることを確認
            if not (
                result.netloc == 'beauty.hotpepper.jp' and
                any(f'/svcS{c}/' in result.path for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ') and
                'mac' in result.path and
                'salon' in result.path
            ):
                return False, "Hot Pepper Beautyのエリアページ（https://beauty.hotpepper.jp/svcS*/mac*/salon/...）を入力してください"
        except Exception:
            return False, "URLの形式が正しくありません"

        # サロン数の検証
        try:
            salon_count = int(data['estimated_salons'])
            if salon_count <= 0:
                return False, "サロン数は1以上の整数である必要があります"
            if salon_count > 10000:  # 現実的な上限値を設定
                return False, "サロン数が上限（10,000）を超えています"
        except ValueError:
            return False, "サロン数は整数で入力してください"

        # 重複チェック
        if self.is_duplicate(data['prefecture'], data['area']):
            return False, "指定された県名とエリア名の組み合わせは既に存在します"

        return True, ""

    def is_duplicate(self, prefecture: str, area: str) -> bool:
        """
        県名とエリア名の組み合わせが既に存在するかチェック

        Args:
            prefecture: 県名
            area: エリア名

        Returns:
            bool: 重複している場合はTrue
        """
        return bool(len(self.df[
            (self.df['prefecture'] == prefecture) & 
            (self.df['area'] == area)
        ]))

    def add_area(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """
        新規エリアを追加

        Args:
            data: 追加するエリアデータ

        Returns:
            tuple[bool, str]: (追加結果, メッセージ)
        """
        # データの検証
        is_valid, message = self.validate_area_data(data)
        if not is_valid:
            return False, message

        try:
            # データフレームに追加
            self.df = pd.concat([
                self.df, 
                pd.DataFrame([data])
            ], ignore_index=True)
            
            # CSVに保存
            self.save_areas()
            return True, f"エリア '{data['prefecture']} {data['area']}' が正常に追加されました"
        except Exception as e:
            logging.error(f"エリア追加中にエラーが発生: {str(e)}")
            return False, f"エリアの追加に失敗しました: {str(e)}"

    def save_areas(self) -> None:
        """エリアデータをCSVファイルに保存"""
        try:
            self.df.to_csv(self.csv_path, index=False)
        except Exception as e:
            logging.error(f"CSVファイルの保存に失敗: {str(e)}")
            raise
