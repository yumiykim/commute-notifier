from commute.calendar import SEOUL
from commute.planner import clock
from commute.timing import action_times, minute_clock, duration

def build_message(day, semester_name, cases, fetched_at, slot, settings):
    title = "내일" if slot == "evening" else "오늘"
    weekday = "월화수목금토일"[day.weekday()]
    parts = [f"**{title} {day.month}/{day.day}({weekday}) 등교 안내 · {semester_name}**"]
    preferred = cases.get(settings.preferred_transfer_seconds)
    comparison = cases.get(settings.comparison_transfer_seconds)
    if preferred:
        actions = action_times(preferred.line5.departure, settings)
        parts.extend([f"\n> **집 출발 {minute_clock(actions.home_departure)} · 마포역 3번출구 {minute_clock(actions.entrance_arrival)}까지**",
                      f"> **승강장 탑승 준비 {minute_clock(actions.platform_ready)}까지**",
                      f"> 🟣 공식 열차 시각 **{clock(preferred.line5.departure)}**"])
    else:
        parts.append("\n> **기본 추천 조건으로 도착 마감에 맞는 열차가 없습니다.**")
        if comparison:
            parts.append("> 빠른 환승 경로만 가능합니다.")

    def details(label, journey):
        parts.append(f"\n**{label}**")
        if journey is None:
            parts.append("해당 조건으로 도착 가능한 열차가 없습니다.")
            return
        parts.extend([f"🟣 마포역 5호선 **{clock(journey.line5.departure)}** 탑승",
                      f"종로3가 {clock(journey.line5.arrival)} 도착",
                      f"🟠 3호선 **{clock(journey.line3.departure)}** 탑승",
                      f"충무로역 1번출구 **{clock(journey.exit_arrival)}** 도착 예상"])

    details(f"기본 추천 · 환승 {duration(settings.preferred_transfer_seconds)}", preferred)
    details(f"빠른 환승 · 환승 {duration(settings.comparison_transfer_seconds)}", comparison)
    fetched_at = fetched_at.astimezone(SEOUL)
    parts.append(f"\n-# 최근 조회: {fetched_at.month}/{fetched_at.day} {fetched_at:%H:%M}")
    return "\n".join(parts)
