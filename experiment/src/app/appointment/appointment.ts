import { CommonModule } from '@angular/common';
import { Component, effect, signal } from '@angular/core';
import { email, form, FormField, readonly, required } from '@angular/forms/signals';
import {
  NgbAccordionDirective,
  NgbAccordionItem,
  NgbAccordionHeader,
  NgbAccordionToggle,
  NgbAccordionBody,
  NgbAccordionCollapse,
} from '@ng-bootstrap/ng-bootstrap/accordion';

// always use the same pattern for available time slots
// only go through week days, each day has time slots
// from 9:00 to 17:00
// time slots are 10 minutes,
// this means there are 48 slots for each day (i.e. 48 bits)
// 48 bits -> 6 bytes -> 12 hexadecimals per day
// use timeslots.py to generate this
const timeslotsString = '00000000000000000000000000000020000000000000000044080100000400000000000004100004000000000000000001000014628000222024072000000000000004800032c80f89634199063481a54581ac8020422010056000000000000011203668024b110c20e00340203f54a93186c0654bf818009d1258f3283518f32842140f1a083209e3f4266f0b525173063da7e13413f5ac105bd98e0b5e99d473a98c755fbc177fe39ecd134ab83d0ff3d3bc95879ed7da36975cf8d3ca8efdecfbfa1f3fe7ef7dffd4bc4b97efa7d4533978b7bff7c5a3f87d783ddedf78f5bce75bf33dffebffffffecffc9fffdf7bfdffffa9fdd2ffdff6b7bafff6ffbfefaef5feffffcfbfffff6ff7ebffffffffffbfffff3fbfdffffdef7fffffffffdffbfffffb7f7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff';
const monthNames: { [month: number]: string } = {
  0: 'januari',
  1: 'februari',
  2: 'maart',
  3: 'april',
  4: 'mei',
  5: 'juni',
  6: 'juli',
  7: 'augustus',
  8: 'september',
  9: 'oktober',
  10: 'november',
  11: 'december'
};

const dayNames: { [day: number]: string } = {
  0: 'maandag',
  1: 'dinsdag',
  2: 'woensdag',
  3: 'donderdag',
  4: 'vrijdag',
  5: 'zaterdag',
  6: 'zondag',
}

interface AppointmentData {
  persons: number;
  location: string;
  showMonth: number;
  month: number;
  dayNumber: string;
  dateString: string;
  slot: string;
  lastname: string;
  firstname: string;
  birthday: string;
  email: string;
  phone: string;
  searchProduct: string;
  searchLocation: string;
}

interface Location { name: string, location: string };

interface Step { number: number, title: string, subtitle?: string };

interface DayTimeSlots {
  dayOfWeek: string,
  /*
   * day of the month or null if it doesn't exist
   * weeks should be padded to always include Monday
   * till Sunday; number is padded with '0' to 2 digits
   */
  number: string | null,
  timeslots: string[]
};

interface MonthTimeSlots {
  index: number,

  year: number,
  month: number,
  /**
   * title e.g. mei 2026
   */
  title: string,
  /**
   * if it's Monday it's 0
   */
  firstDayOfMonth: number,
  /**
   * days split over weeks, starting on Monday
   */
  weeks: DayTimeSlots[][]
};

interface TimeSlots {
  // months
  months: MonthTimeSlots[]
};

@Component({
  selector: 'app-appointment',
  imports: [
    CommonModule,
    FormField,
    NgbAccordionDirective,
    NgbAccordionItem,
    NgbAccordionHeader,
    NgbAccordionToggle,
    NgbAccordionBody,
    NgbAccordionCollapse,
  ],
  templateUrl: './appointment.html',
  styleUrl: './appointment.scss',
})
export class Appointment {
  loadingMonths = true;
  loadingSlots = true;
  loadingConfirmation = false;
  confirmed = false;

  searchProductResult = '';
  time = signal('');

  steps = signal<Step[]>([
    {
      number: 1,
      title: 'Kies een product',
      subtitle: 'Paspoort aanvragen'
    },
    {
      number: 2,
      title: 'Kies een locatie',
    },
    {
      number: 3,
      title: 'Kies een datum en tijd'
    },
    {
      number: 4,
      title: 'Uw gegevens'
    }]);

  currentStep = 1;

  locations: Location[] = [{
    name: 'Centrum',
    location: 'Amstel 1'
  }, {
    name: 'West',
    location: 'Bos en Lommerplein 250'
  }, {
    name: 'Zuid',
    location: 'President Kennedylaan 923'
  }, {
    name: 'Oost',
    location: 'Oranje-Vrijstaatplein 2'
  }, {
    name: 'Noord',
    location: 'Buikslotermeerplein 2000'
  }];

  matchedLocations = [...this.locations];

  lessPeople() {
    this.setPeople(x => x - 1);
  }
  moarPeople() {
    this.setPeople(x => x + 1);
  }

  availableTimeslots: TimeSlots;
  availableDayTimeslots: DayTimeSlots | undefined;

  private setPeople(change: (current: number) => number) {
    let newValue = change(this.appointmentForm.persons().value());
    if (newValue < 0) {
      newValue = 0;
    }
    this.appointmentForm.persons().value.set(newValue);
  }

  show(step: number) {
    this.currentStep = step;
  }

  appointmentModel = signal<AppointmentData>({
    persons: 0,
    location: '',
    showMonth: (new Date()).getMonth(),
    month: (new Date()).getMonth(),
    dayNumber: '',
    dateString: '',
    slot: '',
    lastname: '',
    firstname: '',
    birthday: '',
    email: '',
    phone: '',
    searchProduct: '',
    searchLocation: ''
  });

  appointmentForm = form(this.appointmentModel, (schemaPath) => {
    readonly(schemaPath.persons);
    required(schemaPath.lastname);
    required(schemaPath.firstname);
    required(schemaPath.birthday);
    email(schemaPath.email);
    required(schemaPath.email);
  });

  currentMonth: number;

  private generateEmptyMonth(index: number, year: number, month: number): MonthTimeSlots {
    const daySlots: DayTimeSlots[] = [];

    // get the first day of the month
    var day = new Date();
    day.setFullYear(year);
    day.setMonth(month);
    day.setDate(1);

    // weeks start from a Monday, pad the first week
    const initialOffset = (day.getDay() - 1) % 7;

    for (let i = 0; i < initialOffset; i++) {
      daySlots.push({
        number: null,
        timeslots: [],
        dayOfWeek: ''
      });
    }

    while (day.getMonth() === month) {
      daySlots.push({
        number: `${day.getDate()}`.padStart(2, '0'),
        timeslots: [],
        dayOfWeek: dayNames[(day.getDay() - 1) % 7]
      });
      day.setDate(day.getDate() + 1);
    }

    // pad to end the week
    while (daySlots.length % 7 !== 0) {
      daySlots.push({
        number: null,
        timeslots: [],
        dayOfWeek: ''
      });
    }

    const weeks: DayTimeSlots[][] = [];
    for (let i = 0; i < daySlots.length; i += 7) {
      weeks.push(daySlots.slice(i, i + 7));
    }

    const monthName = monthNames[month] || '';

    return {
      index,
      year,
      month,
      firstDayOfMonth: initialOffset,
      title: `${monthName} ${year}`,
      weeks
    }
  }

  private setTimeslots() {
    const currentDate = new Date();
    let currentYear = currentDate.getFullYear();
    let currentMonth = currentDate.getMonth();
    let timeslots: TimeSlots = {
      months: []
    };

    for (let i = 0; i < 6; i++) {
      timeslots.months.push(this.generateEmptyMonth(i, currentYear, currentMonth));
      currentMonth += 1;
      if (currentMonth > 11) {
        currentMonth = 0;
        currentYear++;
      }
    }

    let currentWeek = Math.floor((currentDate.getDate() + timeslots.months[0].firstDayOfMonth) / 7);
    let currentWeekday = (timeslots.months[0].firstDayOfMonth + currentDate.getDate() - 1) % 7;

    // reset month
    currentMonth = currentDate.getMonth();

    let monthOffset = 0;
    let selectFirst = true;
    // skip today and weekends
    for (let dayTimeslots of this.getNextTimeslots()) {
      do {
        currentDate.setDate(currentDate.getDate() + 1);

        if (currentMonth !== currentDate.getMonth()) {
          // next month
          monthOffset++;
          currentMonth = currentDate.getMonth();
          currentWeek = 0;

          currentWeekday = timeslots.months[monthOffset].firstDayOfMonth;
        } else {
          currentWeekday++;
          if (currentWeekday > 6) {
            currentWeekday = 0;
            currentWeek++;
          }
        }
      }
      while (currentDate.getDay() === 0 || currentDate.getDay() === 6);

      timeslots.months[monthOffset].weeks[currentWeek][currentWeekday].timeslots = dayTimeslots;
      if (dayTimeslots.length && selectFirst) {
        this.selectDay(timeslots.months[monthOffset], timeslots.months[monthOffset].weeks[currentWeek][currentWeekday]);
        selectFirst = false;
      }
    }
    return timeslots;
  }

  selectDay(month: MonthTimeSlots, day: DayTimeSlots) {
    this.appointmentForm.month().value.set(month.month);
    this.appointmentForm.dayNumber().value.set(<string>day.number);
    this.appointmentForm.dateString().value.set(`${day.dayOfWeek}, ${day.number} ${month.title}`);
    this.appointmentForm.slot().value.set('');

    this.availableDayTimeslots = day;
    this.loadingSlots = true;
    setTimeout(() => {
      this.loadingSlots = false;
    }, 500);
  }

  selectTimeslot(slot: string) {
    this.loadingSlots = true;
    setTimeout(() => {
      this.show(4);
      this.appointmentForm.slot().value.set(slot);
      this.loadingSlots = false;
    }, 500);
  }

  /**
   * Gets the timeslots for the next day
   */
  *getNextTimeslots() {
    for (let i = 0; i < timeslotsString.length; i += 12) {
      const dayAvailability = timeslotsString.substring(i, i + 12);
      // get a 1/0 for every timeslot
      const dayAvailabilityFlags = parseInt(dayAvailability, 16).toString(2).padStart(48, '0');

      let timeslot = new Date();
      timeslot.setHours(9);
      timeslot.setMinutes(0);

      let timeslots: string[] = [];

      for (let flag of dayAvailabilityFlags) {
        if (flag == '1') {
          const hours = `${timeslot.getHours()}`.padStart(2, '0');
          const minutes = `${timeslot.getMinutes()}`.padStart(2, '0');
          timeslots.push(`${hours}:${minutes}`)
        }
        timeslot.setMinutes(timeslot.getMinutes() + 10);
      }

      yield timeslots;
    }
  }

  showMonth(diff: number) {
    this.appointmentForm.showMonth().value.set(this.appointmentForm.showMonth().value() + diff);
  }

  erase() {
    if (confirm('Weet je zeker dat je opnieuw wilt beginnen?')) {
      window.location.href = window.location.href;
    }
  }

  confirm() {
    this.loadingConfirmation = true;
    setTimeout(() => {
      this.confirmed = true;
      window.scrollTo(0, 0)
    }, 1000);
  }

  constructor() {
    this.currentMonth = (new Date()).getMonth();
    this.availableTimeslots = this.setTimeslots();
    setInterval(() => {
      var now = new Date();

      this.time.set(`${now.getFullYear()}-${now.getMonth() + 1}-${now.getDate()} ${now.toTimeString().split(' ')[0]}`)
    }, 1);

    // search locations
    effect(() => {
      const searchText = this.appointmentForm.searchLocation().value().toLocaleLowerCase();
      if (!searchText.trim()) {
        this.matchedLocations = [...this.locations];
      } else {
        this.matchedLocations = this.locations.filter(
          loc => loc.name.toLowerCase().indexOf(searchText) >= 0 ||
            loc.location.toLowerCase().indexOf(searchText) >= 0)
      }
    });

    // update persons subtitle
    effect(() => {
      const persons = this.appointmentForm.persons().value();
      const steps = this.steps();
      steps[0].subtitle = 'Paspoort aanvragen';
      if (persons == 1) {
        steps[0].subtitle += ' (1 Persoon)'
      } else if (persons > 0) {
        steps[0].subtitle += ` (${persons} Personen)`
      }
      this.steps.set(steps);
    });

    // update location subtitle
    effect(() => {
      const locationName = this.appointmentForm.location().value();
      const steps = this.steps();
      const location: Location | undefined = this.locations.find(l => l.name == locationName);
      if (location) {
        const updatedSubtitle = location.name + ', ' + location.location;
        if (steps[1].subtitle !== updatedSubtitle) {
          // move to the next step
          this.show(3);
          steps[1].subtitle = updatedSubtitle;
          this.steps.set(steps);
          this.loadingMonths = true;
          setTimeout(() => {
            this.loadingMonths = false;
          }, 1800);
        }
      }
    });

    // update date time
    effect(() => {
      const slot = this.appointmentForm.slot().value();
      const steps = this.steps();
      const timeString = slot ? `${this.appointmentForm.dateString().value()} ${slot}`.trim() : '';
      if (steps[2].subtitle !== timeString) {
        steps[2].subtitle = timeString;
        this.steps.set(steps);
      }
    });
  }
}
