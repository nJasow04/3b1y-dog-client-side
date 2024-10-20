# CalHacks 13 monorepo

> The spot for our code for running spotter on [Spot](https://bostondynamics.com/products/spot/)

**backend**: web server for multilingual, multimodal AI processing
- REST API written in Python using Flask
- [Poetry](https://python-poetry.org/) for dependency management
- [Google Cloud Services](https://cloud.google.com/?hl=en)
- [Gemini](https://gemini.google.com/)
- [Groq](https://groq.ai/)

**Root folder**: frontend that enables easy robot control and shows the robot's camera and data feed
- serves data and object recognition from AI backend
- makes requests to robot control backend based on keyboard and mouse inputs
- [Bun](https://bun.sh/)
- [React](https://react.dev/)
- [shadcn-ui](https://ui.shadcn.com/) components

**robot-control-server**: web server that enables remote control of the robot
- REST API/gRPC service written in Python using Flask
- Boston Dynamics SDK

----

## Press

- Demo
  - https://devpost.com/software/robot-z6y2gp

----

## Running the stack:

First, clone this repo. If you don't have access to a Spot, you can still demo the entire frontend and AI part of the app locally, as long as you provide your Groq and GCP Client Json as an environment variables.

### backend
1. install Poetry
2. `poetry install`
3. `poetry run dev` to start the backend

### frontend
1. npm i
2. npm run dev

### robot server
1. connect to Spot's wifi network
2. run `python3 python/examples/wasd_server/app.py` and replace the hostname `192.168.80.3` with your Spot's IP
3. enter the `admin` username & password, or the equivalent credentials for your Spot
4. send requests to control endpoints manually or via the frontend
