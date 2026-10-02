"""승인된 서울시 공식 HTTP API. 예외에 인증키나 요청 URL을 넣지 않는다."""
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen
from commute.planner import Leg

SERVICE = "SearchSTNTimeTableByIDService"
STATIONS = {"mapo": "2529", "jongno5": "2535", "jongno3": "0319", "chungmuro": "0321"}

class SeoulError(RuntimeError):
    pass

def seconds(value):
    try:
        hours, minutes, secs = map(int, value.split(":"))
        if not (0 <= hours <= 25 and 0 <= minutes < 60 and 0 <= secs < 60):
            raise ValueError
        return hours * 3600 + minutes * 60 + secs
    except (ValueError, AttributeError):
        raise SeoulError("시간표의 시각 형식을 확인할 수 없습니다.") from None

def join_trains(origins, destinations):
    def identity(row):
        return (row["TRAIN_NO"], row["ORIGINSTATION"], row["DESTSTATION"])
    try:
        arrivals = {}
        for row in destinations:
            key = identity(row)
            if key in arrivals:
                raise SeoulError("동일 열차의 시간표가 중복되어 연결할 수 없습니다.")
            arrivals[key] = row
        legs = []
        seen = set()
        for row in origins:
            key = identity(row)
            if key in seen:
                raise SeoulError("동일 열차의 시간표가 중복되어 연결할 수 없습니다.")
            seen.add(key)
            other = arrivals.get(key)
            if other is None:
                continue  # 두 역 모두 정차하는 열차만 사용
            departure = seconds(row["LEFTTIME"])
            arrival = seconds(other["ARRIVETIME"])
            if not departure or not arrival:
                continue  # API의 결측 시각 00:00:00 제외
            if arrival < departure:
                arrival += 86400
            duration = arrival - departure
            if duration > 3600:
                raise SeoulError("역간 운행 시간이 비정상입니다.")
            legs.append(Leg(row["TRAIN_NO"], departure, arrival, row.get("SUBWAYENAME", "")))
        if not legs:
            raise SeoulError("두 역을 연결하는 열차를 찾지 못했습니다.")
        return legs
    except KeyError:
        raise SeoulError("시간표에 필수 열차 정보가 없습니다.") from None

class SeoulClient:
    def __init__(self, key, allow_http=False):
        if not key:
            raise SeoulError("SEOUL_API_KEY를 설정하세요.")
        if not allow_http:
            raise SeoulError("서울시 HTTP API 사용 승인 후 ALLOW_HTTP_SEOUL=true를 설정하세요.")
        self.key = key

    def timetable(self, station, week_tag):
        rows = []
        start = 1
        while True:
            url = f"http://openapi.seoul.go.kr:8088/{quote(self.key, safe='')}/json/{SERVICE}/{start}/{start + 999}/{station}/{week_tag}/2/"
            try:
                with urlopen(url, timeout=20) as response:
                    data = json.load(response)
            except HTTPError as error:
                raise SeoulError(f"서울시 시간표 조회 실패 (HTTP {error.code})") from None
            except (URLError, TimeoutError, OSError, ValueError):
                raise SeoulError("서울시 시간표 서버에 연결할 수 없거나 응답이 올바르지 않습니다.") from None
            payload = data.get(SERVICE, data)
            code = payload.get("RESULT", {}).get("CODE")
            if code != "INFO-000":
                raise SeoulError(f"서울시 시간표 조회 실패 ({code or 'UNKNOWN'})")
            batch = payload.get("row", [])
            if not batch:
                raise SeoulError("서울시 시간표가 비어 있습니다.")
            for row in batch:
                if row.get("STATION_CD") != station or row.get("INOUT_TAG") != "2" or row.get("WEEK_TAG") != str(week_tag):
                    raise SeoulError("응답의 역·방향·요일이 요청과 다릅니다.")
            rows.extend(batch)
            if len(rows) >= int(payload.get("list_total_count", 0)):
                return rows
            start += len(batch)
            if start > 10000:
                raise SeoulError("시간표가 예상 범위를 초과했습니다.")

    def route(self, week_tag):
        data = {name: self.timetable(code, week_tag) for name, code in STATIONS.items()}
        return (join_trains(data["mapo"], data["jongno5"]),
                join_trains(data["jongno3"], data["chungmuro"]))
