import threading
import time
from flask import Flask, render_template
from turbo_flask import Turbo
from xrpl.clients import JsonRpcClient
from xrpl.models import Ledger

app = Flask(__name__)
turbo = Turbo(app)

# Create a client to connect to the main network
client = JsonRpcClient("https://testnet.xrpl-labs.com/")

@app.route('/')
def index():
    return render_template('index.html')

@app.context_processor
def inject_ledger():
    # Create a Ledger request and have the client call it
    ledger_request = Ledger(ledger_index="validated", transactions=True)
    ledger_response = client.request(ledger_request).result
    ledger = ledger_response['ledger']
    return {'close_time_human': ledger['close_time_human'],
            'ledger_hash': ledger['ledger_hash'],
            'ledger_index': ledger['ledger_index'],
            'tx_count': str(len(ledger['transactions']))
            }

def update_ledger():
    with app.app_context():
        while True:
            time.sleep(5)
            turbo.push(turbo.replace(render_template('ledger.html'), 'ledger'))

with app.app_context():
    threading.Thread(target=update_ledger,daemon=True).start()
