import hashlib
import time
import json
import logging
from datetime import datetime
from flask import Flask, jsonify, request
import requests
from threading import Thread

# Log ayarları
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


class MythTransaction:
    def __init__(self, gonderen, alici, miktar, mitolojik_olay):
        self.gonderen = gonderen
        self.alici = alici
        self.miktar = miktar  # Tamag birimi
        self.mitolojik_olay = mitolojik_olay


class Block:
    def __init__(self, index, timestamp, transactions, previous_hash, nonce=0):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = f"{self.index}{self.timestamp}{json.dumps([vars(t) for t in self.transactions])}{self.previous_hash}{self.nonce}".encode()
        return hashlib.sha256(block_string).hexdigest()


class TurkMythChain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.pending_transactions = []
        self.difficulty = 4
        self.nodes = set()
        self.miner_reward = 50
        self.allowed_entities = [
            'Ülgen', 'Erlik Han', 'Kayra Han', 'Asena',
            'Börteçine', 'Sistem', 'Gök Kurt', 'Alp Er Tunga'
        ]

    def create_genesis_block(self):
        return Block(0, datetime.now(),
                     [MythTransaction("Kayra Han", "Kök Tamır", 1000, "Tüm Varlıkların Yaratılışı")],
                     "0")

    def add_node(self, address):
        self.nodes.add(address)

    def valid_chain(self, chain):
        if not chain:
            print("𐱅𐰭𐰼𐰃: Boş zincir!")
            return False

        genesis = self.create_genesis_block()
        if chain[0].hash != genesis.hash:
            print("𐰋𐰃𐰠𐰏𐰀: Kök Tamır bozulmuş!")
            return False

        for i in range(1, len(chain)):
            block = chain[i]
            prev_block = chain[i - 1]

            if block.previous_hash != prev_block.hash:
                print(f"𐰴𐰣𐰍: Blok {block.index} bağlantısı koptu!")
                return False

            if not self.valid_proof(block):
                print(f"𐱅𐰇𐰼𐰇: Blok {block.index} sahte kut!")
                return False
        return True

    def resolve_conflicts(self):
        longest_chain = None
        max_length = len(self.chain)

        for node in self.nodes:
            try:
                response = requests.get(f'http://{node}/chain', timeout=3)
                if response.status_code == 200:
                    chain = [
                        Block(
                            blok['index'],
                            datetime.strptime(blok['timestamp'], '%Y-%m-%d %H:%M:%S.%f'),
                            [MythTransaction(**tx) for tx in blok['transactions']],
                            blok['previous_hash'],
                            blok['nonce']
                        ) for blok in response.json()['chain']
                    ]

                    if len(chain) > max_length and self.valid_chain(chain):
                        max_length = len(chain)
                        longest_chain = chain
            except Exception as e:
                print(f"𐰃𐰤𐰀𐰢: {node} node'u yanıt vermiyor: {str(e)}")

        if longest_chain:
            self.chain = longest_chain
            print("𐰆𐰞𐰆𐰍: Uluğ Türük'ün iradesiyle zincir yenilendi!")
            return True
        return False

    def add_transaction(self, transaction):
        if transaction.gonderen not in self.allowed_entities:
            raise ValueError("𐰃𐰾𐰔: Tanrılar Kurulu bu işlemi reddetti!")
        self.pending_transactions.append(transaction)

    def mine_pending_transactions(self, miner_address):
        if not self.pending_transactions:
            print("𐰉𐰆𐰖𐰆𐰴: Kazılacak işlem yok!")
            return

        block = Block(
            index=len(self.chain),
            timestamp=datetime.now(),
            transactions=self.pending_transactions,
            previous_hash=self.chain[-1].hash
        )

        print(f"𐰚𐰇𐱅: Blok #{block.index} için kut aranıyor...")
        while not block.hash.startswith('0' * self.difficulty):
            block.nonce += 1
            block.hash = block.calculate_hash()

        self.chain.append(block)
        self.pending_transactions = [MythTransaction("Sistem", miner_address, self.miner_reward, "Kut Bulma Ödülü")]
        print(f"𐰸𐰆𐱃: Blok #{block.index} kazıldı! | Nonce: {block.nonce}")


app = Flask(__name__)
blockchain = TurkMythChain()


@app.route('/')
def home():
    return jsonify({
        "message": "𐱅𐰇𐰼𐰚 𐰋𐰃𐰘𐰏𐰇: Türk Mitolojisi Blockchain Ağına Hoş Geldiniz!",
        "mitolojik_varlıklar": blockchain.allowed_entities,
        "endpoints": {
            "/chain": "Zinciri görüntüle",
            "/transactions/new": "Yeni işlem ekle (POST)",
            "/nodes/register": "Node kaydet (POST)",
            "/nodes/resolve": "Konsensüs sağla"
        }
    }), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['gonderen', 'alici', 'miktar', 'mitolojik_olay']

    if not all(k in values for k in required):
        return jsonify({"mesaj": "𐰇𐰔𐰤𐰀: Eksik değerler!"}), 400

    try:
        transaction = MythTransaction(values['gonderen'], values['alici'], values['miktar'], values['mitolojik_olay'])
        blockchain.add_transaction(transaction)
        return jsonify({"mesaj": "𐰖𐰀𐰕: Ülgen'in kayıt defterine eklendi"}), 201
    except ValueError as e:
        return jsonify({"mesaj": str(e)}), 403


@app.route('/chain', methods=['GET'])
def full_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append({
            'index': block.index,
            'timestamp': str(block.timestamp),
            'transactions': [vars(t) for t in block.transactions],
            'hash': block.hash,
            'previous_hash': block.previous_hash,
            'nonce': block.nonce
        })
    return jsonify({'chain': chain_data, 'length': len(chain_data)}), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes', [])

    if not nodes:
        return jsonify({"mesaj": "𐰉𐰆𐰞: Node adresi gerekli!"}), 400

    for node in nodes:
        blockchain.add_node(node)

    return jsonify({
        "mesaj": "𐱅𐰭𐰼𐰃: Yeni tengriler katıldı",
        "nodes": list(blockchain.nodes)
    }), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()
    response = {
        "mesaj": "𐰸𐰆𐰑: Zincir Ülgen'in ışığıyla yenilendi" if replaced else "𐰴𐰢𐰍: Zincir zaten en kutlu",
        "zincir_uzunluk": len(blockchain.chain)
    }
    return jsonify(response), 200


@app.after_request
def after_request(response):
    timestamp = datetime.now().strftime('[%d/%b/%Y %H:%M:%S]')
    print(f"{request.remote_addr} - {timestamp} \"{request.method} {request.path}\" {response.status_code}")
    return response


def run_node(port):
    print(f"𐰇𐰢𐰀𐰤: Node {port} başlatılıyor...")
    app.run(host='127.0.0.1', port=port, use_reloader=False)


if __name__ == '__main__':
    ports = [5000, 5001, 5002]
    for port in ports:
        Thread(target=run_node, args=(port,)).start()
        time.sleep(0.5)

    # Node'ları birbirine bağla
    time.sleep(2)
    for port in ports[1:]:
        requests.post(f'http://127.0.0.1:{ports[0]}/nodes/register',
                      json={'nodes': [f'127.0.0.1:{port}']})

    # Örnek işlemler
    time.sleep(3)
    ornek_islemler = [
        {"gonderen": "Ülgen", "alici": "Erlik Han", "miktar": 100, "mitolojik_olay": "Göğ-Yer Dengesi"},
        {"gonderen": "Asena", "alici": "Börteçine", "miktar": 200, "mitolojik_olay": "Bozkır Antlaşması"},
        {"gonderen": "Kayra Han", "alici": "Gök Kurt", "miktar": 500, "mitolojik_olay": "Ergenekon Çıkışı"}
    ]

    for islem in ornek_islemler:
        response = requests.post(f'http://127.0.0.1:{ports[0]}/transactions/new', json=islem)
        print(f"𐰃𐰾𐰠𐰢: {response.json()['mesaj']}")

    # Madencilik
    print("\n𐰸𐰆𐰞: Bozkırın demircileri çalışıyor...")
    blockchain.mine_pending_transactions("Demi̇rci̇ Kawa")

    # Sonuç
    print("\n𐱅𐰇𐰼𐰚 𐰋𐰃𐰘𐰏𐰇: Son Durum")
    for block in blockchain.chain:
        print(f"\n■ Blok {block.index} » {block.hash[:10]}...")
        print(f"← Önceki: {block.previous_hash[:10]}...")
        print(f"⌛ {block.timestamp.strftime('%d/%m/%Y %H:%M')}")
        print(f"📜 {len(block.transactions)} olay:")
        for tx in block.transactions:
            print(f"  → {tx.mitolojik_olay.ljust(25)} {tx.gonderen}→{tx.alici} ({tx.miktar} Tamag)")