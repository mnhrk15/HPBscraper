"""
memory_optimizer.py - メモリ使用量を最適化するユーティリティモジュール

大量データ処理時のメモリ使用量を抑制し、効率的なメモリ管理を行う機能を提供します。
"""
import gc
import logging
import psutil
from typing import Dict, List, Any, Optional, TypeVar, Generic, Callable
from collections import OrderedDict
from functools import wraps
import time

from config import MEMORY_EFFICIENT_MODE, MAX_CACHE_SIZE, GC_THRESHOLD, get_memory_limit

T = TypeVar('T')

def _log_gc_details(log_prefix: str):
    """GC実行前後の詳細情報をログに出力するヘルパー関数"""
    stats_before = gc.get_stats()
    counts_before = gc.get_count()
    logging.info(f"{log_prefix} - Before GC - Counts (gen0,1,2): {counts_before}")
    for i, s in enumerate(stats_before):
        logging.info(f"{log_prefix} - Before GC - Gen {i} Stats: collections={s['collections']}, collected={s['collected']}, uncollectable={s['uncollectable']}")

    collected_count = gc.collect() # GCを実行

    stats_after = gc.get_stats()
    counts_after = gc.get_count()
    logging.info(f"{log_prefix} - After GC - Objects Collected: {collected_count}")
    logging.info(f"{log_prefix} - After GC - Counts (gen0,1,2): {counts_after}")
    for i, s in enumerate(stats_after):
        logging.info(f"{log_prefix} - After GC - Gen {i} Stats: collections={s['collections']}, collected={s['collected']}, uncollectable={s['uncollectable']}")
    return collected_count

class MemoryMonitor:
    """メモリ使用量を監視するクラス"""
    
    def __init__(self, threshold_percent: float = 80.0, cache_log_interval_sec: int = 60):
        """
        メモリモニターを初期化します。
        
        Args:
            threshold_percent: 警告を出す使用率のしきい値（％）
            cache_log_interval_sec: キャッシュ統計情報をログ出力する間隔（秒）
        """
        self.threshold_percent = threshold_percent
        self.last_check_time = 0
        self.check_interval = 5  # 秒単位でのメモリチェック間隔
        self.last_cache_log_time = 0
        self.cache_log_interval = cache_log_interval_sec
    
    def check_memory_usage(self, force: bool = False) -> Dict[str, Any]:
        """
        現在のメモリ使用状況をチェックし、必要に応じてキャッシュ統計もログ出力します。
        """
        current_time = time.time()
        perform_check = force or (current_time - self.last_check_time) >= self.check_interval

        if not perform_check:
            return {}
            
        self.last_check_time = current_time
        memory_info = {}

        try:
            memory = psutil.virtual_memory()
            memory_info = {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent,
                "is_critical": memory.percent > self.threshold_percent
            }
            
            if memory_info["is_critical"]:
                logging.warning(f"メモリ使用率が高くなっています: {memory.percent:.1f}%")
                _log_gc_details(f"MemoryMonitor Critical GC (Usage: {memory.percent:.1f}%)")

        except Exception as e:
            logging.error(f"メモリ使用状況のチェック中にエラーが発生: {e}", exc_info=True)
            memory_info = {"error": str(e), "is_critical": False}
        
        # キャッシュ統計のログ出力
        if (current_time - self.last_cache_log_time) >= self.cache_log_interval:
            if 'url_cache' in globals() and isinstance(url_cache, LRUCache):
                url_cache.log_stats()
            if 'data_cache' in globals() and isinstance(data_cache, LRUCache):
                data_cache.log_stats()
            self.last_cache_log_time = current_time
            
        return memory_info
    
    def optimize_if_needed(self) -> bool:
        """
        必要に応じてメモリ最適化を行います。
        
        Returns:
            bool: 最適化を実行した場合はTrue
        """
        memory_info = self.check_memory_usage(force=True) # 強制チェックでGCやキャッシュログも考慮
        # is_critical時のGCはcheck_memory_usage内で行われる
        return memory_info.get("is_critical", False)


class LRUCache(Generic[T]):
    """
    LRU (Least Recently Used) キャッシュ実装
    最大サイズを超えた場合に、最も長く使われていないアイテムを削除します。
    """
    
    def __init__(self, name: str, max_size: int = MAX_CACHE_SIZE):
        """
        キャッシュを初期化します。
        
        Args:
            name: キャッシュの名称（ログ出力用）
            max_size: キャッシュの最大サイズ
        """
        self.name = name
        self.cache = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[T]:
        """
        キャッシュからアイテムを取得します。
        取得したアイテムは最も最近使用されたアイテムとして順序が更新されます。
        """
        if key not in self.cache:
            self.misses += 1
            logging.debug(f"LRUCache MISS: key='{key}' CacheName='{self.name}'")
            return None
            
        self.hits += 1
        logging.debug(f"LRUCache HIT: key='{key}' CacheName='{self.name}'")
        value = self.cache.pop(key)
        self.cache[key] = value
        return value
    
    def put(self, key: str, value: T) -> None:
        """
        アイテムをキャッシュに追加します。
        """
        if key in self.cache:
            self.cache.pop(key)
        
        if len(self.cache) >= self.max_size and self.max_size > 0:
            self.cache.popitem(last=False)
            
        if self.max_size > 0: # max_sizeが0の場合はキャッシュ無効として何も追加しない
             self.cache[key] = value
    
    def clear(self) -> None:
        """キャッシュをクリアし、統計情報もリセットします。"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logging.info(f"LRUCache CLEARED: CacheName='{self.name}'")
    
    def __len__(self) -> int:
        """キャッシュ内のアイテム数を返します。"""
        return len(self.cache)

    def log_stats(self) -> None:
        """キャッシュの現在の統計情報をログに出力します。"""
        total_accesses = self.hits + self.misses
        hit_rate = (self.hits / total_accesses * 100) if total_accesses > 0 else 0
        logging.info(f"LRUCache Stats for '{self.name}': Size={len(self.cache)}/{self.max_size}, Hits={self.hits}, Misses={self.misses}, HitRate={hit_rate:.2f}%")


def chunk_processor(chunk_size: int = 100):
    """
    大量のデータを処理する関数をチャンク単位で処理するデコレータ。
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(items, *args, **kwargs):
            if not items or len(items) <= chunk_size or not MEMORY_EFFICIENT_MODE:
                return func(items, *args, **kwargs)
            
            results = []
            item_count = len(items)
            chunks = [items[i:i + chunk_size] for i in range(0, item_count, chunk_size)]
            
            # このデコレータ内でmonitorインスタンスを生成するのではなく、グローバルインスタンスを使用
            # monitor = MemoryMonitor() 
            global memory_monitor # グローバルインスタンスを使用することを明示

            logging.info(f"チャンク処理を開始: 合計{item_count}アイテムを{len(chunks)}チャンクに分割")
            
            for i, chunk in enumerate(chunks):
                memory_monitor.optimize_if_needed() # グローバルインスタンスのメソッドを呼び出し
                
                chunk_result = func(chunk, *args, **kwargs)
                results.extend(chunk_result if isinstance(chunk_result, list) else [chunk_result])
                
                if (i + 1) % 5 == 0 or (i + 1) == len(chunks):
                    logging.info(f"チャンク処理進捗: {i + 1}/{len(chunks)} ({((i + 1) / len(chunks) * 100):.1f}%)")
                
                if (i + 1) % 10 == 0: # 10チャンクごとにGC
                    _log_gc_details(f"ChunkProcessor Periodic GC (Chunk {i+1}/{len(chunks)}) (Items: {len(chunk)} in chunk)")
            
            return results
        
        return wrapper
    
    return decorator


# アプリケーション全体で使用するメモリモニターインスタンス
memory_monitor = MemoryMonitor(cache_log_interval_sec=60) # キャッシュログ間隔を指定

# グローバルLRUキャッシュインスタンス
url_cache = LRUCache[str](name="URL Cache", max_size=MAX_CACHE_SIZE)
data_cache = LRUCache[Dict](name="Data Cache", max_size=MAX_CACHE_SIZE // 2)


def optimize_memory(force: bool = False) -> None:
    """
    アプリケーション全体のメモリ使用量を最適化します。
    
    Args:
        force: 強制的に最適化を実行する場合はTrue
    """
    if force or memory_monitor.optimize_if_needed():
        # キャッシュサイズを制限
        if len(url_cache) > MAX_CACHE_SIZE // 2:
            logging.info(f"URLキャッシュを縮小: {len(url_cache)} → {MAX_CACHE_SIZE // 2}")
            new_cache = LRUCache[str](max_size=MAX_CACHE_SIZE // 2)
            # 最新のアイテムだけを保持
            for key, value in list(url_cache.cache.items())[-MAX_CACHE_SIZE // 2:]:
                new_cache.put(key, value)
            url_cache.cache = new_cache.cache
            
        # データキャッシュもサイズを制限
        if len(data_cache) > MAX_CACHE_SIZE // 4:
            logging.info(f"データキャッシュを縮小: {len(data_cache)} → {MAX_CACHE_SIZE // 4}")
            new_cache = LRUCache[Dict](max_size=MAX_CACHE_SIZE // 4)
            for key, value in list(data_cache.cache.items())[-MAX_CACHE_SIZE // 4:]:
                new_cache.put(key, value)
            data_cache.cache = new_cache.cache
