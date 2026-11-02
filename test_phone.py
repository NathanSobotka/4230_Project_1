# Automated tests for the telephone switching simulation (main.py).
# How to run:  pytest -v test_phone.py
# Sections: 1) setup/helpers  2) requirements tests RT01-RT21 (black box)
#           3) basis path tests (stubs)  4) state transition tests (stub)

import os
import subprocess
import sys

import pytest

import main

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN_PY = os.path.join(HERE, "main.py")

STANDARD = "Alice 11111\nBob 22222\nCarol 33333\nDave 44444\nErin 00555\n"

# commands that leave Alice, Bob and Carol in a 3 way call
THREE_WAY = [
    "alice offhook",
    "alice call bob",
    "bob offhook",
    "alice conference carol",
    "carol offhook",
]
# commands that leave Alice and Bob talking
TWO_WAY = ["alice offhook", "alice call bob", "bob offhook"]


# ---------------------------------------------------------------- setup ----


@pytest.fixture(autouse=True)
def clean_state():
    """Clear main's global phone tables before every test."""
    main.phones.clear()
    main.phone_order.clear()
    yield
    main.phones.clear()
    main.phone_order.clear()


@pytest.fixture
def phone_file(tmp_path):
    """Write the standard phone file and return its path."""
    path = tmp_path / "phones.txt"
    path.write_text(STANDARD)
    return str(path)


def run_file(path, commands, banner=False):
    """Run `python3 main.py <path>` with the commands (plus quit) on stdin.

    Returns stdout and stderr together. Unless banner=True the startup banner
    is removed, along with the "> " prompts, so only the load warnings and the
    command output are left.
    """
    result = subprocess.run(
        [sys.executable, MAIN_PY, path],
        input="\n".join(list(commands) + ["quit"]) + "\n",
        capture_output=True,
        text=True,
        timeout=10,
    )
    lines = (result.stdout + result.stderr).splitlines()
    if not banner:
        start = next((i for i, l in enumerate(lines)
                      if l.startswith("Telephone switching simulation")), None)
        end = next((i for i, l in enumerate(lines)
                    if "exit the simulation" in l), None)
        if start is not None and end is not None:
            lines = lines[:start] + lines[end + 1:]
    cleaned = []
    for line in lines:
        while line.startswith("> "):
            line = line[2:]
        if line.strip() and line.strip() != ">":
            cleaned.append(line)
    return "\n".join(cleaned) + "\n"


def run(file_contents, commands, banner=False):
    """Write file_contents to a temp phone file, then run_file on it."""
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "phones.txt")
        with open(path, "w") as f:
            f.write(file_contents)
        return run_file(path, commands, banner)


def status_line(out, name):
    """The status line for one phone (they start with '<number> - <Name>')."""
    for line in out.splitlines():
        if f" - {name}" in line and "STATUS" in line:
            return line
    raise AssertionError(f"no status line for {name} in:\n{out}")


# ------------------------------------------------- requirements tests -----


def test_RT01():
    """Req 1: standard file, 5 phones loaded and listed."""
    out = run(STANDARD, [], banner=True)
    assert "5 phones loaded" in out
    for entry in ["Alice (11111)", "Bob (22222)", "Carol (33333)",
                  "Dave (44444)", "Erin (00555)"]:
        assert entry in out


def test_RT02():
    """Req 1: 21 pairs in the file, only 20 loaded and a warning printed."""
    contents = "".join(f"P{chr(97 + i)} {10000 + i}\n" for i in range(21))
    out = run(contents, [], banner=True)
    assert "20 phones loaded" in out
    assert "Warning: more than 20 phones" in out
    assert "Pt (10019)" in out
    assert "Pu (10020)" not in out


def test_RT03():
    """Req 2: phone given by number, Erin (00555) hears dialtone."""
    out = run(STANDARD, ["00555 offhook", "status"])
    assert "Erin hears dialtone" in out
    assert "dialtone" in status_line(out, "Erin")


def test_RT04():
    """Req 2: line 'Bobby 222' is rejected with a bad number warning."""
    out = run("Alice 11111\nBobby 222\n", [], banner=True)
    assert "Warning: bad number in 'Bobby 222'" in out
    assert "Bobby (222)" not in out
    assert "1 phones loaded" in out


def test_RT05():
    """Req 3: a 13 letter name and the name B0b are both rejected."""
    out = run("Alice 11111\nAbcdefghijklm 12345\nB0b 22222\n", [], banner=True)
    assert "Warning: bad name in 'Abcdefghijklm 12345'" in out
    assert "Warning: bad name in 'B0b 22222'" in out
    assert "1 phones loaded" in out


def test_RT06():
    """Req 5: call by number, ringback/ringing, then both talking."""
    out = run(STANDARD, ["alice offhook", "alice call 22222", "22222 offhook"])
    assert "Alice hears dialtone" in out
    assert "Alice hears ringback" in out
    assert "Bob hears ringing" in out
    assert "Bob and Alice are talking" in out


def test_RT07():
    """Req 7: callee hangs up, caller hears silence at the end."""
    out = run(STANDARD, TWO_WAY + ["bob onhook"])
    assert "Alice hears silence" in out
    assert out.strip().splitlines()[-1] == "Alice hears silence"


def test_RT08():
    """Req 8: caller leaves a 3 way call, the other two keep talking."""
    out = run(STANDARD, THREE_WAY + ["alice onhook"])
    assert "Bob and Carol are talking" in out
    assert "Alice hears silence" in out


def test_RT09():
    """Req 9: transfer, Alice hears silence and Bob and Carol talk."""
    out = run(STANDARD, TWO_WAY + ["alice transfer carol", "carol offhook"])
    assert "Alice hears silence" in out
    assert "Carol and Bob are talking" in out


def test_RT10():
    """Req 10: calling a phone that is already in a call gives busy."""
    out = run(STANDARD, TWO_WAY + ["carol offhook", "carol call alice"])
    assert "Carol hears busy" in out


def test_RT11():
    """Req 11: calling a number that is not in the file gives denial."""
    out = run(STANDARD, ["alice offhook", "alice call zed"])
    assert "Alice hears denial" in out


def test_RT12():
    """Req 11: a 4th phone cannot join a 3 way call."""
    out = run(STANDARD, THREE_WAY + ["alice conference dave", "status"])
    assert "Alice hears denial" in out
    assert "Dave hears ringing" not in out
    assert "onhook idle" in status_line(out, "Dave")


def test_RT13():
    """Req 12: an onhook phone that tries to call hears silence."""
    out = run(STANDARD, ["alice call bob"])
    assert "Alice hears silence" in out
    assert "Bob hears ringing" not in out


def test_RT14():
    """Req 12: an onhook phone that conferences or transfers hears silence."""
    out = run(STANDARD, ["carol conference dave", "carol transfer dave"])
    assert out.count("Carol hears silence") == 2
    assert "denial" not in out
    assert "Dave hears ringing" not in out


def test_RT15():
    """Req 13: a second offhook on an offhook phone is ignored."""
    out = run(STANDARD, ["alice offhook", "alice offhook"])
    assert out.count("Alice hears dialtone") == 1


def test_RT16():
    """Req 14: status with no calls shows all 5 phones onhook idle."""
    out = run(STANDARD, ["status"])
    for name in ["Alice", "Bob", "Carol", "Dave", "Erin"]:
        assert "onhook idle" in status_line(out, name)


def test_RT17():
    """Req 14: in a 3 way call each phone lists the other two."""
    out = run(STANDARD, THREE_WAY + ["status"])
    names = ["Alice", "Bob", "Carol"]
    for name in names:
        line = status_line(out, name)
        assert "talking" in line
        for other in names:
            if other != name:
                assert other in line.split("Connected devices:")[1]


def test_RT18():
    """Req 1: a missing phone file gives a clear error and no traceback."""
    out = run_file("no_such_phone_file.txt", [])
    assert "no_such_phone_file.txt" in out
    assert "could not read phone file" in out
    assert "Traceback" not in out


def test_RT19():
    """Req 11: transfer from a 3 way call is denied and the call stays up."""
    out = run(STANDARD, THREE_WAY + ["alice transfer dave", "status"])
    assert "Alice hears denial" in out
    assert "Dave hears ringing" not in out
    for name in ["Alice", "Bob", "Carol"]:
        assert "talking" in status_line(out, name)


def test_RT20():
    """Req 9: held party hangs up mid-transfer, Alice keeps calling Carol."""
    out = run(STANDARD, TWO_WAY + ["alice transfer carol", "bob onhook",
                                   "carol offhook"])
    assert out.count("Alice hears ringback") == 3
    assert out.strip().splitlines()[-2:] == [
        "Alice hears ringback",
        "Carol and Alice are talking",
    ]


def test_RT21():
    """Req 11: transfer to an unknown phone is denied, Alice and Bob stay."""
    out = run(STANDARD, TWO_WAY + ["alice transfer zed", "status"])
    assert "Alice hears denial" in out
    assert "Bob (22222)" in status_line(out, "Alice")
    assert "Alice (11111)" in status_line(out, "Bob")
    assert "talking" in status_line(out, "Alice")
    assert "talking" in status_line(out, "Bob")


# ------------------------------------------- white box helpers (direct) ----


def make_phone(name, number, state=main.ONHOOK, connected=()):
    """Build a Phone in a chosen state and register it in main's tables.

    `connected` is a list of already-built Phone objects. The link is added
    on this phone only; build the other side yourself (see put_in_state).
    """
    phone = main.Phone(name, number)
    phone.state = state
    phone.connected = list(connected)
    main.phones[name] = phone
    main.phones[number] = phone
    main.phone_order.append(phone)
    return phone


def link(*pairs):
    """link((a, b), (a, c)) makes each pair list the other in connected."""
    for a, b in pairs:
        a.connected.append(b)
        b.connected.append(a)


def put_in_state(state):
    """Create Alice..Erin with Alice in `state` and her connections to match.

    Returns a dict of name -> Phone. Alice is always the phone under test.
    Bob is her call partner, Carol is the third phone (ringing in
    transferring/conferencing). Dave and Erin stay onhook idle.
    """
    p = {
        "Alice": make_phone("Alice", "11111"),
        "Bob": make_phone("Bob", "22222"),
        "Carol": make_phone("Carol", "33333"),
        "Dave": make_phone("Dave", "44444"),
        "Erin": make_phone("Erin", "00555"),
    }
    a, b, c = p["Alice"], p["Bob"], p["Carol"]
    a.state = state
    if state == main.RINGBACK:
        b.state = main.RINGING
        link((a, b))
    elif state == main.RINGING:
        b.state = main.RINGBACK
        link((a, b))
    elif state == main.TALKING:
        b.state = main.TALKING
        link((a, b))
    elif state in (main.TRANSFERRING, main.CONFERENCING):
        b.state = main.TALKING
        c.state = main.RINGING
        link((a, b), (a, c))
    # onhook idle, dialtone, silence, busy, denial: Alice has no connections
    return p


# ------------------------------------------- state transition tests -------
# Each row: (start state, event, expected next state, expected output)
#   start state: a main state constant, e.g. main.TALKING
#   event:       what Alice does, e.g. "offhook", "call Bob", "transfer Carol"
#   next state:  Alice's state afterwards
#   output:      text that must appear in the output ("" for no check)
# Example: (main.ONHOOK, "offhook", main.DIALTONE, "Alice hears dialtone")

STATE_ROWS = []


def test_ST01():
    """Idle -> offhook -> Dialtone."""
    out = run(STANDARD, ["alice offhook", "status"])

    assert "Alice\tSTATUS: dialtone" in out


def test_ST02():
    """Dialtone -> onhook -> Onhook."""
    out = run(STANDARD, ["alice offhook", "alice onhook"])
    assert "Alice hears dialtone" in out


def test_ST03():
    """Dialtone -> call -> Ringback."""
    out = run(STANDARD, ["alice offhook", "alice call bob", "status"])

    assert "Alice\tSTATUS: ringback" in out


def test_ST04():
    """Ringback -> other phone offhook -> Talking."""
    out = run(STANDARD, ["alice offhook", "alice call bob", "bob offhook"])
    assert "Bob and Alice are talking" in out


def test_ST05():
    """Ringback -> onhook -> Onhook."""
    out = run(STANDARD, ["alice offhook", "alice call bob", "alice onhook"])
    assert "Alice hears ringback" in out
    assert "Bob and Alice are talking" not in out


def test_ST06():
    """Onhook -> incoming call -> Ringing."""
    out = run(STANDARD, ["alice offhook", "alice call bob", "status"])

    assert "Bob\tSTATUS: ringing" in out


def test_ST07():
    """Ringing -> caller onhook -> Onhook."""
    out = run(STANDARD, ["alice offhook", "alice call bob", "alice onhook"])
    assert "Bob hears ringing" in out
    assert "Bob and Alice are talking" not in out


def test_ST08():
    """Ringing -> offhook -> Talking."""
    out = run(STANDARD, ["alice offhook", "alice call bob", "bob offhook"])
    assert "Bob and Alice are talking" in out


def test_ST09():
    """Talking -> onhook -> Onhook."""
    out = run(STANDARD, TWO_WAY + ["alice onhook", "status"])

    assert "Alice\tSTATUS: onhook idle" in out


def test_ST10():
    """Talking -> other phone onhook -> Silence."""
    out = run(STANDARD, TWO_WAY + ["bob onhook", "status"])

    assert "Alice\tSTATUS: silence" in out


def test_ST11():
    """Silence -> onhook -> Onhook."""
    out = run(STANDARD, TWO_WAY + ["bob onhook", "alice onhook", "status"])

    assert "Alice\tSTATUS: onhook idle" in out


def test_ST12():
    """Talking -> transfer -> Transferring."""
    out = run(STANDARD, TWO_WAY + ["alice transfer carol", "status"])

    assert "Alice\tSTATUS: transferring" in out


def test_ST13():
    """Transferring -> onhook -> Onhook."""
    out = run(
        STANDARD,
        TWO_WAY + ["alice transfer carol", "alice onhook", "status"]
    )

    assert "Alice\tSTATUS: onhook idle" in out


def test_ST14():
    """Talking -> conference -> Conferencing."""
    out = run(STANDARD, TWO_WAY + ["alice conference carol", "status"])

    assert "Alice\tSTATUS: conferencing" in out


def test_ST15():
    """Conferencing -> other phone offhook -> Talking."""
    out = run(STANDARD, TWO_WAY + ["alice conference carol", "carol offhook"])
    assert "Carol and Bob and Alice are talking" in out


def test_ST16():
    """Conferencing -> onhook -> Onhook."""
    out = run(STANDARD, THREE_WAY + ["alice onhook"])
    assert "Bob and Carol are talking" in out
    assert "Alice hears silence" in out


@pytest.mark.parametrize("start, event, expected_state, expected_output",
                         STATE_ROWS)
def test_state_transition(start, event, expected_state, expected_output,
                          capsys):
    phones = put_in_state(start)
    main.parse_command(f"Alice {event}")
    out = capsys.readouterr().out
    assert phones["Alice"].state == expected_state
    assert expected_output in out
