import typing
import random


def gen_event() -> tuple:
    players = ["Alice", "Bob", "Charlie", "Dylan"]
    events = ["run", "eat", "sleep", "grab",
              "move", "climb", "swim", "release"]
    for i in range(1000):
        event = random.choice(events)
        player = random.choice(players)
        yield (player, event)


def print_events() -> None:
    print("=== Game Data Stream Processor ===")
    for i in range(1000):
        event = next(gen_event())
        print(f"Event {i}: Player {event[0]} did action {event[1]}")
    event_list = []
    print("Built list of 10 events: ", end="")
    for i in range(10):
        event = next(gen_event())
        event_list.append(event)
    print(event_list)
    for event in consume_event(event_list):
        print("Got event from list: ", event)
        print("Remains in list: ", event_list)


def consume_event(event_list: list) -> typing.Generator:
    while len(event_list) > 0:
        index = random.randint(0, len(event_list) - 1)
        yield event_list.pop(index)
