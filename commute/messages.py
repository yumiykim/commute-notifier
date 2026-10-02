from commute.planner import clock

def build_message(day, start, recommended, latest, fetched_at, slot):
    title = "다음 날 등교 안내" if slot == "evening" else "당일 등교 안내"
    parts = [f"🚇 {title} · {day.isoformat()}", f"수업 {clock(start)} · 1번 출구 도착 마감 {clock(start - 600)}"]
    for label, journey in (("추천 (추가 여유 3분)", recommended), ("시간표상 마지막 가능", latest)):
        if journey is None:
            parts.append(f"\n{label}: 가능한 열차 없음")
            continue
        parts.extend([f"\n**{label}: 마포 {clock(journey.line5.departure)}**",
                      f"5호선 {journey.line5.destination}행 · 열차 {journey.line5.train_id}",
                      f"종로3가 도착 {clock(journey.line5.arrival)} → 3호선 {clock(journey.line3.departure)}",
                      f"3호선 {journey.line3.destination}행 · 열차 {journey.line3.train_id}",
                      f"충무로 도착 {clock(journey.line3.arrival)} · 1번 출구 예상 {clock(journey.exit_arrival)}"])
    parts.append(f"\n환승 도보 3분 · 출구 도보 2분\n시간표 기준이며 지연은 반영하지 않습니다.\n조회 {fetched_at:%Y-%m-%d %H:%M KST} · 출처: 서울교통공사 / 서울 열린데이터광장")
    return "\n".join(parts)
