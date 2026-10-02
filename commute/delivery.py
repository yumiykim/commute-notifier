"""동일 날짜·발송 슬롯 재실행 방지. 불확실한 발송은 자동 재시도하지 않는다."""
import json
from pathlib import Path

class DeliveryLedger:
    def __init__(self, path):
        self.path = Path(path)
        self.entries = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.entries, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path)

    def reserve(self, key):
        if key in self.entries:
            return False
        self.entries[key] = "pending"
        self.save()
        return True

    def mark_sent(self, key):
        self.entries[key] = "sent"
        self.save()
