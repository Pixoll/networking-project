# Networking Project

We assume this will be executed in a Unix system. Commands and bash scripts have only been tested on Ubuntu and Mint.

## Preparations

First and foremost, you must get all the required submodules.

```bash
git submodule update --init --recursive
```

Afterward, add execution permissions to the scripts needed to run the project.
```bash
chmod +x bin/run1
chmod +x bin/run2
chmod +x bin/generate-keys
chmod +x java/gradlew
```

Lastly, you create the encryption/signing keys for the different programs to work properly.

```bash
# usage: ./bin/generate-keys <key_pass>
./bin/generate-keys c286jm45...
```

This will create the following keys in the `.keys` directory:

- `sensor_private.pem` and `sensor_public.pem`: used for communication between C++ and Java
- `aes.key`: used for communication between Java and Python

### Important

> Ensure `sensor_private.pem` and `sensor_public.pem` are present in Machine 1, and `aes.key` is present in both Machine
> 1 and Machine 2.

## Machine 1 - Sensors and intermediate server

Run the `./bin/run1` script to do everything automatically, or follow the steps below.

```bash
# install dependencies, compile, and execute
./bin/run1 3 c286jm45... http://192.168.2.123:5000
```

### Dependencies

- CMake and Make
- Java Runtime and DevKit
- Gradle
- OpenSSL

```bash
sudo apt install build-essential default-jre default-jdk gradle libssl-dev openssl
```

### Compiling

- open62541 library

```bash
cd cpp/open62541
git submodule update --init --recursive
mkdir -p build
cd build
cmake ..
make
```

- C++

```bash
cd cpp
mkdir -p build
cd build
cmake ..
make
```

- Java

```bash
cd java
./gradlew shadowJar
```

### Executing

- Nodes

```bash
cd cpp/build
# usage: ./node <number_of_nodes>
./node 3
```

- Sensors

```bash
cd cpp/build
# usage: ./sensor <number_of_sensors> <key_pass>
./sensor 3 c286jm45...
```

- Intermediate server
```bash
cd java
# usage: java -jar build/libs/java-1.0.0-all.jar <number_of_sensors> <api_base_url>
java -jar build/libs/java-1.0.0-all.jar 3 http://192.168.2.123:5000
```

## Machine 2 - API, DB, and frontend

Run the `./bin/run2` script to do everything automatically, or follow the steps below.

```bash
# install dependencies, prepare, and execute
./bin/run2
```

### Dependencies

- Python 3 with virtual environment
- SQLite
- Node.js

```bash
sudo apt install python3 python3-venv sqlite3

# install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# install node
nvm install 20
nvm use 20
```

### Preparing

- Python

```bash
cd py
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- Svelte

```bash
cd js
npm i
npm run build
```

### Executing

- API

```bash
cd py
source .venv/bin/activate
python3 api.py
```

- Frontend

```bash
cd js
npm run preview
```
