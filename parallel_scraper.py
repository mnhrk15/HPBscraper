"""
並列スクレイピングモジュール
複数のURLを並列に処理する機能を提供
メモリ使用量の最適化と高速化機能を含む
"""
import logging
import time
import gc
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Callable, Tuple, Any
from queue import Queue
from threading import Lock, Event
from datetime import datetime
from tqdm import tqdm
from itertools import islice

# 設定と依存モジュールのインポート
from config import MAX_WORKERS, CHUNK_SIZE, RATE_LIMIT, MEMORY_EFFICIENT_MODE, GC_THRESHOLD
from scraper import BeautyScraper
from memory_optimizer import memory_monitor, chunk_processor, optimize_memory, url_cache

class ParallelScraper:
    """
    複数のサロンURLを並列に処理するクラス。
    メモリ使用量の最適化と高速化機能を備えています。
    """
    def __init__(self):
        # レート制限とプログレス管理
        self.rate_limiter = RateLimiter(RATE_LIMIT)
        self._progress_lock = Lock()
        self._stop_event = Event()
        
        # 進捗状況管理
        self._total_urls = 0
        self._processed_urls = 0
        self._success_count = 0
        self._error_count = 0
        self._start_time = None
        
        # 並列処理設定
        self._executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self._progress_callback = None
        self._is_processing = False
        
        # パフォーマンス設定
        self._memory_efficient = MEMORY_EFFICIENT_MODE
        self._chunk_size = CHUNK_SIZE
        self._last_gc_count = 0  # ガベージコレクションの計数用
        
        logging.info(f"並列スクレイパー初期化: ワーカー数={MAX_WORKERS}, メモリ効率モード={MEMORY_EFFICIENT_MODE}")

    def __del__(self):
        """デストラクタ: リソースのクリーンアップを行う"""
        try:
            if self._executor:
                self._executor.shutdown(wait=False)  # 実行中のタスクを待たずにシャットダウン
            # 明示的にメモリオプティマイズを呼び出す
            optimize_memory(force=True)
        except Exception as e:
            logging.error(f"リソースの解放中にエラーが発生: {e}")

    def stop(self):
        """スクレイピング処理を中断"""
        self._stop_event.set()
        self._is_processing = False
        logging.info("スクレイピング処理を中断しました")
        # 処理中断時にメモリ最適化を実行
        optimize_memory()

    def reset(self):
        """状態をリセット"""
        self._stop_event.clear()
        self._total_urls = 0
        self._processed_urls = 0
        self._success_count = 0
        self._error_count = 0
        self._start_time = None
        self._is_processing = False
        self._last_gc_count = 0
        
        # メモリ最適化を実行
        optimize_memory(force=True)
        logging.info("スクレイピング状態をリセットしました")

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
            
            # 開始時間が設定されていない場合は現在時刻を使用
            current_time = time.time()
            elapsed = current_time - (self._start_time or current_time)
            
            # 進捗率計算（0-100%の範囲内に制限）
            progress = min(100, (self._processed_urls / max(1, self._total_urls)) * 100)
            
            # 1件あたりの平均処理時間計算
            avg_time = elapsed / max(1, self._processed_urls)
            
            # 進捗情報追加 - 速度と残りの件数
            speed = 0
            if elapsed > 0:
                speed = self._processed_urls / elapsed  # 1秒あたりの処理件数
            
            remaining_items = max(0, self._total_urls - self._processed_urls)
            
            return {
                "total": self._total_urls,
                "processed": self._processed_urls,
                "success": self._success_count,
                "error": self._error_count,
                "progress": progress,
                "avg_time": avg_time,
                "eta": self._calculate_eta(),
                "elapsed": elapsed,
                "speed": speed,
                "remaining": remaining_items,
                "memory_optimizations": self._last_gc_count
            }
        except Exception as e:
            logging.error(f"進捗情報の取得でエラーが発生: {str(e)}")
            return {}

    def _update_progress(self, progress_bar: tqdm, success: bool = True) -> None:
        """進捗状況を更新し、メモリ最適化も行います。"""
        try:
            with self._progress_lock:
                self._processed_urls += 1
                if success:
                    self._success_count += 1
                else:
                    self._error_count += 1
                
                # 進捗情報を取得
                progress_info = self._get_progress_info()
                
                # 進捗バーの詳細情報を設定して更新
                if progress_bar:
                    # 進捗詳細情報を表示用に設定
                    progress_bar.set_postfix({
                        '成功': self._success_count,
                        'エラー': self._error_count,
                        '平均時間': f'{progress_info.get("avg_time", 0):.1f}秒/件',
                        '残り時間': progress_info.get("eta", "不明")
                    }, refresh=True)
                    progress_bar.update(1)
                
                # コールバックが設定されていれば実行
                if self._progress_callback:
                    try:
                        self._progress_callback(progress_info)
                    except Exception as e:
                        logging.error(f"進捗コールバックでエラーが発生: {str(e)}")
                
                # 定期的にメモリ使用量をチェックと最適化
                if self._memory_efficient and self._processed_urls % GC_THRESHOLD == 0:
                    optimize_memory()
                    self._last_gc_count += 1
                    logging.debug(f"メモリ最適化実行: 進捗{self._processed_urls}/{self._total_urls}")
        
        except Exception as e:
            logging.error(f"進捗状況の更新中にエラーが発生: {e}")

    def scrape_salon_urls(self, area_url: str) -> List[str]:
        """
        エリアページからサロンURLを収集します。
        URLキャッシュを使用してパフォーマンスを向上させます。
        
        Args:
            area_url: エリアページのURL
            
        Returns:
            List[str]: サロンURLのリスト
        """
        try:
            self._is_processing = True
            
            # キャッシュからの取得を試みる
            cache_key = f"area:{area_url}"
            cached_urls = url_cache.get(cache_key)
            if cached_urls:
                logging.info(f"キャッシュからサロンURLを取得: {len(cached_urls)}件")
                return cached_urls
                
            # URL収集の実行
            urls = BeautyScraper.scrape_salon_urls(area_url, self._should_stop)
            
            # 結果の検証
            if not urls and self._should_stop():
                logging.info("URL収集が中断されました")
                return []
            
            if not urls:
                logging.warning(f"サロンURLが見つかりませんでした: {area_url}")
                return []
            
            # 取得したURLをキャッシュ
            url_cache.put(cache_key, urls)
                
            logging.info(f"サロンURL収集完了: {len(urls)}件")
            return urls
            
        except Exception as e:
            logging.error(f"URL収集中にエラーが発生: {str(e)}")
            return []
            
        finally:
            self._is_processing = False
            # メモリ使用量を確認し最適化
            if self._memory_efficient:
                optimize_memory()

    def _scrape_salon_with_retry(self, scraper: BeautyScraper, url: str) -> Optional[Dict]:
        """単一のサロン情報をスクレイピング（レート制限付き）"""
        # キャッシュから情報を取得を試みる
        cache_key = f"salon:{url}"
        cached_data = url_cache.get(cache_key)
        if cached_data:
            logging.debug(f"キャッシュからサロン情報を取得: {url}")
            return cached_data
            
        retries = 3
        for attempt in range(retries):
            try:
                if self._should_stop():
                    return None
                self.rate_limiter.wait()
                result = scraper.scrape_salon_details(url)
                
                # 成功した場合はキャッシュに保存
                if result:
                    url_cache.put(cache_key, result)
                    
                return result
                
            except Exception as e:
                if attempt == retries - 1:
                    logging.error(f"サロン情報の取得に失敗 (最終試行): {url} - {e}")
                    return None
                logging.warning(f"サロン情報の取得リトライ ({attempt + 1}/{retries}): {url} - {e}")
                time.sleep(2 ** attempt)  # 指数バックオフ

    def scrape_salon_details_parallel(self, salon_urls: List[str]) -> List[Dict]:
        """
        サロン情報を並列で取得します。
        大量のデータを処理する場合はチャンク処理で最適化します。

        Args:
            salon_urls: サロンURLのリスト

        Returns:
            List[Dict]: 取得したサロン情報のリスト
        """
        if not salon_urls:
            return []

        self._is_processing = True
        self._total_urls = len(salon_urls)
        self._processed_urls = 0
        self._success_count = 0
        self._error_count = 0
        self._start_time = time.time()
        
        results = []
        scraper = BeautyScraper()

        try:
            # メモリ使用量の最適化のためにキャッシュの事前確認
            if self._memory_efficient and len(salon_urls) > 100:
                logging.info(f"大量データ処理モードを有効化: {len(salon_urls)}件")
                optimize_memory(force=True)
            
            with tqdm(total=len(salon_urls), desc="サロン情報取得") as progress_bar:
                # バッチサイズを動的に調整
                batch_size = min(CHUNK_SIZE * 2, max(CHUNK_SIZE, len(salon_urls) // MAX_WORKERS))
                salon_batches = [salon_urls[i:i + batch_size] for i in range(0, len(salon_urls), batch_size)]
                
                for batch in salon_batches:
                    if self._should_stop():
                        break
                    
                    # 各バッチを並列処理
                    futures = {
                        self._executor.submit(
                            self._scrape_salon_with_retry, scraper, url
                        ): url for url in batch
                    }

                    for future in as_completed(futures):
                        if self._should_stop():
                            break

                        try:
                            result = future.result()
                            if result:
                                results.append(result)
                                self._update_progress(progress_bar, success=True)
                            else:
                                self._update_progress(progress_bar, success=False)
                        except Exception as e:
                            logging.error(f"処理エラー {futures[future]}: {str(e)}")
                            self._update_progress(progress_bar, success=False)
                    
                    # バッチ処理後にメモリ最適化
                    if self._memory_efficient and len(batch) > 50:
                        optimize_memory()

        finally:
            self._is_processing = False
            self._stop_event.clear()
            logging.info(f"スクレイピング完了: 合計{len(results)}/{self._total_urls}件 (成功: {self._success_count}, エラー: {self._error_count})")

        return results

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
