Creating a dynamically updating XRP Ledger monitor with Turbo Flask
===================================================================

To begin you may want to create a directory and activate a virtual environment for your project. Once that is done install [Flask](https://pypi.org/project/Flask/), [Turbo-Flask](https://pypi.org/project/Turbo-Flask/) and the [XRP Ledger](https://pypi.org/project/xrpl-py/) Python library.

```
% pip install flask turbo-flask xrpl-py
```

First create a static Flask web application named `app.py` that will display basic XRP Ledger (XRPL) data when the client browser make a request:

```
from flask import Flask, render\_template  
from xrpl.clients import JsonRpcClient  
from xrpl.models import Ledger  
  
app = Flask(\_\_name\_\_)  
  
\# Create a client to connect to the test network  
client = JsonRpcClient("https://testnet.xrpl-labs.com/")  
  
@app.route('/')  
def index():  
    return render\_template('index.html')  
  
@app.context\_processor  
def inject\_ledger():  
    # Create a Ledger request and have the client call it  
    ledger\_request = Ledger(ledger\_index="validated", transactions=True)  
    ledger\_response = client.request(ledger\_request).result  
    ledger = ledger\_response\['ledger'\]  
    return {'close\_time\_human': ledger\['close\_time\_human'\],  
            'ledger\_hash': ledger\['ledger\_hash'\],  
            'ledger\_index': ledger\['ledger\_index'\],  
            'tx\_count': str(len(ledger\['transactions'\]))  
            }
```

The `JsonRpcClient` class provides a sync client for interacting with the XRP Ledger JSON RPC. The function `inject_ledger` uses this client to request the latest validated [ledger](https://xrpl.org/ledger.html) from the testnet blockchain, an example of a successful response is shown below:

```
{  
  "result": {  
    "ledger": {  
      "accepted": true,  
      "account\_hash": "B258A8BB4743FB74CBBD6E9F67E4A56C4432EA09E5805E4CC2DA26F2DBE8F3D1",  
      "close\_flags": 0,  
      "close\_time": 638329271,  
      "close\_time\_human": "2020-Mar-24 01:41:11.000000000 UTC",  
      "close\_time\_resolution": 10,  
      "closed": true,  
      "hash": "3652D7FD0576BC452C0D2E9B747BDD733075971D1A9A1D98125055DEF428721A",  
      "ledger\_hash": "3652D7FD0576BC452C0D2E9B747BDD733075971D1A9A1D98125055DEF428721A",  
      "ledger\_index": "54300940",  
      "parent\_close\_time": 638329270,  
      "parent\_hash": "AE996778246BC81F85D5AF051241DAA577C23BCA04C034A7074F93700194520D",  
      "seqNum": "54300940",  
      "totalCoins": "99991024049618156",  
      "total\_coins": "99991024049618156",  
      "transaction\_hash": "FC6FFCB71B2527DDD630EE5409D38913B4D4C026AA6C3B14A3E9D4ED45CFE30D"  
    },  
    "ledger\_hash": "3652D7FD0576BC452C0D2E9B747BDD733075971D1A9A1D98125055DEF428721A",  
    "ledger\_index": 54300940,  
    "status": "success",  
    "validated": true  
  }  
}
```

Flask’s `context_processor` decorator makes our `inject_ledger` function available to the Flask application.

Inside the project create a folder called templates which contains html files to be served by the Flask development server on runtime:

```
my-app/  
├─ templates/  
│  ├─ base.html  
│  ├─ index.html  
│  ├─ ledger.html  
├─ app.py
```

The `base.html` includes the HTML definition and simple style for the table that will contain data retrieved from the XRPL by our application:

```
<!doctype html>  
<html>  
  <head>  
    <title>XRP Ledger + Turbo Flask Demo</title>  
    <style>  
      .ledger {  
        float: left;  
        width: 780px;  
        border: 1px solid black;  
        margin-right: 10px;  
        margin-bottom: 10px;  
        padding: 10px;  
      }  
      .ledger th, .ledger td {  
        padding: 6px;  
        text-align: left;  
      }  
    </style>  
  </head>  
  <body>  
    {% block content %}{% endblock %}  
    {% include "ledger.html" %}  
  </body>  
</html>
```

The `index.html` served by Flask extends the base template and simply includes some introductory text:

```
{% extends "base.html" %}{% block content %}  
<h1>The XRP Ledger: The Blockchain Built for Business</h1>  
<p>The XRP Ledger (XRPL) is a decentralized, public blockchain led by a global community of businesses and developers looking to solve problems and create value.</p>  
<p>Visit <a href="[https://xrpl.org/](https://xrpl.org/)" target="\_blank">xrpl.log</a> to learn more.</p>  
{% endblock %}
```

Finally `ledger.html` includes the [Jinja](https://palletsprojects.com/p/jinja/) template variables to be populated by the `inject_ledger` function inside our application:

```
<p>  
    <div id="ledger" class="ledger">  
        <table>  
          <tr><th>Close Time: </th><td>{{ close\_time\_human }}</td></tr>  
          <tr><th>Ledger Hash: </th><td>{{ ledger\_hash }}</td></tr>  
          <tr><th>Ledger Index: </th><td><a href="//testnet.xrpl.org/ledgers/{{ ledger\_index }}" target="\_blank">{{ledger\_index }}</a></td></tr>  
          <tr><th># of TXs: </th><td>{{ tx\_count }}</td></tr>  
        </table>  
    </div>  
</p>
```

Now run the application and open a browser to the Flask development web server running on [http://127.0.0.1:5000](http://127.0.0.1:5000)

```
% flask run
```

Note the page is static, data is updated only when the user presses refresh. To make this page dynamic we introduce the magic of Hotwire’s 🌶 [Turbo](https://turbo.hotwired.dev/)

Import the Turbo class and immediately after the Flask application instance is initialised wire it up to Turbo:

```
from turbo\_flask import Turbo
``````
turbo = Turbo(app)
```

Import threading and time for a new background process:

```
import threading  
import time
```

At the bottom of your `app.py` file create the new background process which uses Turbo to push updates into the `ledger.html` file every 5 seconds. Setting `daemon=True` inside our thread will ensure the process stops when the main Flask application exits:

```
def update\_ledger():  
    with app.app\_context():  
        while True:  
            time.sleep(5)  
            turbo.push(turbo.replace(render\_template('ledger.html'), 'ledger'))  
  
with app.app\_context():  
    threading.Thread(target=update\_ledger,daemon=True).start()
```

Inside the `base.html` include Turbo inside the `<head>` element. This opens a websocket connection with the web server allowing the server to send data to the client without them having to request it:

```
<!doctype html>  
<html>  
 <head>  
 …  
 {{ turbo() }}  
 </head>  
</html>
```

Run the Flask (now with Turbo) application:

```
% flask run
```

Open your browser to [http://127.0.0.1:5000](http://127.0.0.1:5000) and watch as the background process dynamically updates information from the XRP Ledger without refreshing the page as shown in this animated gif:

**References**:

\[1\] [Dynamically Update Your Flask Web Pages Using Turbo-Flask](https://blog.miguelgrinberg.com/post/dynamically-update-your-flask-web-pages-using-turbo-flask)  
\[2\] [XRPL Code Snippets](https://xrpl-py.readthedocs.io/en/stable/source/snippets.html)  
\[3\] [Flask deprecated before\_first\_request how to update](https://stackoverflow.com/questions/73570041/flask-deprecated-before-first-request-how-to-update)  
\[4\] [Flask v2.3.x Release Notes](https://flask.palletsprojects.com/en/2.3.x/changes/)  
\[5\] [Threading — Thread Objects](https://docs.python.org/3/library/threading.html#thread-objects)
