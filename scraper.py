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
import streamlit as st

class BeautyScraper:
    @staticmethod
    def scrape_phone_number(tel_url: str) -> str:
        """
        電話番号ページから電話番号をスクレイピング

        Args:
            tel_url (str): 電話番号ページのURL

        Returns:
            str: スクレイピングした電話番号、またはエラーを示す文字列
        """
        try:
            response = HTTPClient.get(tel_url)
            if not response or not response.content:
                logging.warning(f"電話番号ページの取得に失敗しました (レスポンスなしまたは空): {tel_url}")
                return "電話番号ページ取得失敗"

            soup = BeautifulSoup(response.content, 'html.parser')
            
            for selector_idx, selector in enumerate(PHONE_SELECTORS):
                phone_element = soup.select_one(selector)
                if phone_element:
                    phone_text = phone_element.text.strip()
                    if phone_text:
                        logging.debug(f"電話番号を取得: {phone_text} (URL: {tel_url}, セレクタ: {selector})")
                        return phone_text
                    else:
                        logging.debug(f"電話番号要素は存在しますがテキストが空です。URL: {tel_url}, セレクタ: {selector}")
            
            logging.warning(f"定義された全てのセレクタで電話番号が見つかりませんでした: {tel_url}, 使用セレクタ数: {len(PHONE_SELECTORS)}")
            return "電話番号情報なし"

        except Exception as e:
            logging.error(f"電話番号スクレイピング中に予期せぬ例外が発生: {tel_url} - {e}", exc_info=True)
            return "電話番号スクレイピング例外"

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
            if not response or not response.content:
                logging.warning(f"サロン詳細: HTTPレスポンスが空またはありません。URL: {salon_url}")
                return None

            soup = BeautifulSoup(response.content, 'html.parser')
            logging.debug(f"サロンページのHTMLを取得: {len(response.content)} bytes. URL: {salon_url}")

            # 店名の取得
            name = "店名情報なし"
            name_selector = SALON_SELECTORS.get('name')
            if name_selector:
                name_element = soup.select_one(name_selector)
                if name_element:
                    name_text = name_element.text.strip()
                    if name_text:
                        name = name_text
                    else:
                        logging.warning(f"サロン詳細: 店名要素が見つかりましたがテキストが空です。URL: {salon_url}, セレクタ: {name_selector}")
                else:
                    logging.warning(f"サロン詳細: 店名要素が見つかりませんでした。URL: {salon_url}, セレクタ: {name_selector}")
            else:
                logging.warning(f"サロン詳細: 店名のセレクタがconfigに定義されていません。URL: {salon_url}")

            # データ初期化
            phone_number = "電話番号情報なし"
            address = "住所情報なし"
            staff_count = "スタッフ数情報なし"

            # サロンデータの取得 (テーブル形式)
            all_rows = soup.find_all('tr')
            for row in all_rows:
                label_element = row.find('th', class_='w120')
                if not label_element:
                    continue

                label_text = label_element.text.strip()

                # 電話番号の処理
                if "電話番号" in label_text: # 正しいif条件に変更
                    tel_td_element = row.find('td', {'colspan': '3'})
                    if tel_td_element:
                        tel_link_element = tel_td_element.find('a')
                        if tel_link_element and tel_link_element.has_attr('href'):
                            tel_url = tel_link_element['href']
                            # scrape_phone_number の堅牢性は別途対応
                            scraped_phone = BeautyScraper.scrape_phone_number(tel_url)
                            if scraped_phone and scraped_phone not in ["電話番号情報なし", "電話番号取得エラー", "電話番号スクレイピングエラー"]:
                                phone_number = scraped_phone
                            elif scraped_phone:
                                phone_number = scraped_phone # エラーメッセージをそのまま使う
                        elif not tel_link_element:
                            logging.warning(f"サロン詳細(表): 「電話番号」のtd内にリンク(aタグ)が見つかりませんでした。URL: {salon_url}, 行HTML(一部): {str(row)[:150]}")
                        elif not tel_link_element.has_attr('href'):
                             logging.warning(f"サロン詳細(表): 「電話番号」のリンク(aタグ)にhref属性がありません。URL: {salon_url}, 行HTML(一部): {str(row)[:150]}")
                    else:
                        logging.warning(f"サロン詳細(表): 「電話番号」のth要素に対するtd要素が見つかりませんでした。URL: {salon_url}, 行HTML(一部): {str(row)[:150]}")
                
                # 住所の処理
                elif "住所" in label_text:
                    addr_element = row.find('td', {'colspan': '3'})
                    if addr_element:
                        extracted_address = addr_element.text.strip()
                        if extracted_address:
                            address = extracted_address
                        else:
                            logging.warning(f"サロン詳細(表): 「住所」のtd要素は存在しますが、テキストが空です。URL: {salon_url}, 行HTML(一部): {str(row)[:150]}")
                    else:
                        logging.warning(f"サロン詳細(表): 「住所」のth要素に対するtd要素が見つかりませんでした。URL: {salon_url}, 行HTML(一部): {str(row)[:150]}")
                
                # スタッフ数の処理
                elif "スタッフ数" in label_text:
                    staff_element = row.find('td', class_='w208 vaT') # セレクタは既存のものを維持
                    if staff_element:
                        extracted_staff_count = staff_element.text.strip()
                        if extracted_staff_count:
                            staff_count = extracted_staff_count
                        else:
                            logging.warning(f"サロン詳細(表): 「スタッフ数」のtd要素は存在しますが、テキストが空です。URL: {salon_url}, 行HTML(一部): {str(row)[:150]}")
                    else:
                        logging.warning(f"サロン詳細(表): 「スタッフ数」のth要素に対するtd要素が見つかりませんでした。URL: {salon_url}, 行HTML(一部): {str(row)[:150]}")

            # 関連リンクの取得
            links = []
            links_selector = SALON_SELECTORS.get('links')
            if links_selector:
                links_elements = soup.select(links_selector)
                if links_elements:
                    for link_el in links_elements:
                        href = link_el.get('href')
                        if href:
                            links.append(normalize_url(href)) # URL正規化を追加
                        else:
                            logging.warning(f"サロン詳細: 関連リンク要素にhref属性がありません。URL: {salon_url}, 要素HTML(一部): {str(link_el)[:100]}")
                # else: # links_elements が空の場合のログは、頻出する可能性があるのでDEBUGレベルかコメントアウト
                    # logging.debug(f"サロン詳細: 関連リンク要素が見つかりませんでした（セレクタは存在）。URL: {salon_url}, セレクタ: {links_selector}")
            else:
                logging.debug(f"サロン詳細: 関連リンクのセレクタがconfigに定義されていません。URL: {salon_url}")
            
            valid_links = [l for l in links if l is not None] # normalize_urlがNoneを返す可能性も考慮
            related_links_str = "\n".join(valid_links)
            related_links_count = len(valid_links)

            return {
                "サロン名": name,
                "電話番号": phone_number,
                "住所": address,
                "スタッフ数": staff_count,
                "関連リンク": related_links_str,
                "関連リンク数": related_links_count,
                "サロンURL": salon_url
            }

        except Exception as e:
            logging.error(f"サロン詳細スクレイピング中に予期せぬエラー: {salon_url} - {e}", exc_info=True) # スタックトレースも記録
            return None

    @staticmethod
    def scrape_salon_urls(area_url: str, should_stop: Callable[[], bool] = None, progress_placeholder=None) -> List[str]:
        """
        エリアページからサロンURLをスクレイピング

        Args:
            area_url (str): エリアページのURL
            should_stop (callable, optional): 処理を中断するかどうかを返すコールバック関数

        Returns:
            List[str]: サロンURLのリスト
        """
        # デフォルト値とエラー状態対応のための初期化
        salon_urls = []
        last_page_num = 1  # 最初から変数を初期化
        
        # StreamlitのUI要素のためのプレースホルダーを作成
        if progress_placeholder is None:
            # 呼び出し元で指定されなかった場合、ここで作成
            main_status_placeholder = st.empty()
            progress_bar_placeholder = st.empty()
        else:
            main_status_placeholder = progress_placeholder.get("main_status", st.empty())
            progress_bar_placeholder = progress_placeholder.get("progress_bar", st.empty())

        # メソッド全体を大きなtry-exceptで囲み、どのような状況でもエラーが伝搬しないようにする
        try:
            # ステータス表示
            with main_status_placeholder.container():
                st.info(f"エリアURLからサロン情報を収集中です: {area_url}")
            
            # 中断チェック
            if should_stop and should_stop():
                logging.info("処理が中断されました。")
                main_status_placeholder.empty() # スピナーをクリア
                return salon_urls

            # 最初のページを取得
            response = None
            try:
                response = HTTPClient.get(area_url)
            except Exception as e:
                logging.error(f"エリアURLへのアクセス中にエラー: {str(e)}")
                main_status_placeholder.warning(f"指定されたエリア ({area_url}) へのアクセス中にエラーが発生しました。")
                return salon_urls
                
            if not response:
                logging.error(f"指定されたエリアURLにアクセスできませんでした: {area_url}")
                main_status_placeholder.warning(f"指定されたエリア ({area_url}) からサロンURLが見つかりませんでした。URLが正しいか、サイトの構造が変わっていないか確認してください。")
                return salon_urls
        
            if not response.text:
                logging.error(f"指定されたエリアURLのレスポンスが空でした: {area_url}")
                main_status_placeholder.warning(f"このエリアで有効なサロンURLが見つかりませんでした。")
                return salon_urls

            # HTMLパース
            soup = None
            try:
                soup = BeautifulSoup(response.text, "html.parser")
            except Exception as e:
                logging.error(f"HTMLパース中にエラー: {str(e)}")
                main_status_placeholder.warning("ページデータの解析中にエラーが発生しました。")
                return salon_urls
            
            # 総ページ数を取得 - 必ず1で初期化済み
            try:
                pagination_element_selector = '#mainContents div.preListHead div p.pa.bottom0.right0'
                pagination = soup.select_one(pagination_element_selector)
                if not pagination:
                    logging.warning(f"ページネーション要素が見つかりませんでした。セレクタ: {pagination_element_selector}。1ページのみ処理します。")
                else:
                    pagination_text = pagination.text.strip()
                    match = re.search(r'/(\d+)ページ', pagination_text)
                    if match:
                        try:
                            last_page_num = int(match.group(1))
                        except (ValueError, TypeError):
                            logging.warning(f"ページ番号の変換エラー: '{match.group(1)}'。1ページのみ処理します。")
                            # last_page_numは既に1に初期化済み
                    else:
                        logging.warning(f"ページネーションのテキストから総ページ数を抽出できませんでした。テキスト: '{pagination_text}'。1ページのみ処理します。")
            except Exception as e_page_count:
                logging.error(f"総ページ数取得中に予期せぬエラー: {e_page_count}")
                # last_page_numは既に1に初期化済み
            
            logging.info(f"ページ数: {last_page_num}")

            try:
                for page_num in range(1, last_page_num + 1):
                    # 中断チェック
                    if should_stop and should_stop():
                        logging.info(f"処理がページ {page_num} で中断されました")
                        break

                    page_url = area_url
                    if page_num > 1:
                        page_url = f"{area_url}PN{page_num}.html?searchGender=ALL"
                    
                    logging.info(f"ページ {page_num}/{last_page_num} を処理中: {page_url}")
                    with main_status_placeholder.container():
                        st.info(f"ページ {page_num}/{last_page_num} を収集中 ({page_url})...")
                    if last_page_num > 0:
                        progress_bar_placeholder.progress(page_num / last_page_num)
                    
                    # ページコンテンツを取得
                    response = None
                    try:
                        response = HTTPClient.get(page_url)
                    except Exception as e:
                        logging.error(f"ページ取得中にエラー: {str(e)}")
                        continue
                        
                    if not response or not response.text:
                        logging.warning(f"ページ {page_num} のレスポンスが無効です")
                        continue

                    soup = None
                    try:
                        soup = BeautifulSoup(response.text, "html.parser")
                    except Exception as e:
                        logging.error(f"ページ {page_num} のHTML解析中にエラー: {str(e)}")
                        continue
                    
                    # サロンURLを抽出
                    try:
                        salon_list_selector = 'ul.slnCassetteList.mT20 > li'
                        salon_items = soup.select(salon_list_selector)
                        
                        if not salon_items and page_num < last_page_num : # 最終ページ以外でサロンが見つからない場合
                            logging.warning(f"ページ {page_num} でサロンリストが見つかりませんでした。セレクタ: {salon_list_selector}")

                        for item_idx, item in enumerate(salon_items):
                            # 中断チェック
                            if should_stop and should_stop():
                                logging.info(f"処理がサロン取得中に中断されました (ページ {page_num})")
                                return salon_urls

                            salon_link_selector = 'div.slnCassetteHeader h3.slnName a'
                            link = None
                            try:
                                link = item.select_one(salon_link_selector)
                                if link and link.has_attr('href'):
                                    url = normalize_url(link['href'])
                                    if url and url not in salon_urls:
                                        salon_urls.append(url)
                                    logging.debug(f"サロンURL追加: {url} (合計: {len(salon_urls)}件)") # INFOからDEBUGに変更
                            except Exception as e:
                                logging.error(f"サロンURL取得中にエラー: {e}")
                                continue
                    except Exception as e:
                        logging.error(f"ページ {page_num} のサロンリスト抽出中にエラー: {str(e)}")
                        continue
            except Exception as e:
                logging.error(f"ページ処理中に予期せぬエラー: {str(e)}")
            
            # URLが取得できたかチェック
            if not salon_urls:
                logging.warning("サロンURLが見つかりませんでした。")
                with main_status_placeholder.container():
                    st.warning(f"指定されたエリア ({area_url}) からサロンURLが見つかりませんでした。URLが正しいか、サイトの構造が変わっていないか確認してください。")

            return salon_urls
                
        except Exception as e:
            logging.error(f"URL収集中にエラーが発生: {str(e)}")
            logging.exception(e)  # スタックトレースを出力
            with main_status_placeholder.container():
                st.error(f"URL収集中にエラーが発生しました: {e}")
        finally:
            # 処理完了後、UI要素をクリアまたは最終状態を表示
            with main_status_placeholder.container():
                if salon_urls: # URLが1件以上収集できた場合
                    st.success(f"サロンURL収集完了。合計: {len(salon_urls)}件")
                elif area_url: # URLが収集できず、エリアURLが指定されていた場合
                    st.warning(f"指定されたエリア ({area_url}) からサロンURLが見つかりませんでした。URLが正しいか、サイトの構造が変わっていないか確認してください。")
                else: # その他の場合 (エラーなど)
                    st.info("URL収集処理が終了しました。")
            
            # 進捗バーを完了状態にするかクリア
            if last_page_num > 0 and len(salon_urls) > 0 : # 正常に収集できた場合
                 progress_bar_placeholder.progress(1.0)
            else: # エラー時や収集できなかった場合はクリア
                 progress_bar_placeholder.empty()

        return salon_urls