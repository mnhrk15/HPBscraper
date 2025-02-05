"""
並列スクレイピングモジュール
複数のURLを並列に処理する機能を提供
"""
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Callable
from queue import Queue
from threading import Lock, Event
from datetime import datetime
from tqdm import tqdm

from config import MAX_WORKERS, CHUNK_SIZE, RATE_LIMIT
from scraper import BeautyScraper

class ParallelScraper:
    def __init__(self):
        self.rate_limiter = RateLimiter(RATE_LIMIT)
        self._progress_lock = Lock()
        self._stop_event = Event()
        self._total_urls = 0
        self._processed_urls = 0
        self._success_count = 0
        self._error_count = 0
        self._start_time = None
        self._executor = None
        self._progress_callback = None
        self._is_processing = False

    def stop(self):
        """スクレイピング処理を中断"""
        self._stop_event.set()
        self._is_processing = False

    def reset(self):
        """状態をリセット"""
        self._stop_event.clear()
        self._total_urls = 0
        self._processed_urls = 0
        self._success_count = 0
        self._error_count = 0
        self._start_time = None
        self._is_processing = False

    def set_progress_callback(self, callback: Callable):
        """進捗コールバックを設定"""
        self._progress_callback = callback

    def _should_stop(self) -> bool:
        """中断すべきかどうかを判定"""
        return self._stop_event.is_set() or not self._is_processing

    def _calculate_eta(self) -> str:
        """残り時間を計算"""
        try:
            if not self._start_time or self._processed_urls == 0:
                return "計算中..."
            
            elapsed = max(0.1, time.time() - self._start_time)
            avg_time_per_url = elapsed / self._processed_urls
            remaining_urls = max(0, self._total_urls - self._processed_urls)
            eta_seconds = avg_time_per_url * remaining_urls
            
            if eta_seconds < 60:
                return f"約{int(max(0, eta_seconds))}秒"
            elif eta_seconds < 3600:
                return f"約{int(eta_seconds / 60)}分"
            else:
                hours = int(eta_seconds / 3600)
                minutes = int((eta_seconds % 3600) / 60)
                return f"約{hours}時間{minutes}分"
        except Exception as e:
            logging.error(f"ETAの計算でエラーが発生: {str(e)}")
            return "計算不能"

    def _get_progress_info(self) -> dict:
        """進捗情報を取得"""
        try:
            if not self._total_urls:
                return {}
            
            elapsed = time.time() - (self._start_time or time.time())
            progress = min(100, (self._processed_urls / max(1, self._total_urls)) * 100)
            avg_time = elapsed / max(1, self._processed_urls)
            
            return {
                "total": self._total_urls,
                "processed": self._processed_urls,
                "success": self._success_count,
                "error": self._error_count,
                "progress": progress,
                "avg_time": avg_time,
                "eta": self._calculate_eta(),
                "elapsed": elapsed
            }
        except Exception as e:
            logging.error(f"進捗情報の取得でエラーが発生: {str(e)}")
            return {}

    def _update_progress(self, progress_bar: tqdm, success: bool = True) -> None:
        """進捗状況を更新"""
        try:
            with self._progress_lock:
                self._processed_urls += 1
                if success:
                    self._success_count += 1
                else:
                    self._error_count += 1
                
                progress_info = self._get_progress_info()
                
                if progress_bar:
                    progress_bar.set_postfix({
                        '成功': self._success_count,
                        'エラー': self._error_count,
                        '平均時間': f'{progress_info.get("avg_time", 0):.1f}秒/件',
                        '残り時間': progress_info.get("eta", "不明")
                    }, refresh=True)
                    progress_bar.update(1)
                
                if self._progress_callback:
                    try:
                        self._progress_callback(progress_info)
                    except Exception as e:
                        logging.error(f"進捗コールバックでエラーが発生: {str(e)}")
        except Exception as e:
            logging.error(f"進捗更新でエラーが発生: {str(e)}")

    def scrape_salon_urls(self, area_url: str) -> List[str]:
        """エリアページからサロンURLを収集"""
        try:
            # 処理開始前の状態初期化
            self.reset()
            self._is_processing = True
            
            # URL収集の実行
            urls = BeautyScraper.scrape_salon_urls(area_url, self._should_stop)
            
            # 結果の検証
            if not urls and self._should_stop():
                logging.info("URL収集が中断されました")
                return []
            
            if not urls:
                logging.warning(f"サロンURLが見つかりませんでした: {area_url}")
                return []
                
            logging.info(f"サロンURL収集完了: {len(urls)}件")
            return urls
            
        except Exception as e:
            logging.error(f"URL収集中にエラーが発生: {str(e)}")
            return []
            
        finally:
            self._is_processing = False

    def _scrape_salon_with_retry(self, scraper: BeautyScraper, url: str) -> Optional[Dict]:
        """単一のサロン情報をスクレイピング（レート制限付き）"""
        retries = 3
        for attempt in range(retries):
            try:
                if self._should_stop():
                    return None
                self.rate_limiter.wait()
                return scraper.scrape_salon_details(url)
            except Exception as e:
                if attempt == retries - 1:
                    logging.error(f"サロン情報の取得に失敗 (最終試行): {url} - {e}")
                    return None
                logging.warning(f"サロン情報の取得リトライ ({attempt + 1}/{retries}): {url} - {e}")
                time.sleep(2 ** attempt)  # 指数バックオフ

    def scrape_salon_details_parallel(self, salon_urls: List[str]) -> List[Dict]:
        """サロン情報を並列で取得"""
        if not salon_urls:
            return []

        try:
            self.reset()
            self._is_processing = True
            self._start_time = time.time()
            self._total_urls = len(salon_urls)
            
            results = []
            scraper = BeautyScraper()

            if self._progress_callback:
                self._progress_callback(self._get_progress_info())

            with tqdm(total=len(salon_urls), desc="サロン情報取得") as progress_bar:
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as self._executor:
                    futures = [
                        self._executor.submit(self._scrape_salon_with_retry, scraper, url)
                        for url in salon_urls
                    ]
                    
                    for future in as_completed(futures):
                        if self._should_stop():
                            logging.info("処理が中断されました")
                            break

                        try:
                            data = future.result()
                            if data:
                                results.append(data)
                                self._update_progress(progress_bar, success=True)
                            else:
                                self._update_progress(progress_bar, success=False)
                        except Exception as e:
                            logging.error(f"並列処理中にエラーが発生: {str(e)}")
                            self._update_progress(progress_bar, success=False)

            return results
        finally:
            self._is_processing = False
            if self._progress_callback:
                self._progress_callback(self._get_progress_info())

class RateLimiter:
    """リクエストのレート制限を管理するクラス"""
    
    def __init__(self, rate_limit: float):
        self.rate_limit = max(0.1, rate_limit)  # 最小値を設定
        self.last_request_time = time.time()
        self._lock = Lock()

    def wait(self) -> None:
        """必要な待機時間を計算して待機"""
        with self._lock:
            now = time.time()
            elapsed = now - self.last_request_time
            wait_time = max(0, self.rate_limit - elapsed)
            if wait_time > 0:
                time.sleep(wait_time)
            self.last_request_time = time.time()
