import re

BASELINES = ["pub", "5.2", "5.2ha", "5.2fl", "5.3", "6.0", "3.9", "3.8"]
BASELINES_ALT = "|".join(BASELINES)

# Terminal special rules (1.4)
TERMINAL_FEATURE = re.compile(r"^\d+-feature-\d+-.+$")
TERMINAL_FIX = re.compile(r"^\d+-fix-\d+-.+$")
TERMINAL_PRIVATE = re.compile(r"^private_(" + BASELINES_ALT + r")_.+_\d{8}$")
TERMINAL_PRIVATE_F = re.compile(r"^private_(" + BASELINES_ALT + r")_.+_\d{8}f_\d+_\d{8}$")
TERMINAL_PRIVATE_T = re.compile(r"^private_(" + BASELINES_ALT + r")_.+_\d{8}t_\d+_\d{8}$")

def _is_terminal(name):
    return bool(
        TERMINAL_FEATURE.match(name)
        or TERMINAL_FIX.match(name)
        or TERMINAL_PRIVATE.match(name)
        or TERMINAL_PRIVATE_F.match(name)
        or TERMINAL_PRIVATE_T.match(name)
    )

# General rules (1.3)
GENERAL_MASTER = re.compile(
    r"^master$"
    r"|^master_(" + BASELINES_ALT + r")_.+$"
)
GENERAL_RELEASE_BASE = re.compile(
    r"^release_(" + BASELINES_ALT + r")_.+_\d{8}$"
)
GENERAL_RELEASE_F = re.compile(
    r"^release_(" + BASELINES_ALT + r")_.+_\d{8}f_\d+_\d{8}_.+$"
)
GENERAL_RELEASE_T = re.compile(
    r"^release_(" + BASELINES_ALT + r")_.+_\d{8}t_\d+_\d{8}(_.+)?$"
)
GENERAL_RELEASE_C = re.compile(
    r"^release_(" + BASELINES_ALT + r")_.+_\d{8}c_.+$"
)
GENERAL_FEATURE = re.compile(
    r"^feature_(" + BASELINES_ALT + r")_.+_\d{8}_\d+_.+$"
)
GENERAL_BUGFIX = re.compile(r"^bugfix_.+$")

# Multi-product (1.5.8): master_<product>_<baseline>_<source>
GENERAL_MASTER_PRODUCT = re.compile(
    r"^master_[a-z][a-z0-9]*_(" + BASELINES_ALT + r")_.+$"
)
GENERAL_RELEASE_PRODUCT = re.compile(
    r"^release_[a-z][a-z0-9]*_(" + BASELINES_ALT + r")_.+_\d{8}$"
)
GENERAL_RELEASE_PRODUCT_F = re.compile(
    r"^release_[a-z][a-z0-9]*_(" + BASELINES_ALT + r")_.+_\d{8}f_\d+_\d{8}_.+$"
)
GENERAL_RELEASE_PRODUCT_T = re.compile(
    r"^release_[a-z][a-z0-9]*_(" + BASELINES_ALT + r")_.+_\d{8}t_\d+_\d{8}(_.+)?$"
)

def _is_general(name):
    return bool(
        GENERAL_MASTER.match(name)
        or GENERAL_RELEASE_BASE.match(name)
        or GENERAL_RELEASE_F.match(name)
        or GENERAL_RELEASE_T.match(name)
        or GENERAL_RELEASE_C.match(name)
        or GENERAL_FEATURE.match(name)
        or GENERAL_BUGFIX.match(name)
        or GENERAL_MASTER_PRODUCT.match(name)
        or GENERAL_RELEASE_PRODUCT.match(name)
        or GENERAL_RELEASE_PRODUCT_F.match(name)
        or GENERAL_RELEASE_PRODUCT_T.match(name)
    )

def check_branch(name):
    if _is_terminal(name):
        return "PASS"
    if _is_general(name):
        return "PASS"
    if re.search(r"[A-Z\u4e00-\u9fff]", name):
        return "FAIL (uppercase or chinese)"
    if re.search(r"[^a-z0-9_.\-]", name):
        return "FAIL (invalid chars)"
    return "FAIL (structure/whitelist)"

# Test cases from GIT_WORKFLOW.md Section 5
cases = [
    ("master", "PASS"),
    ("master_5.2_3.2", "PASS"),
    ("master_nmst_5.2_3.2", "PASS"),
    ("release_pub_3.8_20221224", "PASS"),
    ("release_5.2_3.2_20221024", "PASS"),
    ("release_5.2_3.2_20221024f_34543_20221105_new_vod", "PASS"),
    ("release_6.0_3.9_20221024t_34543_20221105_ccb_test", "PASS"),
    ("release_5.2_3.2_20221024c_ccb", "PASS"),
    ("feature_5.2_3.2_20221024_45678_new_vod", "PASS"),
    ("bugfix_fix_pstn_audio", "PASS"),
    ("584778-feature-584778-show-type-ts", "PASS"),
    ("124-fix-34533-fix-no-video-bug", "PASS"),
    ("private_5.2_3.2_20231024", "PASS"),
    ("private_6.0_3.9_20231024f_34566_20231101", "PASS"),
    ("private_6.0_3.9_20231024t_34777_20231106", "PASS"),
    ("Feature_5.3_中文描述", "FAIL"),
    ("feature_5.5_test", "FAIL"),
    ("feature-5.3-test", "FAIL"),
]

all_ok = True
for name, expected in cases:
    result = check_branch(name)
    ok = result.startswith(expected)
    if not ok:
        all_ok = False
    print(f"[{'OK' if ok else 'MISMATCH'}] {name:60s} => {result} (expected {expected})")

print()
assert all_ok, "SOME FAILURES"
print("ALL PASS" if all_ok else "SOME FAILURES")
