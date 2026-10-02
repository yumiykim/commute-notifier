"""웹훅 URL을 오류나 로그에 노출하지 않는 발송 어댑터."""
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

def send_message(webhook_url: str, content: str) -> None:
    parsed = urlparse(webhook_url)
    if parsed.scheme != "https" or parsed.hostname != "discord.com" or not parsed.path.startswith("/api/webhooks/"):
        raise ValueError("유효한 discord.com 웹훅 URL이 필요합니다.")
    if not content or len(content) > 2000:
        raise ValueError("메시지는 1~2000자여야 합니다.")
    request = Request(webhook_url, data=json.dumps({"content": content, "allowed_mentions": {"parse": []}}).encode(), headers={"Content-Type": "application/json", "User-Agent": "commute-notifier/0.1"}, method="POST")
    try:
        with urlopen(request, timeout=15) as response:
            if response.status not in (200, 204):
                raise RuntimeError("디스코드 발송을 확인할 수 없습니다.")
    except HTTPError as error:
        raise RuntimeError(f"디스코드 발송 실패 (HTTP {error.code})") from None
    except (URLError, TimeoutError):
        raise RuntimeError("디스코드 연결 실패. 발송 여부를 확인하세요.") from None
