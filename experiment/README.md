# Experiment

The system consists of three parts:

1. A mockup appointment web app
2. A proxy based on `mitmproxy`, which proxies a site and can be configured to reroute to the mockup appointment when needed
3. A web app for recording speech, sending it to a backend for processing, and receiving a spoken reply

Both web apps are exposed from the same container app, using different routes.

## Proxy

To mock and modify an actual site [`mitmproxy`](https://www.mitmproxy.org/) is used. You connect the browser to this proxy, and that proxy will then connect to this server. It will request the actual server and intercept and modify requests if needed.

Steps:

1. Install `mitmproxy`
2. Setup to use this proxy from your browser. It's important only your browser uses this proxy, as this application itself needs to be able to reach the actual server!
3. `mitmproxy -s proxy.py` (add `-p` to specify a port)

To override any request create an `proxy-override/override.tsv`-file and specify the domain, path pattern, mime type and location of the override. The override file is expected in a folder named domain within the proxy-override folder. E.g. if you want to override `uu.nl/example.html` place this file in `proxy-store/uu.nl/example.html` and specify `example.html` in the `override.csv`.

To create this file, you can use the copies of the responses stored in `proxy-store`. This is particularly useful if these responses cannot be directly downloaded from the browser, because it is being rewritten by for example [wombat](https://github.com/webrecorder/wombat).

## Development server

For the experiment it is assumed an override has been made of the relevant page which then points to this application. Once that has been setup the local development server can be run.

To start a local development server, run:

```bash
ng serve
```

Once the server is running, open your browser and navigate to `http://localhost:4200/`. The application will automatically reload whenever you modify any of the source files.

It will by default go to the appointment mockup. The recording app can be found under `http://localhost:4200/speak`. To access it from your mobile phone, first find out your local IP address (e.g. using `ifconfig`). For example 192.168.1.123

Then run:

```bash
ng serve --host 192.168.1.123
```

Go to http://192.168.1.123:4200 (replace 192.168.1.123 with your actual IP address) from your mobile phone. Make sure this computer and your phone are on the same (wifi) network.

TODO: this doesn't work because the browser requires [a secure context](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia) which means you also have to enable https.

## Code scaffolding

Angular CLI includes powerful code scaffolding tools. To generate a new component, run:

```bash
ng generate component component-name
```

For a complete list of available schematics (such as `components`, `directives`, or `pipes`), run:

```bash
ng generate --help
```

## Building

To build the project run:

```bash
ng build
```

This will compile your project and store the build artifacts in the `dist/` directory. By default, the production build optimizes your application for performance and speed.

For deployment in a folder as a static file:

```bash
ng build --base-href=/iva-di/
```

Copy the contents of the `dist/experiment/browser` folder to the server. Create a subfolder `speak` and place a copy of `index.html` there (or configure the server to rewrite calls to use `index.html`).

## Running unit tests

To execute unit tests with the [Vitest](https://vitest.dev/) test runner, use the following command:

```bash
ng test
```

## Additional Resources

For more information on using the Angular CLI, including detailed command references, visit the [Angular CLI Overview and Command Reference](https://angular.dev/tools/cli) page.
