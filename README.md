# Solark-influx

Imports data from Sol-Ark to InfluxDB v2.

## Requirements

- Sol-Ark credentials (email/password)
- InfluxDB v2 instance with write credentials to a bucket
- Docker or Python 3.11+

## Running the app

The app reads settings from `template.config.toml`, then `config.toml` (if it exists), then environment variables.
See `template.config.toml` for details.

### From the command line

```bash
git clone git@github.com:vdbg/solark-influx.git 
cd solark-influx
cp template.config.toml config.toml
# follow instruction to edit
nano config.toml
pip3 install -r requirements.txt
python3 ./main.py
```


### With Docker (no config file)

Inspect `template.config.toml` for the settings to override. 

For example:

```sh
sudo docker run \
  -d \
  --name solark-influx \
  --pull=always \
  --restart=always \
  -e SOLARK_INFLUX_SOLARK_USERNAME=user \
  -e SOLARK_INFLUX_SOLARK_PASSWORD=password \
  -e SOLARK_INFLUX_INFLUX_TOKEN=token \
  -e SOLARK_INFLUX_INFLUX_ORG=my_org \
  vdbg/solark-influx:latest
```

Alternatively, you can use a compose.yaml file, optionally with a .env file.

### With Docker (using config file)

1. `sudo docker run --name solark-influx -v config.toml:/app/config.toml vdbg/solark-influx:latest`
2. `sudo docker cp solark-influx:/app/template.config.toml config.toml`
3. Edit `config.toml`
4. `sudo docker start solark-influx -i`
5. `sudo docker container rm solark-influx`
6. `sudo docker run -d --name solark-influx -v /path_to_your/config.toml:/app/config.toml --pull=always --restart=always vdbg/solark-influx:latest`

