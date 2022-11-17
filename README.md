# Omada Python Client

A Python client for Omada 5.x+.

After seeing that the [Omada client from ghaberek](https://github.com/ghaberek/omada-api) is longer being maintained, I decided to build this client for the primary goal to provide an Omada integration in [Home Assistant](https://www.home-assistant.io/).

I'm open to accepting contributions. If there's an API that you need that is not implemented, please create an issue.

This client has both blocking and async APIs.

## Example using Blocking API

```python
import requests

from omada import Omada

session = requests.Session()
session.verify = false

omada = Omada("YourOmadaIPAddress", session = session)
omada.login("username", "passsword")

for client in omada.get_clients():
    print client

omada.logout()
```


## Running tests
To run tests, you must first create a `test.cfg` file. Then run `pytest` (if you don't have pytest installed, run `python3 -m pip install -U pytest`).

Sample `test.cfg`:

```
[omada]
host=192.168.1.2
username=admin
password=YOUR_PASSWORD
```
