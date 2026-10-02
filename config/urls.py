from django.http import JsonResponse
from django.urls import path

def index(request):
    return JsonResponse({"service": "commute-notifier", "status": "ready", "route": "마포 → 종로3가 → 충무로 1번 출구", "notice": "실제 시간표 조회: manage.py notify_commute. 자동 발송에는 GitHub Secrets 설정이 필요합니다."}, json_dumps_params={"ensure_ascii": False})

urlpatterns = [path("", index)]
