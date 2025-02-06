"""
Excel出力モジュール
スクレイピングしたデータをExcelファイルに出力
"""
import openpyxl
from datetime import datetime
from typing import List, Dict
import io

class ExcelExporter:
    @staticmethod
    def export_salon_data(salon_data_list: List[Dict], file_name: str = None) -> str:
        """
        サロンデータをExcelファイルに出力

        Args:
            salon_data_list (List[Dict]): サロンデータのリスト
            file_name (str, optional): 出力ファイル名

        Returns:
            str: 保存したファイルのパス
        """
        if not file_name:
            file_name = f"hotpepper_beauty_salons_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"

        workbook = openpyxl.Workbook()
        sheet = workbook.active
        
        # ヘッダーの設定
        header = ["サロン名", "電話番号", "住所", "スタッフ数", "関連リンク", "関連リンク数", "サロンURL"]
        sheet.append(header)

        # データの書き込み
        for data in salon_data_list:
            sheet.append([data.get(h, '') for h in header])

        workbook.save(file_name)
        return file_name

    @staticmethod
    def get_excel_bytes(salon_data_list: List[Dict]) -> tuple[bytes, str]:
        """
        サロンデータをExcelファイルのバイトデータとして返す

        Args:
            salon_data_list (List[Dict]): サロンデータのリスト

        Returns:
            tuple[bytes, str]: Excelファイルのバイトデータとファイル名
        """
        file_name = f"hotpepper_beauty_salons_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        
        # ヘッダーの設定
        header = ["サロン名", "電話番号", "住所", "スタッフ数", "関連リンク", "関連リンク数", "サロンURL"]
        sheet.append(header)

        # データの書き込み
        for data in salon_data_list:
            sheet.append([data.get(h, '') for h in header])

        # メモリ上でバイトデータとして保存
        excel_bytes = io.BytesIO()
        workbook.save(excel_bytes)
        return excel_bytes.getvalue(), file_name