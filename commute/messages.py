from commute.calendar import SEOUL
from commute.planner import clock

def build_message(day, semester_name, cases, fetched_at, slot):
    title = "내일" if slot == "evening" else "오늘"
    weekday = "월화수목금토일"[day.weekday()]
    parts = [f"**{title} {day.month}/{day.day}({weekday}) 등교 안내 · {semester_name}**"]
    walking, running = cases.get(3), cases.get(2)
    if walking and running:
        if walking.line5.departure == running.line5.departure:
            parts.append(f"\n> **마포역 5호선 {clock(walking.line5.departure)} 탑승**")
        else:
            parts.extend(["\n> **마포역 탑승**",
                          f"> 🚶 3분 환승 **{clock(walking.line5.departure)}** · 🏃 2분 환승 **{clock(running.line5.departure)}**"])
            difference = running.line5.departure - walking.line5.departure
            if difference > 0:
                minutes, seconds = divmod(difference, 60)
                duration = f"{minutes}분" if minutes else ""
                if seconds:
                    duration += f" {seconds}초" if duration else f"{seconds}초"
                parts.append(f"> 2분 환승 시 {duration} 늦게 탑승 가능")
    elif walking or running:
        journey = walking or running
        condition = "🚶 3분 환승" if walking else "🏃 2분 환승"
        parts.append(f"\n> **마포역 5호선 {clock(journey.line5.departure)} 탑승** ({condition})")
    else:
        parts.append("\n> **도착 마감에 맞는 열차가 없습니다.**")
    for minutes, journey in cases.items():
        parts.append(f"\n**{minutes}분 환승**")
        if journey is None:
            parts.append("해당 조건으로 도착 가능한 열차가 없습니다.")
            continue
        parts.extend([f"🟣 마포역 5호선 **{clock(journey.line5.departure)}** 탑승",
                      f"종로3가 {clock(journey.line5.arrival)} 도착",
                      f"🟠 3호선 **{clock(journey.line3.departure)}** 탑승",
                      f"충무로역 1번출구 **{clock(journey.exit_arrival)}** 도착 예상"])
    fetched_at = fetched_at.astimezone(SEOUL)
    parts.append(f"\n-# 최근 조회: {fetched_at.month}/{fetched_at.day} {fetched_at:%H:%M}")
    return "\n".join(parts)
