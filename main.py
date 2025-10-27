import streamlit as st
import subprocess
import tempfile
import os
import sys

st.set_page_config(page_title="ABC 자동 채점기", page_icon="✅", layout="wide")

st.title("🧪 AtCoder ABC — 기초 파이썬 자동 채점기")
st.caption("※ import / 파일 접근 / 네트워크 / 시스템 호출 금지. 표준 입력/출력만 사용하세요.")

# -----------------------------
# 문제 정의 (설명 + 공개 테스트 미리보기 2개)
#   - 실제 채점용 테스트는 Streamlit Secrets에서 불러옵니다.
#   - 각 문제당 5~10개의 테스트를 secrets에 저장하세요.
# -----------------------------
problems = {
    "ABC081A": {
        "name": "Placing Marbles (ABC081A)",
        "statement": "3자리 문자열 s(각 문자 \"0\" 또는 \"1\")의 '1' 개수를 출력.",
        "starter": "s = input().strip()
# 여기에 코드를 작성하세요
# 예: print( ... )
",
        # 공개 미리보기 예시 (secrets가 없을 때 UI 미리보기용)
        "preview": [
            {"in": "101
", "out": "2
"},
            {"in": "000
", "out": "0
"},
        ],
    },
    "ABC081B": {
        "name": "Shift only (ABC081B)",
        "statement": "배열의 모든 원소가 홀수가 될 때까지 동시에 2로 나눌 수 있는 횟수.",
        "starter": "n = int(input())
a = list(map(int, input().split()))
# 여기에 코드를 작성하세요
",
        "preview": [
            {"in": "3
8 12 40
", "out": "2
"},
            {"in": "4
5 6 8 10
", "out": "0
"},
        ],
    },
    "ABC083B": {
        "name": "Some Sums (ABC083B)",
        "statement": "1..N에서 자릿수 합이 [A,B]인 수들의 총합.",
        "starter": "n, a, b = map(int, input().split())
# 여기에 코드를 작성하세요
",
        "preview": [
            {"in": "20 2 5
", "out": "84
"},
            {"in": "10 1 2
", "out": "13
"},
        ],
    },
    "ABC085B": {
        "name": "Kagami Mochi (ABC085B)",
        "statement": "서로 다른 직경의 개수.",
        "starter": "n = int(input())
# 이후 줄들에서 정수 n개를 입력받아 처리하세요
",
        "preview": [
            {"in": "4
10
8
8
6
", "out": "3
"},
            {"in": "3
1
1
1
", "out": "1
"},
        ],
    },
    "ABC086A": {
        "name": "Product (ABC086A)",
        "statement": "두 수의 곱이 짝수면 Even, 홀수면 Odd.",
        "starter": "a, b = map(int, input().split())
# 여기에 코드를 작성하세요
",
        "preview": [
            {"in": "3 4
", "out": "Even
"},
            {"in": "1 3
", "out": "Odd
"},
        ],
    },
    "ABC117B": {
        "name": "Polygon (ABC117B)",
        "statement": "가장 긴 변 < 나머지 합이면 Yes, 아니면 No.",
        "starter": "n = int(input())
L = list(map(int, input().split()))
# 여기에 코드를 작성하세요
",
        "preview": [
            {"in": "4
3 4 5 6
", "out": "Yes
"},
            {"in": "3
1 2 3
", "out": "No
"},
        ],
    },
    "ABC139B": {
        "name": "Power Socket (ABC139B)",
        "statement": "멀티탭을 연결해 소켓 수가 B개 이상이 될 때까지 필요한 멀티탭 개수.",
        "starter": "a, b = map(int, input().split())
# 여기에 코드를 작성하세요
",
        "preview": [
            {"in": "4 10
", "out": "3
"},
            {"in": "2 5
", "out": "4
"},
        ],
    },
    "ABC125A": {
        "name": "Biscuit Generator (ABC125A)",
        "statement": "t초 동안 A초마다 B개 생성 → 총 개수.",
        "starter": "a, b, t = map(int, input().split())
# 여기에 코드를 작성하세요
",
        "preview": [
            {"in": "3 5 7
", "out": "10
"},
            {"in": "2 4 9
", "out": "16
"},
        ],
    },
    "ABC104B": {
        "name": "AcCepted (ABC104B)",
        "statement": "첫 글자 'A', 가운데에 'C' 1개, 나머지는 모두 소문자면 AC, 아니면 WA.",
        "starter": "s = input().strip()
# 여기에 코드를 작성하세요
",
        "preview": [
            {"in": "AtCoder
", "out": "AC
"},
            {"in": "ACoder
", "out": "WA
"},
        ],
    },
    "ABC079C": {
        "name": "Train Ticket (ABC079C)",
        "statement": "4자리 사이에 + 또는 - 를 넣어 결과가 7이 되는 식 출력 (예: 1+2+2+2=7).",
        "starter": "s = input().strip()
# 여기에 코드를 작성하세요
",
        "preview": [
            {"in": "1222
", "out": "1+2+2+2=7
"},
            {"in": "3029
", "out": "3+0+2+9=7
"},
        ],
    },
}

problem_keys = list(problems.keys())

# -----------------------------
# 사이드바: 문제 선택
# -----------------------------
with st.sidebar:
    st.header("문제 선택")
    key = st.selectbox(
        "문제(번호)",
        options=problem_keys,
        format_func=lambda k: f"{k} — {problems[k]['name']}",
    )
    st.markdown("---")
    st.subheader("채점 옵션")
    time_limit = st.number_input("시간 제한(초)", min_value=1.0, max_value=10.0, value=2.0, step=0.5)
    whitespace_insensitive = st.checkbox("공백/개행 무시 비교", value=True)

prob = problems[key]

# -----------------------------
# 본문: 문제 설명 / 예시
# -----------------------------
col1, col2 = st.columns([1.3, 1])
with col1:
    st.subheader(f"{key} · {problems[key]['name']}")
    st.write(problems[key]["statement"]) 

    # 비공개 채점용 테스트 로드 (secrets)
    def load_tests(k):
        try:
            cfg = st.secrets.get("tests", {})
            tests = cfg.get(k, None)
            if tests is None:
                return None
            # 기대 형태: [{"in": "...", "out": "..."}, ...]
            if not isinstance(tests, list):
                return None
            good = []
            for t in tests:
                if isinstance(t, dict) and "in" in t and "out" in t:
                    good.append({"in": str(t["in"]), "out": str(t["out"])})
            return good if good else None
        except Exception:
            return None

    loaded_tests = load_tests(key)

    # 미리보기 2개 (secrets 있으면 앞 2개, 없으면 preview 사용)
    st.markdown("**공개 예시 (미리보기 2개)**")
    preview_tests = []
    if loaded_tests and len(loaded_tests) >= 2:
        preview_tests = loaded_tests[:2]
    else:
        preview_tests = problems[key].get("preview", [])
        st.info("secrets에 테스트가 없거나 2개 미만입니다. preview 예시를 표시합니다.")

    for idx, t in enumerate(preview_tests, 1):
        with st.expander(f"예시 {idx}"):
            st.code(t["in"], language="text")
            st.code(t["out"], language="text")

with col2:
    st.subheader("내 코드")
    code = st.text_area(
        label="여기에 파이썬 코드를 작성하세요 (표준 입력 사용)",
        value=problems[key]["starter"],
        height=300,
        placeholder="print('hello')"
    )
    st.caption("금지: import / 파일 접근 / 네트워크 / 시스템 호출 / eval/exec 등")
    run_btn = st.button("✅ 채점하기", type="primary")
    st.subheader("내 코드")
    code = st.text_area(
        label="여기에 파이썬 코드를 작성하세요 (표준 입력 사용)",
        value=prob["starter"],
        height=300,
        placeholder="print('hello')"
    )
    st.caption("금지: import / 파일 접근 / 네트워크 / 시스템 호출 / eval/exec 등")
    run_btn = st.button("✅ 채점하기", type="primary")

# -----------------------------
# 보안/금지 검사 (간단 룰)
# -----------------------------
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

# -----------------------------
# 채점 실행
# -----------------------------
if run_btn:
    bad = has_dangerous(code)
    if bad:
        st.error(f"보안상 금지된 표현이 발견되었습니다: `{bad.strip()}`")
        st.stop()

    # 임시 파일에 코드 저장
    with tempfile.TemporaryDirectory() as tmp:
        user_py = os.path.join(tmp, "user_code.py")
        with open(user_py, "w", encoding="utf-8") as f:
            f.write(code)

        results = []
        passed = 0

        # 채점용 테스트는 secrets에서 불러옵니다.
        tests_to_run = loaded_tests
        if not tests_to_run or len(tests_to_run) < 5 or len(tests_to_run) > 10:
            st.error("테스트 케이스를 secrets에 5~10개 저장하세요. 현재 유효한 테스트 세트를 찾을 수 없습니다.")
            st.stop()

        for idx, t in enumerate(tests_to_run, 1):
            inp = t["in"]
            expected = t["out"]

            try:
                proc = subprocess.run(
                    [sys.executable, user_py],
                    input=inp,
                    text=True,
                    capture_output=True,
                    timeout=float(time_limit),
                )
                out = proc.stdout
                err = proc.stderr
                rc = proc.returncode
                status = "OK"

                def norm(s: str) -> str:
                    if whitespace_insensitive:
                        # 줄 단위로 공백을 좌우 trim하고 빈 줄 제거하여 비교
                        lines = [ln.strip() for ln in s.strip().splitlines() if ln.strip() != ""]
                        return "\n".join(lines)
                    return s.strip()

                if rc != 0:
                    status = "RE(런타임 에러)"
                elif norm(out) != norm(expected):
                    status = "WA(틀렸습니다)"
                else:
                    passed += 1

                results.append({
                    "테스트": idx,
                    "판정": status,
                    "입력": inp,
                    "기대 출력": expected,
                    "내 출력": out,
                    "에러": err,
                })

            except subprocess.TimeoutExpired:
                results.append({
                    "테스트": idx,
                    "판정": "TLE(시간 초과)",
                    "입력": inp,
                    "기대 출력": expected,
                    "내 출력": "",
                    "에러": "시간 제한 초과",
                })

        score = int(100 * passed / len(tests_to_run))
        st.success(f"총합: {passed}/{len(tests_to_run)} 통과 · 점수: {score}점")
        st.success(f"총합: {passed}/{len(prob['tests'])} 통과 · 점수: {score}점")

        # 결과 표
        for r in results:
            color = {
                "OK": "✅",
                "WA(틀렸습니다)": "❌",
                "RE(런타임 에러)": "💥",
                "TLE(시간 초과)": "⏰",
            }.get(r["판정"], "")

            with st.expander(f"{color} 테스트 {r['테스트']} — {r['판정']}"):
                st.markdown("**입력**")
                st.code(r["입력"], language="text")
                st.markdown("**기대 출력**")
                st.code(r["기대 출력"], language="text")
                st.markdown("**내 출력**")
                st.code(r["내 출력"], language="text")
                if r["에러"]:
                    st.markdown("**에러 메시지**")
                    st.code(r["에러"], language="text")

st.markdown("---")
st.caption("Tip: 예시는 '공개 테스트'입니다. 수업/실전용으로는 숨김 테스트를 problems['tests']에 추가하여 더 강건하게 채점하세요.")
