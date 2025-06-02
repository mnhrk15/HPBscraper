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

class MemoryMonitor:
    """メモリ使用量を監視するクラス"""
    
    def __init__(self, threshold_percent: float = 80.0):
        """
        メモリモニターを初期化します。
        
        Args:
            threshold_percent: 警告を出す使用率のしきい値（％）
        """
        self.threshold_percent = threshold_percent
        self.last_check_time = 0
        self.check_interval = 5  # 秒単位でのチェック間隔
    
    def check_memory_usage(self, force: bool = False) -> Dict[str, Any]:
        """
        現在のメモリ使用状況をチェックします。
        頻繁なチェックを避けるため、一定間隔でのみチェックします。
        
        Args:
            force: 間隔に関わらず強制的にチェックする場合はTrue
            
        Returns:
            Dict: メモリ使用情報を含む辞書
        """
        current_time = time.time()
        if not force and (current_time - self.last_check_time) < self.check_interval:
            return {}
            
        self.last_check_time = current_time
        
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
                # 明示的にガベージコレクションを実行
                collected = gc.collect()
                logging.info(f"ガベージコレクション実行: {collected}オブジェクト回収")
                
            return memory_info
            
        except Exception as e:
            logging.error(f"メモリ使用状況のチェック中にエラーが発生: {e}")
            return {"error": str(e), "is_critical": False}
    
    def optimize_if_needed(self) -> bool:
        """
        必要に応じてメモリ最適化を行います。
        
        Returns:
            bool: 最適化を実行した場合はTrue
        """
        memory_info = self.check_memory_usage()
        if memory_info.get("is_critical", False):
            # メモリ最適化処理
            gc.collect()
            return True
        return False


class LRUCache(Generic[T]):
    """
    LRU (Least Recently Used) キャッシュ実装
    最大サイズを超えた場合に、最も長く使われていないアイテムを削除します。
    """
    
    def __init__(self, max_size: int = MAX_CACHE_SIZE):
        """
        キャッシュを初期化します。
        
        Args:
            max_size: キャッシュの最大サイズ
        """
        self.cache = OrderedDict()
        self.max_size = max_size
    
    def get(self, key: str) -> Optional[T]:
        """
        キャッシュからアイテムを取得します。
        取得したアイテムは最も最近使用されたアイテムとして順序が更新されます。
        
        Args:
            key: キャッシュキー
            
        Returns:
            キャッシュされた値またはNone
        """
        if key not in self.cache:
            return None
            
        # キーが存在する場合、最近使用したアイテムとして順序を更新
        value = self.cache.pop(key)
        self.cache[key] = value
        return value
    
    def put(self, key: str, value: T) -> None:
        """
        アイテムをキャッシュに追加します。
        
        Args:
            key: キャッシュキー
            value: キャッシュする値
        """
        # 既存のキーの場合は削除して再追加
        if key in self.cache:
            self.cache.pop(key)
        
        # サイズ制限を超える場合は、最も古いアイテムを削除
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
            
        self.cache[key] = value
    
    def clear(self) -> None:
        """キャッシュをクリアします。"""
        self.cache.clear()
    
    def __len__(self) -> int:
        """キャッシュ内のアイテム数を返します。"""
        return len(self.cache)


def chunk_processor(chunk_size: int = 100):
    """
    大量のデータを処理する関数をチャンク単位で処理するデコレータ。
    
    Args:
        chunk_size: 一度に処理するアイテム数
        
    Returns:
        デコレータ関数
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(items, *args, **kwargs):
            if not items or len(items) <= chunk_size or not MEMORY_EFFICIENT_MODE:
                # 少量のデータやメモリ効率モードが無効の場合は通常処理
                return func(items, *args, **kwargs)
            
            # 大量データの場合はチャンク処理
            results = []
            item_count = len(items)
            chunks = [items[i:i + chunk_size] for i in range(0, item_count, chunk_size)]
            
            monitor = MemoryMonitor()
            logging.info(f"チャンク処理を開始: 合計{item_count}アイテムを{len(chunks)}チャンクに分割")
            
            for i, chunk in enumerate(chunks):
                # メモリ使用状況をチェック
                monitor.optimize_if_needed()
                
                # チャンクを処理
                chunk_result = func(chunk, *args, **kwargs)
                results.extend(chunk_result if isinstance(chunk_result, list) else [chunk_result])
                
                # 進捗ログ
                if (i + 1) % 5 == 0 or (i + 1) == len(chunks):
                    logging.info(f"チャンク処理進捗: {i + 1}/{len(chunks)} ({((i + 1) / len(chunks) * 100):.1f}%)")
                
                # 大きなチャンク処理後に明示的にガベージコレクション
                if (i + 1) % 10 == 0:
                    gc.collect()
            
            return results
        
        return wrapper
    
    return decorator


# アプリケーション全体で使用するメモリモニターインスタンス
memory_monitor = MemoryMonitor()

# グローバルLRUキャッシュインスタンス
url_cache = LRUCache[str](max_size=MAX_CACHE_SIZE)
data_cache = LRUCache[Dict](max_size=MAX_CACHE_SIZE // 2)  # データはサイズが大きいため、少なめに設定


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
