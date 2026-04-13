import { CommonModule } from '@angular/common';
import { Component, ElementRef, signal, ViewChild } from '@angular/core';

type SpeakState = 'ready' | 'recording' | 'waiting' | 'speaking';

@Component({
  selector: 'app-speak',
  imports: [CommonModule],
  templateUrl: './speak.html',
  styleUrl: './speak.scss',
})
export class Speak {
  state = signal<SpeakState>('ready');
  private mediaRecorder?: MediaRecorder;
  // recording is stored here
  private mediaChunks: Blob[] = [];
  private initialized = false;

  @ViewChild('audio', { static: false, read: ElementRef<HTMLAudioElement> })
  audioElement!: ElementRef<HTMLAudioElement>;

  constructor() {
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
              // TODO: send this data to a server
              const blob = new Blob(this.mediaChunks, { type: "audio/ogg; codecs=opus" });

              // pretend it takes some time
              setTimeout(() => {
                // TODO: here we just playback the recording
                this.state.set('speaking');
                const audioURL = window.URL.createObjectURL(blob);
                this.audioElement.nativeElement.src = audioURL;
                this.audioElement.nativeElement.play();
                this.audioElement.nativeElement.onended = (e) => {
                  this.state.set('ready');
                };
              }, 2500);
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
