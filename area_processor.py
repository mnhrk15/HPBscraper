"""
エリアデータの処理を行うモジュール
サロン数の取得を行う
"""
import logging
import re
import time
from typing import Dict, Optional, Tuple
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

class AreaProcessor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        })
        self.setup_logging()

    def setup_logging(self):
        """ロギングの設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='area_processing.log'
        )

    def get_salon_count(self, url: str) -> int:
        """URLからサロン数を取得"""
        try:
            # URLが特定のサロンページの場合はスキップ
            if 'sacX421' in url:
                return 0

            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 検索結果の件数を取得（複数のパターンに対応）
            count = 0
            
            # パターン1: ヘッダーの検索結果件数
            header_count = soup.select_one('span.numberOfResult')
            if header_count:
                text = header_count.text.strip()
                match = re.search(r'(\d+)', text)
                if match:
                    count = int(match.group(1))
                    logging.info(f"Found count from header: {count} for {url}")
                    return count
            
            # パターン2: ページネーション情報
            pagination = soup.select_one('div.pagination')
            if pagination:
                text = pagination.text.strip()
                match = re.search(r'全(\d+)件', text)
                if match:
                    count = int(match.group(1))
                    logging.info(f"Found count from pagination: {count} for {url}")
                    return count
            
            # パターン3: サロンリストの要素数をカウント
            salon_items = soup.select('li.slnList')
            if salon_items:
                count = len(salon_items)
                logging.info(f"Found count from salon list: {count} for {url}")
                return count
            
            logging.warning(f"サロン数を取得できませんでした（セレクターにマッチせず）: {url}")
            return 0

        except requests.exceptions.RequestException as e:
            logging.error(f"Request error for {url}: {e}")
            return 0
        except Exception as e:
            logging.error(f"Unexpected error getting salon count for {url}: {e}")
            return 0

    def process_areas(self, input_csv: str, output_csv: str):
        """エリアデータの処理メイン関数"""
        try:
            # 現在のCSVを読み込み
            df = pd.read_csv(input_csv)
            
            # サロン数を取得
            print("サロン数を取得中...")
            df['estimated_salons'] = 0  # 初期値を設定
            
            with tqdm(total=len(df)) as pbar:
                for idx, row in df.iterrows():
                    salon_count = self.get_salon_count(row['url'])
                    df.at[idx, 'estimated_salons'] = salon_count
                    time.sleep(3)  # レート制限のための待機時間を3秒に増やす
                    pbar.update(1)
            
            # 列の順序を変更して保存
            df = df[['area', 'url', 'estimated_salons']]
            
            # サロン数の統計を表示
            print("\nサロン数の統計:")
            print(f"合計サロン数: {df['estimated_salons'].sum():,}")
            print(f"平均サロン数: {df['estimated_salons'].mean():.1f}")
            print(f"最大サロン数: {df['estimated_salons'].max():,}")
            print(f"サロン数が0のエリア数: {len(df[df['estimated_salons'] == 0])}")
            
            df.to_csv(output_csv, index=False)
            print(f"\n処理が完了しました。結果は {output_csv} に保存されました。")
            
        except Exception as e:
            logging.error(f"エラーが発生しました: {e}")
            raise

def main():
    processor = AreaProcessor()
    processor.process_areas('area.csv', 'area_structured.csv')

if __name__ == "__main__":
    main()
