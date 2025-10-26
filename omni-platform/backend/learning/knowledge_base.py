import os
import json
import time
from typing import Dict, Any, List, Optional

class KnowledgeBase:
    def __init__(self, storage_path: Optional[str] = None):
        base = storage_path or os.getenv("KNOWLEDGE_BASE_PATH", "./data/knowledge_base.json")
        self.storage_path = base
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({"pages": {}}, f)

    def _load(self) -> Dict[str, Any]:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"pages": {}}

    def _save(self, data: Dict[str, Any]) -> None:
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def put_page(self, title: str, content: str, tags: Optional[List[str]] = None, critical: bool = False, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        data = self._load()
        pages = data.get("pages", {})
        pages[title] = {
            "title": title,
            "content": content,
            "tags": tags or [],
            "critical": bool(critical),
            "tenant_id": tenant_id,
            "updated_at": int(time.time()*1000),
        }
        data["pages"] = pages
        self._save(data)
        return pages[title]

    def get_page(self, title: str) -> Optional[Dict[str, Any]]:
        data = self._load()
        return data.get("pages", {}).get(title)

    def list_pages(self) -> List[Dict[str, Any]]:
        data = self._load()
        return list(data.get("pages", {}).values())

    def search(self, query: str) -> List[Dict[str, Any]]:
        q = (query or "").lower()
        results: List[Dict[str, Any]] = []
        for p in self.list_pages():
            text = (p.get("title", "") + "\n" + p.get("content", "")).lower()
            if q in text or any(q in (t.lower()) for t in p.get("tags", [])):
                results.append(p)
        return results

    def set_critical(self, title: str, critical: bool = True, tags: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        data = self._load()
        page = data.get("pages", {}).get(title)
        if not page:
            return None
        page["critical"] = bool(critical)
        if tags is not None:
            page["tags"] = tags
        page["updated_at"] = int(time.time()*1000)
        self._save(data)
        return page

    def list_critical(self) -> List[Dict[str, Any]]:
        return [p for p in self.list_pages() if p.get("critical")]