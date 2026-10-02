from commute.calendar import SEOUL
from commute.planner import clock

def build_message(day, semester_name, cases, fetched_at, slot):
    title = "내일" if slot == "evening" else "오늘"
    parts = [f"🚇 **{title} {day.month}/{day.day} 등교 안내 · {semester_name}**"]
    for minutes, journey in cases.items():
        parts.append(f"\n**🚶 환승 도보 {minutes}분**")
        if journey is None:
            parts.append("해당 조건으로 도착 가능한 열차가 없습니다.")
            continue
        parts.extend([f"🟣 **마포역 5호선 · {clock(journey.line5.departure)} 탑승**",
                      f"　↓ 종로3가 {clock(journey.line5.arrival)} 도착",
                      f"🟠 **3호선 · {clock(journey.line3.departure)} 탑승**",
                      "　↓",
                      f"🚶 **충무로역 1번출구 · {clock(journey.exit_arrival)} 도착 예상**"])
    fetched_at = fetched_at.astimezone(SEOUL)
    parts.append(f"\n-# 🕒 최근 조회: {fetched_at.month}/{fetched_at.day} {fetched_at:%H:%M}")
    return "\n".join(parts)
