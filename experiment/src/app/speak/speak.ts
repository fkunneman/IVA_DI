import { CommonModule } from '@angular/common';
import { Component, ElementRef, signal, ViewChild } from '@angular/core';
import { environment } from './../../environments/environment';
import { HttpClient, HttpHeaders } from '@angular/common/http';

const synth = window.speechSynthesis;

const SpeakRate = 0.5;
const SpeakPitch = 1;

type SpeakState = 'preflight' | 'ready' | 'recording' | 'waiting' | 'speaking';

@Component({
  selector: 'app-speak',
  imports: [CommonModule],
  templateUrl: './speak.html',
  styleUrl: './speak.scss',
})
export class Speak {
  state = signal<SpeakState>('preflight');

  // what did the speaker just say?
  speakerText = signal<string[]>([]);

  // what did the model respond?
  responseText = signal<string[]>([]);

  private mediaRecorder?: MediaRecorder;
  // recording is stored here
  private mediaChunks: Blob[] = [];
  private initialized = false;
  private agentId: string = '';

  @ViewChild('audio', { static: false, read: ElementRef<HTMLAudioElement> })
  audioElement!: ElementRef<HTMLAudioElement>;

  voice?: SpeechSynthesisVoice;

  constructor(private httpClient: HttpClient) {
    for (const voice of synth.getVoices()) {
      if (voice.lang === 'nl-NL') {
        this.voice = voice;
        return;
      }
    }
  }

  async start() {
    this.state.set('waiting');
    const { agentId, text } = await this.newSession();
    this.agentId = agentId;
    await this.say(text);
    this.state.set('ready');
  }

  private newSession() {
    const headers = new HttpHeaders({
      "Authorization": "Basic " + btoa(`${environment.apiUser}:${environment.apiPassword}`)
    });

    return new Promise<{ agentId: string, text: string }>((resolve) => {
      this.httpClient.post<{ agent_id: string, first_message: string }>(environment.startChainUrl, '', {
        headers: headers,
        responseType: 'json'
      }).subscribe(
        response => {
          resolve({
            agentId: response.agent_id,
            text: response.first_message
          });
        }
      );
    });
  }

  private say(text: string) {
    this.responseText.set(text.split(' '));
    return new Promise<void>((resolve) => {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = SpeakRate;
      utterance.pitch = SpeakPitch;
      if (this.voice) {
        utterance.voice = this.voice;
      }
      synth.speak(utterance);
      let polling = setInterval(() => {
        if (!synth.speaking) {
          clearInterval(polling);
          // done speaking
          resolve();
        }
      }, 5);
    });
  }

  private async process(text: string) {
    this.speakerText.set(
      text.split(' ')
    );

    // send to langchain
    let reply: string;
    try {
      reply = (await this.messageLangChain(text)).text;
    }
    catch (err) {
      console.error(err);
      this.state.set('speaking');
      this.responseText.set(`${err}`.split(' '));
      await this.say('Er is iets mis gegaan.');
      this.state.set('ready');
      return;
    }

    this.state.set('speaking');
    this.responseText.set(reply.split(' '));
    await this.say(reply);
    this.state.set('ready');
  }

  private messageLangChain(text: string) {
    const headers = new HttpHeaders({
      "Authorization": "Basic " + btoa(`${environment.apiUser}:${environment.apiPassword}`),
      "Content-Type": "application/x-www-form-urlencoded"
    });

    return new Promise<{ text: string }>((resolve, reject) => {
      this.httpClient.post<{ response: string }>(
        environment.messageChainUrl + this.agentId,
        `message=${text}`,
        {
          headers: headers,
          responseType: 'json'
        }).subscribe({
          next: response => {
            resolve({
              text: response.response
            });
          },
          error: (err) => {
            reject(err);
          }
        });
    });
  }

  async initAudio() {
    return new Promise<boolean>((resolve, reject) => {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices
          .getUserMedia(
            // constraints - only audio needed for this app
            {
              audio: true,
            },
          )

          // Success callback
          .then((stream) => {
            this.mediaRecorder = new MediaRecorder(stream);
            this.mediaRecorder.ondataavailable = (e) => {
              this.mediaChunks.push(e.data);
            };
            this.mediaRecorder.onstop = (e) => {
              if (this.state() != 'waiting') {
                return;
              }

              this.speakerText.set([]);

              // TODO: send this data to a server
              // const blob = new Blob(this.mediaChunks, { type: "audio/ogg; codecs=opus" });

              const headers = new HttpHeaders({
                "Authorization": "Basic " + btoa(`${environment.apiUser}:${environment.apiPassword}`)
              });

              const file = new File(this.mediaChunks, 'test.ogg');
              const formData = new FormData();
              formData.append('file', file);

              this.httpClient.post(environment.speechApiUrl, formData, {
                headers: headers,
                responseType: 'text'
              }).subscribe(
                response => {
                  this.process(response);
                }
              );

              // this.responseText.set('');

              // // pretend it takes some time
              // setTimeout(() => {
              //   // TODO: here we just playback the recording
              //   this.responseText.set('Dit is het antwoord.');
              //   this.state.set('speaking');
              //   // const audioURL = window.URL.createObjectURL(blob);
              //   // this.audioElement.nativeElement.src = audioURL;
              //   // this.audioElement.nativeElement.play();
              //   // this.audioElement.nativeElement.onended = (e) => {
              //   //   this.state.set('ready');
              //   // };
              // }, 2500);
            };

            resolve(true);
          })
          // Error callback
          .catch((err) => {
            reject(`The following getUserMedia error occurred: ${err}`);
          });
      } else {
        reject("getUserMedia not supported on your browser!");
      }
    });
  }

  async record() {
    if (!this.initialized) {
      try {
        this.initialized = await this.initAudio();
      }
      catch (error) {
        alert(error);
        return;
      }
    }
    this.state.set('recording');
    this.mediaChunks = [];
    this.mediaRecorder?.start();
  }

  cancel() {
    this.state.set('ready');
    this.mediaRecorder?.stop();
  }

  send() {
    this.state.set('waiting');
    this.mediaRecorder?.stop();
  }
}
