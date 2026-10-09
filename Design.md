# CS 4230 Project 1: Telephone Switching Simulation (Design)

## Data

- Phone: name, number (string), state, list of connected phones
- One dictionary holds every phone under both its name and its number, so one lookup works for either
- Seven states: onhook idle, dialtone, ringback, ringing, talking, silence, busy
- Phone numbers are stored as strings so a leading zero survives ("01234" stays "01234")

## What each state hears

| State | Hears |
|---|---|
| onhook idle | nothing |
| dialtone | dialtone |
| ringback (caller waiting) | ringback |
| ringing (callee being rung, still onhook) | ringing |
| talking | "X and Y are talking" (built from the list, works for 2 or 3 phones) |
| silence (offhook, nobody on the line) | silence |
| busy | busy |

## Loading the file

- Each line is one name and one number
- Name: a single word, 1 to 12 letters (A-Z, a-z)
- Number: exactly 5 digits, kept as a string
- Skip bad lines, duplicates, and anything past 20 pairs, and print a warning

## Parsing

Split the line on spaces.

- 1 piece: must be "status"
- 2 pieces: phone + onhook or offhook
- 3 pieces: phone + call, transfer, or conference + another phone
- Unknown first word or wrong shape: print an error and keep running (never crash)

## Rules per command

**Offhook**
- From onhook idle: go to dialtone
- From ringing: go to talking (the caller is already in the list)
- Already offhook: ignore (print nothing)

**Call** (valid only from dialtone)
- Target not in the dictionary: caller hears denial
- Target not onhook idle: caller goes to busy, no lists change
- Otherwise: caller goes to ringback, target goes to ringing, each goes into the other's list

**Conference** (valid only when talking with exactly one other phone, otherwise denial)
- Same target checks as a call
- A goes to ringback, C goes to ringing, A and C add each other
- When C picks up, B and C add each other and all three are talking

**Transfer** (same start as conference)
- When C picks up: A's list empties and A goes to silence, B swaps A for C, C gets B

**Onhook**
- From any offhook state: go to onhook idle, empty own list, remove self from everyone else's list
- Then fix the others: a talking phone with an empty list goes to silence, a ringing phone with an empty list goes back to onhook idle
- Onhook phone told to go onhook again: silence, nothing changes

**Anything else from an onhook idle phone:** silence, nothing changes

**Denial** is output only. It never changes state or lists.

## Status

One line per phone in file order: the name plus the state. Talking phones also show who they are talking to.

```
Alice: talking to Bob
Bob: talking to Alice
Carol: onhook
```

## Walkthroughs to test against

1. Normal call: offhook, call, answer, onhook. Check lists at each step.
2. Conference: A and B talking, A conferences C, C answers, then B hangs up. A and C stay talking.
3. Transfer: A and B talking, A transfers to C, C answers. A silence, B and C talking.
4. Busy: A and B talking, C offhook, C calls A. C hears busy, A and B unchanged.
5. Denial: call a number not in the file, and a 4th phone into a 3 way call.
6. Caller hangs up while the callee is still ringing. Callee returns to onhook idle.
7. Onhook phone sent a call command: silence.
8. Offhook twice: second one ignored.
