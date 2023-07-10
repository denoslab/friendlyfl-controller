# FriendlyFL Routing Server

A federated learning (FL) system that is friendly to users with diverse backgrounds,
for instance, in healthcare. This repo is the Routing Server (RS) component.

## Overview
The project architecture diagram is shown below.

![Figure 1. Project architecture overview.
](docs/images/friendlyfl-arch.png)

### Sites

A **Site** is a local environment running either local training or model aggregation for FL.
A site registering to the Routing Server (RS) will update its state on RS.
A site can create a project and become the coordinator of the project.
The model aggregation will be done at the site.
Other sites can join the same project and become participants.

### Controllers

A **Controller** will be installed on every site. With the Controller running,
a Site can act as either a **Coordinator** or a **Participant**. 

#### Coordinators

As a Coordinator, a Site can create a Project for FL and let other Sites join the Project.
As a Participant, a Site can join a Project created by a Coordinator. 

#### Participants

The Controller will provide a web portal for a local user to manage and inspect the FL process.
For Sites to communicate with each other, a Routing Server (RS) is required to forward messages and maintain projects.
RS does not have a web portal by itself.

### Projects, Tasks, and Runs

A Project defines one or multiple FL **Tasks** with one Coordinator and multiple Participants.
A Project can have an ordered list of predefined Tasks. Each Task will allow its parameters to be customized.
A Project can have multiple **Runs** to allow repeated training over time. 

A Coordinator creates and controls the lifecycle of the Project. It can start a Run of the Project.
It can also stop the entire Run. The coordinator can view the status and logs of all Participants.

Once a Project is created, other Sites can join as Participants.
In comparison, a Participant cannot kick-start the participating project.
It can only passively work under defined processes in a Project.
A Participant can only view the logs and progress of itself without seeing other Participants.

A Project can have multiple Runs for repeated learning processes. A Run has its states.
Key events will move the state of a Run.

Commands will be initiated by the coordinator and broadcast to all participants.
Once started, progress will be sent back to the coordinator periodically.
RS will exchange local model updates and global model updates.

### Routing Server (RS)

A **Routing Server (RS)** has two responsibilities:

Providing a persistent layer for administrative data to facilitate smooth FL processes.
RS maintains global records of users, sites, projects, and runs.

Forwarding messages between participants and coordinators in a project.

Note that RS does not do model aggregation. Coordinator does.
Currently, Sites exchange information with RS through polling.
Message payloads can have end-to-end encryption. RS will not be able to read the message payloads.
Private key exchanges between sites will be done securely.

## Developers
### Environment

#### Mac

##### Prerequisites

###### brew
We are going to use [brew](https://brew.sh/) to install some tools. If you don't have brew installed on your Mac, run the following command:
```shell
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

###### Pyenv

We would suggest to use [pyenv](https://github.com/pyenv/pyenv) to manage and switch multiple versions of Python.
To install follow steps below.
```shell
brew update
brew install pyenv
```
If this didn't work for you try these [fixes](https://github.com/pyenv/pyenv#homebrew-in-macos).

To test if this was installed correctly try running the following in your terminal:
```shell
pyenv versions
```

We are going to be using Python version 3.10.10, so let's get that installed.
```shell
pyenv install 3.10.10
```

###### Poetry
We are going to use [poetry](https://python-poetry.org/) to manage dependencies. 

Run the following command in your terminal to install poetry:
```shell
curl -sSL https://install.python-poetry.org | python3 -
```

#### Windows
Todo
#### Linux
Todo


### Development

#### With Docker
##### Build docker image
```shell
docker build -t friendlyfl-router:latest .
```

##### Start
```shell
docker run -it -p 8000:8000 docker.io/library/friendlyfl-router:latest
```

#### Without Docker

##### Create a virtual environment
```shell
python3 -m venv venv
source venv/bin/activate
```

##### Install dependencies
```shell
poetry install
```

##### Database Migration
```shell
python3 manage.py migrate
```

##### Start Development Server
```shell
python3 manage.py runserver
```

##### De-active virtual environment
Type `deactivate` in your terminal

#### Code Format
Run the following command to format python code in friendlyfl-router directory
```shell
autopep8 --exclude='*/migrations/*' --in-place --recursive ./friendlyfl/
```
