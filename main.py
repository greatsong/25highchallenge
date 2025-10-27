import streamlit as st
import subprocess
import tempfile
import os
import sys

st.set_page_config(page_title="알고리즘 기초 — 파이썬 자동 채점기", page_icon="✅", layout="wide")

st.title("알고리즘 기초 — 파이썬 자동 채점기 + Google Sheets")
st.caption("※ 유저 코드: import/파일/네트워크/시스템 호출 금지. 앱은 Google Sheets에 점수를 기록합니다.")

# =============================
# Google Sheets (Service Account)
# =============================
try:
    from google.oauth2.service_account import Credentials
    import gspread
    SHEETS_READY = True
except Exception:
    SHEETS_READY = False

@st.cache_resource(show_spinner=False)
def get_worksheet():
    if not SHEETS_READY:
        return None
    sa_info = st.secrets.get("gcp_service_account", None)
    if not sa_info:
        return None
    creds = Credentials.from_service_account_info(sa_info, scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ])
    gc = gspread.authorize(creds)
    wb_name = st.secrets.get("sheets", {}).get("workbook_name", None)
    ws_name = st.secrets.get("sheets", {}).get("worksheet_scores", "scores")
    if not wb_name:
        return None
    try:
        sh = gc.open(wb_name)
    except gspread.SpreadsheetNotFound:
        sh = gc.create(wb_name)
    try:
        ws = sh.worksheet(ws_name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=ws_name, rows=2000, cols=20)
    header = ["timestamp", "student_id", "name", "problem", "got_weight", "total_weight", "score", "version"]
    vals = ws.get_all_values()
    if not vals or not vals[0] or vals[0] != header:
        ws.clear()
        ws.append_row(header)
    return ws

# 정답/테스트 버전 태그 (변경 이력 관리)
TESTS_VERSION = st.secrets.get("tests_version", "v1")

st.markdown("---")

# =============================
# 학생 정보 입력
# =============================
info1, info2, info3 = st.columns([1,1,1])
with info1:
    student_id = st.text_input("학번 (필수)", max_chars=40, placeholder="2025-001")
with info2:
    student_name = st.text_input("이름 (필수)", max_chars=40, placeholder="홍길동")
with info3:
    st.caption("Google Sheets 기록을 위해 학번/이름이 필요합니다.")

# =============================
# 문제 정의 (미리보기만 포함) — 실제 테스트는 secrets에서 로드
# =============================
problems = {
    "P01": {
        "name": "Count the Ones",
        "statement": (
            "세 자리 이진 문자열 s(각 문자 '0' 또는 '1')가 주어진다. "
            "s에 포함된 '1'의 개수를 출력한다. 입력은 한 줄이며, 출력은 정수 한 줄이다.\n"
            "예) s=101 → 2."
        ),
        "starter": """s = input().strip()
# 여기에 코드를 작성하세요
""",
        "preview": [
            {"in": "101\n", "out": "2\n"},
            {"in": "000\n", "out": "0\n"},
        ],
    },
    "P02": {
        "name": "Divide by Two Game",
        "statement": (
            "정수 N과 길이 N의 배열 a가 주어진다. 모든 원소가 홀수가 될 때까지, "
            "배열의 모든 원소를 동시에 2로 나누는 연산을 반복할 수 있다. 가능한 연산 횟수의 최댓값을 출력한다.\n"
            "입력: 첫 줄 N, 둘째 줄 a1..aN. 출력: 정수 한 줄."
        ),
        "starter": """n = int(input())
a = list(map(int, input().split()))
# 여기에 코드를 작성하세요
""",
        "preview": [
            {"in": "3\n8 12 40\n", "out": "2\n"},
            {"in": "4\n5 6 8 10\n", "out": "0\n"},
        ],
    },
    "P03": {
        "name": "Digit Sum Filter",
        "statement": (
            "정수 N, A, B가 주어진다. 1부터 N까지의 모든 정수 중 자릿수 합이 A 이상 B 이하인 수를 모두 더한 결과를 출력한다. "
            "자릿수 합은 정수를 10으로 나누며 나머지를 누적해 구한다."
        ),
        "starter": """n, a, b = map(int, input().split())
# 여기에 코드를 작성하세요
""",
        "preview": [
            {"in": "20 2 5\n", "out": "84\n"},
            {"in": "10 1 2\n", "out": "13\n"},
        ],
    },
    "P04": {
        "name": "Distinct Discs",
        "statement": (
            "정수 N과 N개의 직경 값이 주어진다. 같은 직경을 가진 디스크는 한 종류로 본다. "
            "서로 다른 직경의 개수를 출력한다. 입력은 첫 줄 N, 이후 N줄에 각 직경. 출력은 정수 한 줄."
        ),
        "starter": """n = int(input())
# 이후 줄들에서 정수 n개를 입력받아 처리하세요
""",
        "preview": [
            {"in": "4\n10\n8\n8\n6\n", "out": "3\n"},
            {"in": "3\n1\n1\n1\n", "out": "1\n"},
        ],
    },
    "P05": {
        "name": "Parity of Product",
        "statement": (
            "두 정수 A, B가 주어진다. A×B가 짝수면 'Even', 홀수면 'Odd'를 출력한다. 출력은 대소문자에 유의한다."
        ),
        "starter": """a, b = map(int, input().split())
# 여기에 코드를 작성하세요
""",
        "preview": [
            {"in": "3 4\n", "out": "Even\n"},
            {"in": "1 3\n", "out": "Odd\n"},
        ],
    },
    "P06": {
        "name": "Polygon Check",
        "statement": (
            "정수 N과 N개의 막대 길이가 주어진다. 가장 긴 막대의 길이가 나머지 막대 길이의 합보다 작으면 단순 다각형을 만들 수 있다. "
            "만들 수 있으면 'Yes', 아니면 'No'를 출력한다. 정렬 없이도 합과 최댓값만으로 판정할 수 있다."
        ),
        "starter": """n = int(input())
L = list(map(int, input().split()))
# 여기에 코드를 작성하세요
""",
        "preview": [
            {"in": "4\n3 4 5 6\n", "out": "Yes\n"},
            {"in": "3\n1 2 3\n", "out": "No\n"},
        ],
    },
    "P07": {
        "name": "Power Strip Planner",
        "statement": (
            "한 멀티탭에는 구멍이 A개 있다. 벽에 첫 멀티탭을 꽂으면 사용 가능한 소켓 수는 A가 된다. "
            "추가로 멀티탭을 연결할 때마다 연결에 1개를 쓰므로 소켓 수는 매번 A-1개씩 증가한다. "
            "필요한 소켓이 B개 이상이 되기까지 필요한 멀티탭 개수를 구하라."
        ),
        "starter": """a, b = map(int, input().split())
# 여기에 코드를 작성하세요
""",
        "preview": [
            {"in": "4 10\n", "out": "3\n"},
            {"in": "2 5\n", "out": "4\n"},
        ],
    },
    "P08": {
        "name": "Periodic Biscuits",
        "statement": (
            "매 A초마다 과자 B개가 만들어진다. 시간 T초 동안 만들어지는 과자의 총 개수를 출력한다. "
            "생산은 정확히 A의 배수 시점에만 이루어진다고 가정한다."
        ),
        "starter": """a, b, t = map(int, input().split())
# 여기에 코드를 작성하세요
""",
        "preview": [
            {"in": "3 5 7\n", "out": "10\n"},
            {"in": "2 4 9\n", "out": "16\n"},
        ],
    },
    "P09": {
        "name": "Pattern: Accepted or Not",
        "statement": (
            "문자열 s가 다음을 모두 만족하면 'AC', 아니면 'WA'를 출력한다: "
            "(1) s의 첫 글자는 'A'이다. (2) s의 3번째 문자부터 끝에서 두 번째 문자 사이에 'C'가 정확히 1번 등장한다. "
            "(3) 위 두 위치를 제외한 나머지 문자는 모두 소문자 알파벳이다."
        ),
        "starter": """s = input().strip()
# 여기에 코드를 작성하세요
""",
        "preview": [
            {"in": "AtCoder\n", "out": "AC\n"},
            {"in": "ACoder\n", "out": "WA\n"},
        ],
    },
    "P10": {
        "name": "Make Seven with Signs",
        "statement": (
            "네 자리 숫자 문자열 s가 주어진다. 인접한 자리 사이에 '+' 또는 '-'를 넣어 계산한 결과가 7이 되는 식을 하나 만들어라. "
            "출력은 예를 들어 s=1222일 때 '1+2+2+2=7'처럼 등호와 함께 한 줄로 출력한다. 여러 해답이 있을 수 있으며, 입력의 네 자릿수 순서는 바뀌지 않는다."
        ),
        "starter": """s = input().strip()
# 여기에 코드를 작성하세요
""",
        "preview": [
            {"in": "1222\n", "out": "1+2+2+2=7\n"},
            {"in": "3029\n", "out": "3+0+2+9=7\n"},
        ],
    },
}

problem_keys = list(problems.keys())

# =============================
# 사이드바
# =============================
with st.sidebar:
    st.header("문제 선택")
    key = st.selectbox(
        "문제", options=problem_keys,
        format_func=lambda k: f"{k} — {problems[k]['name']}",
    )
    st.markdown("---")
    st.subheader("채점 옵션")
    time_limit = st.number_input("시간 제한(초)", min_value=1.0, max_value=10.0, value=2.0, step=0.5)
    whitespace_insensitive = st.checkbox("공백/개행 무시 비교", value=True)

# =============================
# Secrets에서 테스트 로드
# =============================

def load_tests_from_secrets(problem_key: str):
    cfg = st.secrets.get("tests", {})
    raw = cfg.get(problem_key, None)
    if not isinstance(raw, list):
        return None
    tests = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        if "in" not in item or "out" not in item:
            continue
        t = {
            "in": str(item["in"]),
            "out": str(item["out"]),
            "name": str(item.get("name", "")),
            "hidden": bool(item.get("hidden", False)),
        }
        try:
            w = int(item.get("weight", 1))
            if w <= 0:
                w = 1
        except Exception:
            w = 1
        t["weight"] = w
        tests.append(t)
    return tests if tests else None

# =============================
# 유틸
# =============================

dangerous_keywords = [
    "import ", "from ", "open(", "__", "os.", "sys.", "subprocess", "socket",
    "requests", "shutil", "pathlib", "glob", "eval(", "exec(", "compile(",
]

def has_dangerous(code_str: str) -> str:
    lower = code_str.lower()
    for k in dangerous_keywords:
        if k in lower:
            return k
    return ""


def norm_output(s: str, trim_ws: bool) -> str:
    if trim_ws:
        lines = [ln.strip() for ln in s.strip().splitlines() if ln.strip() != ""]
        return "\n".join(lines)
    return s.strip()

# ----------------------------
# 특수 채점기(문항별 커스텀 판정)
# ----------------------------

def custom_judge(problem_key: str, raw_input: str, user_out: str, trim_ws: bool):
    """문항별 커스텀 채점 로직.
    True/False를 반환하면 그 결과를 사용하고, None이면 기본 문자열 비교로 돌아갑니다.
    """
    # P10: 여러 가능한 올바른 식 허용
    if problem_key == "P10":
        s = norm_output(raw_input, trim_ws)
        s = s.replace("\n", "").replace("\r", "")
        if len(s) != 4 or not s.isdigit():
            return False
        out = user_out.replace(" ", "").replace("\t", "")
        out = out.strip()
        if not out.endswith("=7"):
            return False
        expr = out[:-2]
        if len(expr) != 7:
            return False
        d0, o1, d1, o2, d2, o3, d3 = expr[0], expr[1], expr[2], expr[3], expr[4], expr[5], expr[6]
        if any(o not in "+-" for o in (o1, o2, o3)):
            return False
        if any(not d.isdigit() for d in (d0, d1, d2, d3)):
            return False
        if [d0, d1, d2, d3] != list(s):
            return False
        vals = [int(d0), int(d1), int(d2), int(d3)]
        ops = [o1, o2, o3]
        total = vals[0]
        for i in range(3):
            if ops[i] == '+':
                total += vals[i+1]
            else:
                total -= vals[i+1]
        return total == 7
    return None

# =============================
# 본문 UI
# =============================
col1, col2 = st.columns([1.3, 1])

with col1:
    st.subheader(f"{key} — {problems[key]['name']}")
    st.write(problems[key]["statement"]) 

    loaded_tests = load_tests_from_secrets(key)
    if loaded_tests is None:
        st.warning("secrets에서 테스트를 찾지 못했습니다. ↗ Settings → Secrets에서 tests를 설정하세요.")

    # 공개 미리보기: hidden=False 우선 2개
    preview = []
    source_preview = problems[key].get("preview", [])
    if loaded_tests:
        visible = [t for t in loaded_tests if not t.get("hidden", False)]
        if len(visible) >= 2:
            preview = visible[:2]
        elif len(loaded_tests) >= 2:
            preview = loaded_tests[:2]
    if not preview:
        preview = source_preview
        st.info("secrets 미설정/부족 → 내장 preview 표시")

    st.markdown("**공개 예시 (미리보기 2개)**")
    for idx, t in enumerate(preview, 1):
        with st.expander(f"예시 {idx} {('· ' + t.get('name')) if t.get('name') else ''}"):
            st.code(t["in"], language="text")
            st.code(t["out"], language="text")

with col2:
    st.subheader("내 코드")
    code = st.text_area(
        label="여기에 파이썬 코드를 작성하세요 (표준 입력 사용)",
        value=problems[key]["starter"],
        height=320,
        placeholder="print('hello')"
    )
    st.caption("금지: import / 파일/네트워크 / 시스템 호출 / eval/exec 등")
    run_btn = st.button("✅ 채점하기", type="primary")
    submit_btn = st.button("📤 채점 + 점수 제출", type="secondary")

# =============================
# 채점 로직
# =============================

def grade_and_collect(code: str, key: str):
    bad = has_dangerous(code)
    if bad:
        st.error(f"보안상 금지된 표현이 발견되었습니다: `{bad.strip()}`")
        return None
    tests_to_run = load_tests_from_secrets(key)
    if not tests_to_run or not (5 <= len(tests_to_run) <= 10):
        st.error("테스트 케이스를 secrets에 문제당 5~10개 저장하세요.")
        return None
    with tempfile.TemporaryDirectory() as tmp:
        user_py = os.path.join(tmp, "user_code.py")
        with open(user_py, "w", encoding="utf-8") as f:
            f.write(code)
        results = []
        total_weight = sum(t.get("weight", 1) for t in tests_to_run)
        got_weight = 0
        for idx, t in enumerate(tests_to_run, 1):
            inp, expected = t["in"], t["out"]
            name = t.get("name", "")
            weight = t.get("weight", 1)
            try:
                proc = subprocess.run([sys.executable, user_py], input=inp, text=True, capture_output=True, timeout=float(time_limit))
                out, err, rc = proc.stdout, proc.stderr, proc.returncode
                status = "OK"
                if rc != 0:
                    status = "RE(런타임 에러)"
                else:
                    # 커스텀 채점 우선
                    cj = custom_judge(key, inp, out, whitespace_insensitive)
                    if cj is True:
                        pass
                    elif cj is False:
                        status = "WA(틀렸습니다)"
                    elif norm_output(out, whitespace_insensitive) != norm_output(expected, whitespace_insensitive):
                        status = "WA(틀렸습니다)"
                    else:
                        got_weight += weight
                results.append({"idx": idx, "name": name, "판정": status, "가중치": weight, "입력": inp, "기대 출력": expected, "내 출력": out, "에러": err})
            except subprocess.TimeoutExpired:
                results.append({"idx": idx, "name": name, "판정": "TLE(시간 초과)", "가중치": weight, "입력": inp, "기대 출력": expected, "내 출력": "", "에러": "시간 제한 초과"})
        score = int(100 * got_weight / max(1, total_weight))
        return {"results": results, "got_weight": got_weight, "total_weight": total_weight, "score": score}

if run_btn or submit_btn:
    if not student_id or not student_name:
        st.error("학번과 이름을 입력하세요.")
        st.stop()
    graded = grade_and_collect(code, key)
    if not graded:
        st.stop()
    got_weight = graded["got_weight"]; total_weight = graded["total_weight"]; score = graded["score"]; results = graded["results"]
    st.success(f"점수: {score}점 · 획득 가중치 {got_weight}/{total_weight}")
    for r in results:
        color = {"OK": "✅", "WA(틀렸습니다)": "❌", "RE(런타임 에러)": "💥", "TLE(시간 초과)": "⏰"}.get(r["판정"], "")
        title = f"테스트 {r['idx']} — {r['판정']}" + (f" · {r['name']}" if r.get('name') else '')
        with st.expander(f"{color} {title}"):
            st.markdown("**가중치**: " + str(r["가중치"]))
            st.markdown("**입력**"); st.code(r["입력"], language="text")
            st.markdown("**기대 출력**"); st.code(r["기대 출력"], language="text")
            st.markdown("**내 출력**"); st.code(r["내 출력"], language="text")
            if r["에러"]:
                st.markdown("**에러 메시지**"); st.code(r["에러"], language="text")

# 제출: Google Sheets 업서트
if submit_btn:
    ws = get_worksheet()
    if ws is None:
        st.error("Google Sheets 설정이 완료되지 않았습니다. requirements 설치/Secrets를 확인하세요.")
    else:
        import datetime
        ts = datetime.datetime.utcnow().isoformat() + "Z"
        row = [ts, student_id, student_name, key, str(got_weight), str(total_weight), str(score), str(TESTS_VERSION)]
        all_vals = ws.get_all_values()
        header = all_vals[0] if all_vals else []
        idx_student = header.index("student_id") if "student_id" in header else 1
        idx_problem = header.index("problem") if "problem" in header else 3
        target_row = None
        for i in range(1, len(all_vals)):
            if all_vals[i][idx_student] == student_id and all_vals[i][idx_problem] == key:
                target_row = i + 1
                break
        if target_row:
            ws.update(f"A{target_row}:H{target_row}", [row])
            st.success("기존 기록을 최신 기준으로 업데이트했습니다 (업서트).")
        else:
            ws.append_row(row)
            st.success("점수를 Google Sheets에 제출했습니다.")

st.markdown("---")
st.caption("Tip: secrets의 각 테스트에 name/weight/hidden을 선택적으로 넣으면 운영이 편리합니다. tests_version으로 정답/테스트 변경 이력을 관리하세요.")
