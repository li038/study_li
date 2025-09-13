"""
缓存管理器 - 智能缓存系统
"""
import os
import json
import hashlib
import pickle
import logging
from typing import Any, Optional, Dict
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CacheManager:
    """智能缓存管理器"""
    
    def __init__(self, cache_dir: str = "cache", default_ttl: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.default_ttl = default_ttl  # 默认缓存时间（秒）
        
        # 确保子目录存在
        (self.cache_dir / "text").mkdir(exist_ok=True)
        (self.cache_dir / "vector").mkdir(exist_ok=True)
        (self.cache_dir / "metadata").mkdir(exist_ok=True)
    
    def _generate_key(self, data: str) -> str:
        """生成缓存键（使用哈希避免中文和特殊字符问题）"""
        # 使用SHA256生成更安全的哈希值
        return hashlib.sha256(data.encode('utf-8')).hexdigest()[:32]
    
    def _get_cache_path(self, key: str, cache_type: str = "text") -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / cache_type / f"{key}.cache"
    
    def _is_expired(self, cache_path: Path, ttl: int) -> bool:
        """检查缓存是否过期"""
        if not cache_path.exists():
            return True
        
        file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - file_time > timedelta(seconds=ttl)
    
    def set(self, key: str, value: Any, cache_type: str = "text", ttl: Optional[int] = None) -> bool:
        """设置缓存"""
        try:
            ttl = ttl or self.default_ttl
            cache_path = self._get_cache_path(key, cache_type)
            
            cache_data = {
                'value': value,
                'timestamp': datetime.now().isoformat(),
                'ttl': ttl
            }
            
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
            
            return True
        except Exception as e:
            logger.error(f"设置缓存失败: {e}")
            return False
    
    def get(self, key: str, cache_type: str = "text") -> Optional[Any]:
        """获取缓存"""
        try:
            cache_path = self._get_cache_path(key, cache_type)
            
            if not cache_path.exists():
                return None
            
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            # 检查是否过期
            if self._is_expired(cache_path, cache_data['ttl']):
                cache_path.unlink()
                return None
            
            return cache_data['value']
        except Exception as e:
            logger.error(f"获取缓存失败: {e}")
            return None
    
    def delete(self, key: str, cache_type: str = "text") -> bool:
        """删除缓存"""
        try:
            cache_path = self._get_cache_path(key, cache_type)
            if cache_path.exists():
                cache_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"删除缓存失败: {e}")
            return False
    
    def clear_expired(self, cache_type: str = "text") -> int:
        """清除过期缓存"""
        try:
            cache_dir = self.cache_dir / cache_type
            cleared_count = 0
            
            for cache_file in cache_dir.glob("*.cache"):
                try:
                    with open(cache_file, 'rb') as f:
                        cache_data = pickle.load(f)
                    
                    if self._is_expired(cache_file, cache_data['ttl']):
                        cache_file.unlink()
                        cleared_count += 1
                except Exception:
                    # 如果文件损坏，直接删除
                    cache_file.unlink()
                    cleared_count += 1
            
            return cleared_count
        except Exception as e:
            logger.error(f"清除过期缓存失败: {e}")
            return 0
    
    def clear_all(self, cache_type: str = "text") -> int:
        """清除所有缓存"""
        try:
            cache_dir = self.cache_dir / cache_type
            cleared_count = 0
            
            for cache_file in cache_dir.glob("*.cache"):
                cache_file.unlink()
                cleared_count += 1
            
            return cleared_count
        except Exception as e:
            logger.error(f"清除所有缓存失败: {e}")
            return 0
    
    def get_cache_info(self, cache_type: str = "text") -> Dict:
        """获取缓存统计信息"""
        try:
            cache_dir = self.cache_dir / cache_type
            
            total_files = 0
            total_size = 0
            expired_files = 0
            
            for cache_file in cache_dir.glob("*.cache"):
                total_files += 1
                total_size += cache_file.stat().st_size
                
                try:
                    with open(cache_file, 'rb') as f:
                        cache_data = pickle.load(f)
                    
                    if self._is_expired(cache_file, cache_data['ttl']):
                        expired_files += 1
                except Exception:
                    expired_files += 1
            
            return {
                'total_files': total_files,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'expired_files': expired_files,
                'cache_type': cache_type
            }
        except Exception as e:
            logger.error(f"获取缓存信息失败: {e}")
            return {}
    
    def cache_query(self, query: str, func, *args, **kwargs) -> Any:
        """智能查询缓存包装器"""
        cache_key = self._generate_key(f"{query}_{func.__name__}_{args}_{kwargs}")
        
        # 尝试从缓存获取
        cached_result = self.get(cache_key, "text")
        if cached_result is not None:
            logger.info(f"缓存命中: {query}")
            return cached_result
        
        # 执行函数
        result = func(*args, **kwargs)
        
        # 缓存结果
        ttl = kwargs.pop('cache_ttl', self.default_ttl)
        self.set(cache_key, result, "text", ttl)
        
        return result