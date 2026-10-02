"""이전 GitHub Actions artifact에서 작은 발송 기록만 복원한다."""
import io
import json
import os
from pathlib import Path
from urllib.request import Request, HTTPRedirectHandler, build_opener
from urllib.parse import urlparse
from zipfile import ZipFile

class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        redirected = super().redirect_request(request, fp, code, msg, headers, newurl)
        if urlparse(newurl).scheme != "https":
            raise ValueError("비암호화 리디렉션 차단")
        if urlparse(request.full_url).hostname != urlparse(newurl).hostname:
            redirected.remove_header("Authorization")
        return redirected

def get(url):
    request = Request(url, headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"], "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
    with build_opener(SafeRedirect()).open(request, timeout=20) as response:
        return response.read()

def main():
    repository = os.environ["GITHUB_REPOSITORY"]
    url = f"https://api.github.com/repos/{repository}/actions/artifacts?name=delivery-state&per_page=100"
    artifacts = json.loads(get(url))["artifacts"]
    valid = [item for item in artifacts if not item["expired"]]
    if not valid:
        print("이전 발송 기록 없음: 첫 실행 또는 보관기간 만료")
        return
    latest = max(valid, key=lambda item: item["id"])
    with ZipFile(io.BytesIO(get(latest["archive_download_url"]))) as archive:
        content = archive.read("deliveries.json")
    data = json.loads(content)
    if not isinstance(data, dict) or any(value not in ("pending", "sent") for value in data.values()):
        raise ValueError("발송 기록이 올바르지 않습니다.")
    path = Path(".state/deliveries.json")
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    print("이전 발송 기록 복원 완료")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        raise SystemExit("발송 기록 복원 실패: 중복 방지를 위해 실행 중단") from None
