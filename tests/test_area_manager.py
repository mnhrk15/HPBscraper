"""
AreaManagerのユニットテスト

このモジュールでは、AreaManagerクラスの各機能をテストします。
主なテスト項目：
- データ検証機能
- エリアの追加機能
- CSVファイルの読み書き
- エラーケースの処理
"""

import unittest
import pandas as pd
import tempfile
import os
from pathlib import Path
from area_manager import AreaManager

class TestAreaManager(unittest.TestCase):
    def setUp(self):
        """テストの前準備"""
        # 一時ファイルを作成してテストデータを書き込む
        self.temp_dir = tempfile.mkdtemp()
        self.csv_path = os.path.join(self.temp_dir, 'test_area.csv')
        self.test_data = pd.DataFrame({
            'prefecture': ['東京都'],
            'area': ['渋谷'],
            'url': ['https://example.com/shibuya'],
            'estimated_salons': [100]
        })
        self.test_data.to_csv(self.csv_path, index=False)
        self.manager = AreaManager(self.csv_path)

    def tearDown(self):
        """テスト後のクリーンアップ"""
        # 一時ファイルとディレクトリを削除
        if os.path.exists(self.csv_path):
            os.remove(self.csv_path)
        os.rmdir(self.temp_dir)

    def test_load_csv(self):
        """CSVファイルの読み込みテスト"""
        self.assertEqual(len(self.manager.df), 1)
        self.assertEqual(self.manager.df.iloc[0]['prefecture'], '東京都')
        self.assertEqual(self.manager.df.iloc[0]['area'], '渋谷')

    def test_validate_valid_data(self):
        """正常なデータのバリデーションテスト"""
        valid_data = {
            'prefecture': '大阪府',
            'area': '心斎橋',
            'url': 'https://example.com/shinsaibashi',
            'estimated_salons': 50
        }
        is_valid, message = self.manager.validate_area_data(valid_data)
        self.assertTrue(is_valid)
        self.assertEqual(message, '')

    def test_validate_missing_field(self):
        """必須フィールド欠落のテスト"""
        invalid_data = {
            'prefecture': '大阪府',
            'area': '心斎橋',
            'url': 'https://example.com/shinsaibashi'
            # estimated_salonsが欠落
        }
        is_valid, message = self.manager.validate_area_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn('estimated_salons', message)

    def test_validate_invalid_url(self):
        """不正なURLのテスト"""
        invalid_data = {
            'prefecture': '大阪府',
            'area': '心斎橋',
            'url': 'invalid-url',
            'estimated_salons': 50
        }
        is_valid, message = self.manager.validate_area_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn('URL', message)

    def test_validate_invalid_salon_count(self):
        """不正なサロン数のテスト"""
        invalid_data = {
            'prefecture': '大阪府',
            'area': '心斎橋',
            'url': 'https://example.com/shinsaibashi',
            'estimated_salons': -1
        }
        is_valid, message = self.manager.validate_area_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn('サロン数', message)

    def test_duplicate_check(self):
        """重複チェックのテスト"""
        # 既存データと同じ組み合わせ
        self.assertTrue(self.manager.is_duplicate('東京都', '渋谷'))
        # 新しい組み合わせ
        self.assertFalse(self.manager.is_duplicate('大阪府', '心斎橋'))

    def test_add_area(self):
        """エリア追加のテスト"""
        new_area = {
            'prefecture': '大阪府',
            'area': '心斎橋',
            'url': 'https://example.com/shinsaibashi',
            'estimated_salons': 50
        }
        success, message = self.manager.add_area(new_area)
        self.assertTrue(success)
        self.assertIn('正常に追加', message)
        self.assertEqual(len(self.manager.df), 2)

    def test_add_duplicate_area(self):
        """重複エリア追加のテスト"""
        duplicate_area = {
            'prefecture': '東京都',
            'area': '渋谷',
            'url': 'https://example.com/shibuya2',
            'estimated_salons': 150
        }
        success, message = self.manager.add_area(duplicate_area)
        self.assertFalse(success)
        self.assertIn('既に存在', message)
        self.assertEqual(len(self.manager.df), 1)

if __name__ == '__main__':
    unittest.main()
