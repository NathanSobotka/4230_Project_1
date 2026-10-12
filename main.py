# import regex to enforce phone and name formats A-Za-z
import re
# import sys to read command line arguments
import sys

'''How to run the program:
Command line: python3 main.py <phone file>'''

# Constants for phone states
ONHOOK = "onhook idle"
DIALTONE = "dialtone"
RINGBACK = "ringback"
RINGING = "ringing"
TALKING = "talking"
SILENCE = "silence"
BUSY = "busy"

# Maximum number of phones allowed
MAX_PHONES = 20


class Phone:
    def __init__(self, name, number):
        self.name = name
        self.number = number  # string so a leading zero survives
        self.state = ONHOOK
        self.connected = []


phones = {}  # every phone, under both its name and its number
phone_order = []  # file order, for status


def load_file(path):
    count = 0
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if count >= MAX_PHONES:
                print(f"Warning: more than {MAX_PHONES} phones, skipping '{line}'")
                continue
            parts = line.split()
            if len(parts) != 2:
                print(f"Warning: bad line '{line}'")
                continue
            name, number = parts
            if not re.fullmatch(r"[A-Za-z]{1,12}", name):
                print(f"Warning: bad name in '{line}'")
                continue
            if not re.fullmatch(r"[0-9]{5}", number):
                print(f"Warning: bad number in '{line}'")
                continue
            if name in phones or number in phones:
                print(f"Warning: duplicate in '{line}'")
                continue
            name = name.title()  # always store names as Alice, Bob, etc.
            if name in phones:
                print(f"Warning: duplicate in '{line}'")
                continue
            phone = Phone(name, number)
            phones[name] = phone
            phones[number] = phone
            phone_order.append(phone)
            count += 1


def offhook(phone):
    if phone.state == ONHOOK:
        phone.state = DIALTONE
        print(f"{phone.name} hears dialtone")
    elif phone.state == RINGING:
        phone.state = TALKING
    # already offhook: ignore


def onhook(phone):
    pass  # TODO


def status():
    pass  # TODO


def call(phone, target):
    pass  # TODO


def conference(phone, target):
    pass  # TODO


def transfer(phone, target):
    pass  # TODO


def parse_command(line):
    parts = line.split()
    if len(parts) == 1:
        if parts[0] == "status":
            status()
        else:
            print(f"Error: unknown command '{line}'")
    elif len(parts) == 2:
        who, action = parts
        who = who.title()  # bob, BOB, BOb all become Bob
        if who not in phones:
            print(f"Error: unknown phone '{who}'")
        elif action == "offhook":
            offhook(phones[who])
        elif action == "onhook":
            onhook(phones[who])
        else:
            print(f"Error: unknown command '{line}'")
    elif len(parts) == 3:
        who, action, other = parts
        who = who.title()
        other = other.title()
        if who not in phones:
            print(f"Error: unknown phone '{who}'")
        elif action == "call":
            call(phones[who], other)
        elif action == "conference":
            conference(phones[who], other)
        elif action == "transfer":
            transfer(phones[who], other)
        else:
            print(f"Error: unknown command '{line}'")
    else:
        print(f"Error: unknown command '{line}'")


def main():
    # Base case: check for correct number of command line arguments
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <phone file>. You must provide a phone file as a command line argument.")
        return
    load_file(sys.argv[1])

    # Print the prompt and the list of phones loaded from the file
    print(f"\nTelephone switching simulation: {len(phone_order)} phones loaded.")
    # Take phones and names from the phone_order list and print them in a string format
    print("Phones: " + ", ".join(f"{p.name} ({p.number})" for p in phone_order))
    print("\nCommands (a phone can be given by name or number):")
    print("  <Name or Phone> offhook              pick up the phone")
    print("  <Name or Phone> onhook               hang up the phone")
    print("  <Name or Phone> call <Name or Phone>         call another phone (needs dialtone)")
    print("  <Name or Phone> conference <Name or Phone>   add a third phone to a call")
    print("  <Name or Phone> transfer <Name or Phone>     transfer a call to another phone")
    print("  status                       show every phone's state")
    print("  quit                         exit the simulation\n")

    # Start the command loop
    while True:
        try:
            line = input("> ").strip()
        except EOFError:
            print('\n Exiting simulation. Goodbye!')
            break
        if line == "quit":
            break
        if line:
            parse_command(line)


if __name__ == "__main__":
    main()
