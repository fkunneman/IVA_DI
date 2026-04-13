#!/usr/bin/env python3
from random import random

# generate random timeslots

weeks = 20
# what is the chance the day will have a timeslot available?
day_available = 0.1
day_available_increase_per_day = 0.05

# what is the chance a single timeslot is available?
timeslot_available = 0.00001
# how much does this probability increase per day?
timeslot_available_increase_per_day = 0.02

for week in range(0, weeks):
    # flip bits for every available timeslot
    for day in range(0, 5):
        slot_availability = 0
        if random() < day_available:
          for slot in range(0, 48):
              if random() < timeslot_available:
                  slot_availability += 2**slot

        print(slot_availability.to_bytes(6).hex())
        timeslot_available += timeslot_available_increase_per_day
        day_available += day_available_increase_per_day
