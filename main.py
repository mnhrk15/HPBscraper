"""
メインモジュール
スクレイピングの実行を制御
"""
import logging
from typing import Optional
from logging_setup import setup_logging
from parallel_scraper import ParallelScraper
from excel_exporter import ExcelExporter

def main() -> Optional[str]:
    """
    メイン実行関数
    スクレイピングを実行しExcelファイルを出力

    Returns:
        Optional[str]: 出力されたExcelファイルのパス、エラー時はNone
    """
    setup_logging()
    
    print("ホットペッパービューティースクレイパーを開始します...")
    area_url = input("エリアページURLを入力してください: ")
    
    logging.info(f"スクレイピング開始: {area_url}")
    print("サロンURLの収集を開始します...")
    
    # 並列スクレイパーの初期化
    scraper = ParallelScraper()
    
    # サロンURL収集
    salon_urls = scraper.scrape_salon_urls(area_url)
    if not salon_urls:
        logging.error("サロンURLが見つかりませんでした。")
        print("サロンURLが見つかりませんでした。終了します。")
        return None
        
    print(f"サロン数: {len(salon_urls)}")
    print("サロン情報の取得を開始します...")
    
    # 並列でサロン情報を収集
    salon_data_list = scraper.scrape_salon_details_parallel(salon_urls)

    if not salon_data_list:
        logging.error("サロンデータが取得できませんでした。")
        print("サロンデータが取得できませんでした。終了します。")
        return None

    print(f"取得完了: {len(salon_data_list)}件のサロン情報")
    
    # Excelファイルに出力
    try:
        exporter = ExcelExporter()
        output_path = exporter.export_salon_data(salon_data_list)
        print(f"Excelファイルを出力しました: {output_path}")
        logging.info(f"Excelファイル出力完了: {output_path}")
        print("スクレイピングが完了しました。")
        return output_path
    except Exception as e:
        logging.error(f"Excelファイルの出力に失敗しました: {e}")
        print("Excelファイルの出力に失敗しました。")
        return None

if __name__ == "__main__":
    main()