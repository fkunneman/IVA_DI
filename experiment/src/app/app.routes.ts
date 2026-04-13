import { Routes } from '@angular/router';
import { Appointment } from './appointment/appointment';
import { Speak } from './speak/speak';

export const routes: Routes = [{
  path: '',
  component: Appointment
}, {
  path: 'speak',
  component: Speak
}];
