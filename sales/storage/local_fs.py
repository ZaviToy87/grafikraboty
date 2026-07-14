# -*- coding: utf-8 -*-
"""
sales/storage/local_fs.py — Локальное файловое хранилище для данных продаж
"""
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
from ..models.sale import Sale


class LocalStorage:
    """Локальное файловое хранилище для данных о продажах"""
    
    def __init__(self, base_dir: str = None):
        """
        Инициализировать хранилище.
        
        Args:
            base_dir: Базовая директория для хранения данных
        """
        if base_dir is None:
            base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "sales_data")
        
        self.base_dir = Path(base_dir)
        self.files_dir = self.base_dir / "files"
        self.metadata_dir = self.base_dir / "metadata"
        self.cache_dir = self.base_dir / "cache"
        
        # Создаём директории
        self.files_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_hash(self, filepath: str) -> str:
        """Получить MD5 хэш файла"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def save_file(self, filepath: str, user_id: int, 
                  original_name: str = None) -> Dict[str, Any]:
        """
        Сохранить файл в хранилище.
        
        Args:
            filepath: Путь к исходному файлу
            user_id: ID пользователя, загрузившего файл
            original_name: Оригинальное имя файла
        
        Returns:
            Метаданные сохранённого файла
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Файл не найден: {filepath}")
        
        file_hash = self._get_file_hash(filepath)
        ext = Path(filepath).suffix.lower()
        
        # Новое имя файла: hash + расширение
        new_filename = f"{file_hash}{ext}"
        new_filepath = self.files_dir / new_filename
        
        # Копируем файл если ещё не существует
        if not new_filepath.exists():
            import shutil
            shutil.copy2(filepath, new_filepath)
        
        # Метаданные
        metadata = {
            "id": file_hash,
            "original_name": original_name or Path(filepath).name,
            "stored_name": new_filename,
            "filepath": str(new_filepath),
            "user_id": user_id,
            "file_size": os.path.getsize(filepath),
            "file_hash": file_hash,
            "extension": ext,
            "uploaded_at": datetime.now().isoformat()
        }
        
        # Сохраняем метаданные
        self._save_metadata(file_hash, metadata)
        
        return metadata
    
    def _save_metadata(self, file_id: str, metadata: dict):
        """Сохранить метаданные файла"""
        metadata_path = self.metadata_dir / f"{file_id}.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def get_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Получить метаданные файла по ID"""
        metadata_path = self.metadata_dir / f"{file_id}.json"
        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    
    def get_file(self, file_id: str) -> Optional[str]:
        """
        Получить путь к файлу по ID.
        
        Args:
            file_id: ID файла (хэш)
        
        Returns:
            Путь к файлу или None
        """
        metadata = self.get_metadata(file_id)
        if metadata and os.path.exists(metadata["filepath"]):
            return metadata["filepath"]
        return None
    
    def list_files(self, user_id: int = None) -> List[Dict[str, Any]]:
        """
        Получить список всех файлов.
        
        Args:
            user_id: Фильтр по ID пользователя (опционально)
        
        Returns:
            Список метаданных файлов
        """
        files = []
        for metadata_path in self.metadata_dir.glob("*.json"):
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                if user_id is None or metadata.get("user_id") == user_id:
                    files.append(metadata)
        return sorted(files, key=lambda x: x.get("uploaded_at", ""), reverse=True)
    
    def delete_file(self, file_id: str) -> bool:
        """
        Удалить файл из хранилища.
        
        Args:
            file_id: ID файла (хэш)
        
        Returns:
            True если файл удалён
        """
        metadata = self.get_metadata(file_id)
        if not metadata:
            return False
        
        # Удаляем файл
        filepath = metadata.get("filepath")
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        
        # Удаляем метаданные
        metadata_path = self.metadata_dir / f"{file_id}.json"
        if metadata_path.exists():
            metadata_path.unlink()
        
        return True
    
    def save_sales_data(self, sales: List[Sale], period_id: str) -> str:
        """
        Сохранить данные о продажах.
        
        Args:
            sales: Список записей о продажах
            period_id: ID периода
        
        Returns:
            Путь к сохранённому файлу
        """
        filename = f"sales_{period_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.files_dir / filename
        
        data = {
            "period_id": period_id,
            "saved_at": datetime.now().isoformat(),
            "total_records": len(sales),
            "sales": [s.to_dict() if hasattr(s, 'to_dict') else dict(s) for s in sales]
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return str(filepath)
    
    def load_sales_data(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Загрузить данные о продажах из файла.
        
        Args:
            filepath: Путь к файлу
        
        Returns:
            Список записей о продажах
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("sales", [])
    
    def clear_cache(self):
        """Очистить кэш"""
        for cache_file in self.cache_dir.glob("*"):
            cache_file.unlink()
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику хранилища"""
        files = list(self.files_dir.glob("*"))
        metadata_files = list(self.metadata_dir.glob("*.json"))
        
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        
        return {
            "total_files": len(files),
            "total_metadata": len(metadata_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "base_dir": str(self.base_dir)
        }
