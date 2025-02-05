"""
スクレイピングモジュール
サロン情報のスクレイピング機能を提供
"""
import logging
import re
import time
from typing import Dict, List, Optional, Callable
from bs4 import BeautifulSoup
from http_client import HTTPClient
from url_utils import normalize_url
from config import PHONE_SELECTORS, SCRAPING_DELAY, SALON_SELECTORS

class BeautyScraper:
    @staticmethod
    def scrape_phone_number(tel_url: str) -> str:
        """
        電話番号ページから電話番号をスクレイピング

        Args:
            tel_url (str): 電話番号ページのURL

        Returns:
            str: スクレイピングした電話番号
        """
        try:
            response = HTTPClient.get(tel_url)
            if not response:
                return "電話番号取得エラー"

            soup = BeautifulSoup(response.content, 'html.parser')
            
            for selector in PHONE_SELECTORS:
                phone_element = soup.select_one(selector)
                if phone_element and phone_element.text.strip():
                    phone_number = phone_element.text.strip()
                    logging.debug(f"電話番号を取得: {phone_number}")
                    return phone_number

            logging.warning(f"電話番号が見つかりませんでした: {tel_url}")
            return "電話番号情報なし"

        except Exception as e:
            logging.error(f"電話番号スクレイピングエラー: {tel_url} - {e}")
            return "電話番号スクレイピングエラー"

    @staticmethod
    def scrape_salon_details(salon_url: str) -> Optional[Dict]:
        """
        サロン詳細ページから情報をスクレイピング

        Args:
            salon_url (str): サロン詳細ページのURL

        Returns:
            Optional[Dict]: サロン情報を含む辞書、エラー時はNone
        """
        try:
            response = HTTPClient.get(salon_url)
            if not response:
                return None

            soup = BeautifulSoup(response.content, 'html.parser')
            logging.debug(f"サロンページのHTMLを取得: {len(response.content)} bytes")

            # 店名の取得
            name_element = soup.select_one(SALON_SELECTORS['name'])
            name = name_element.text.strip() if name_element else "店名情報なし"

            # データ初期化
            phone_number = "電話番号情報なし"
            address = "住所情報なし"
            staff_count = "スタッフ数情報なし"

            # サロンデータの取得
            all_rows = soup.find_all('tr')
            for row in all_rows:
                label_element = row.find('th', class_='w120')
                if not label_element:
                    continue

                label_text = label_element.text.strip()

                # 電話番号の処理
                if "電話番号" in label_text:
                    tel_element = row.find('td', {'colspan': '3'})
                    if tel_element:
                        tel_link = tel_element.find('a')
                        if tel_link and 'href' in tel_link.attrs:
                            tel_url = tel_link['href']
                            phone_number = BeautyScraper.scrape_phone_number(tel_url)

                # 住所の処理
                elif "住所" in label_text:
                    addr_element = row.find('td', {'colspan': '3'})
                    if addr_element:
                        address = addr_element.text.strip()

                # スタッフ数の処理
                elif "スタッフ数" in label_text:
                    staff_element = row.find('td', class_='w208 vaT')
                    if staff_element:
                        staff_count = staff_element.text.strip()

            # 関連リンクの取得
            links = []
            links_element = soup.select(SALON_SELECTORS['links'])
            if links_element:
                links = [link.get('href') for link in links_element]
            related_links = "\n".join(links)
            related_links_count = len(links)

            return {
                "サロン名": name,
                "電話番号": phone_number,
                "住所": address,
                "スタッフ数": staff_count,
                "関連リンク": related_links,
                "関連リンク数": related_links_count,
                "サロンURL": salon_url
            }

        except Exception as e:
            logging.error(f"サロン詳細スクレイピングエラー: {salon_url} - {e}")
            return None

    @staticmethod
    def scrape_salon_urls(area_url: str, should_stop: Callable[[], bool] = None) -> List[str]:
        """
        エリアページからサロンURLをスクレイピング

        Args:
            area_url (str): エリアページのURL
            should_stop (callable, optional): 処理を中断するかどうかを返すコールバック関数

        Returns:
            List[str]: サロンURLのリスト
        """
        salon_urls = []
        try:
            # 中断チェック
            if should_stop and should_stop():
                logging.info("URL収集を開始前に中断されました")
                return salon_urls

            # 最初のページを取得
            response = HTTPClient.get(area_url)
            if not response or not response.text:
                return salon_urls

            soup = BeautifulSoup(response.text, "html.parser")
            
            # 総ページ数を取得
            pagination = soup.select_one('#mainContents div.preListHead div p.pa.bottom0.right0')
            if not pagination:
                last_page_num = 1
            else:
                pagination_text = pagination.text.strip()
                match = re.search(r'/(\d+)ページ', pagination_text)
                last_page_num = int(match.group(1)) if match else 1
            
            logging.info(f"ページ数: {last_page_num}")

            for page_num in range(1, last_page_num + 1):
                # 中断チェック
                if should_stop and should_stop():
                    logging.info(f"URL収集がページ {page_num} で中断されました")
                    break

                page_url = area_url
                if page_num > 1:
                    page_url = f"{area_url}PN{page_num}.html?searchGender=ALL"
                
                logging.info(f"ページ {page_num}/{last_page_num} を処理中: {page_url}")
                
                # ページコンテンツを取得
                response = HTTPClient.get(page_url)
                if not response or not response.text:
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                
                # サロンURLを抽出
                salon_items = soup.select('ul.slnCassetteList.mT20 > li')
                for item in salon_items:
                    # 中断チェック
                    if should_stop and should_stop():
                        logging.info(f"URL収集がサロン取得中に中断されました (ページ {page_num})")
                        return salon_urls

                    link = item.select_one('div.slnCassetteHeader h3.slnName a')
                    if link and link.has_attr('href'):
                        url = normalize_url(link['href'])
                        if url and url not in salon_urls:
                            salon_urls.append(url)
                            logging.info(f"サロンURL追加: {url} (合計: {len(salon_urls)}件)")

                # ページ間の待機時間
                if page_num < last_page_num:
                    time.sleep(1)

        except Exception as e:
            logging.error(f"URL収集中にエラーが発生: {str(e)}")
            logging.exception(e)  # スタックトレースを出力
        
        return salon_urls