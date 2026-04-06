from flask import Flask, send_from_directory, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os

app = Flask(__name__, static_folder='.', static_url_path='')

database_url = os.environ.get('DATABASE_URL', 'sqlite:///clients.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(200), nullable=False)
    owner_name = db.Column(db.String(200), default='')
    phone = db.Column(db.String(50), default='')
    email = db.Column(db.String(200), default='')
    website_url = db.Column(db.String(500), default='')
    plan = db.Column(db.String(50), default='Website Only')
    mrr = db.Column(db.Float, default=0)
    initial_payment = db.Column(db.Float, default=0)
    stripe_status = db.Column(db.String(20), default='Pending')
    notes = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Deployment
    github_repo = db.Column(db.String(500), default='')
    cloudflare_url = db.Column(db.String(500), default='')
    live_url = db.Column(db.String(500), default='')
    # Assets
    google_business = db.Column(db.String(500), default='')
    google_search_console = db.Column(db.String(500), default='')
    google_analytics = db.Column(db.String(500), default='')
    login_credentials = db.Column(db.Text, default='')
    # Contract & Billing
    start_date = db.Column(db.String(20), default='')
    contract_length = db.Column(db.String(30), default='Month-to-Month')
    contract_status = db.Column(db.String(20), default='Active')
    contract_doc_url = db.Column(db.String(500), default='')
    total_paid = db.Column(db.Float, default=0)
    payment_history = db.Column(db.Text, default='[]')

    def to_dict(self):
        return {
            'id': self.id,
            'business_name': self.business_name,
            'owner_name': self.owner_name,
            'phone': self.phone,
            'email': self.email,
            'website_url': self.website_url,
            'plan': self.plan,
            'mrr': self.mrr,
            'initial_payment': self.initial_payment,
            'stripe_status': self.stripe_status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'start_date': self.start_date or '',
            'contract_length': self.contract_length or 'Month-to-Month',
            'contract_status': self.contract_status or 'Active',
            'contract_doc_url': self.contract_doc_url or '',
            'github_repo': self.github_repo or '',
            'cloudflare_url': self.cloudflare_url or '',
            'live_url': self.live_url or '',
            'google_business': self.google_business or '',
            'google_search_console': self.google_search_console or '',
            'google_analytics': self.google_analytics or '',
            'login_credentials': self.login_credentials or '',
            'total_paid': self.total_paid or 0,
            'payment_history': json.loads(self.payment_history or '[]'),
        }


FIELDS = [
    'business_name', 'owner_name', 'phone', 'email', 'website_url',
    'plan', 'stripe_status', 'notes', 'start_date',
    'contract_length', 'contract_status', 'contract_doc_url',
    'github_repo', 'cloudflare_url', 'live_url',
    'google_business', 'google_search_console', 'google_analytics',
    'login_credentials',
]
FLOAT_FIELDS = ['mrr', 'initial_payment', 'total_paid']


def apply_fields(c, data):
    for f in FIELDS:
        if f in data:
            setattr(c, f, data[f])
    for f in FLOAT_FIELDS:
        if f in data:
            setattr(c, f, float(data[f] or 0))
    if 'payment_history' in data:
        c.payment_history = json.dumps(data['payment_history'])


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/api/clients', methods=['GET'])
def get_clients():
    clients = Client.query.order_by(Client.created_at.desc()).all()
    return jsonify([c.to_dict() for c in clients])


@app.route('/api/clients/<int:client_id>', methods=['GET'])
def get_client(client_id):
    c = Client.query.get_or_404(client_id)
    return jsonify(c.to_dict())


@app.route('/api/clients', methods=['POST'])
def create_client():
    data = request.get_json()
    c = Client(business_name=data.get('business_name', ''))
    apply_fields(c, data)
    db.session.add(c)
    db.session.commit()
    return jsonify(c.to_dict()), 201


@app.route('/api/clients/<int:client_id>', methods=['PUT'])
def update_client(client_id):
    c = Client.query.get_or_404(client_id)
    data = request.get_json()
    apply_fields(c, data)
    db.session.commit()
    return jsonify(c.to_dict())


@app.route('/api/clients/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    c = Client.query.get_or_404(client_id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({'ok': True})


def seed_data():
    if Client.query.count() == 0:
        seeds = [
            Client(
                business_name='Presidio Dental Care',
                owner_name='Dr. Maria Santos',
                phone='(520) 555-0142',
                email='maria@presidiodental.com',
                website_url='https://presidiodental.com',
                plan='Website + SEO',
                mrr=450,
                initial_payment=1500,
                stripe_status='Active',
                notes='Flagship client. Referred two other practices.',
                start_date='2025-11-01',
                github_repo='https://github.com/apexintegrations2006/presidio-dental',
                live_url='https://presidiodental.com',
            ),
            Client(
                business_name='Smile Tucson Family Dentistry',
                owner_name='Dr. James Whitfield',
                phone='(520) 555-0287',
                email='james@smiletucson.com',
                website_url='https://smiletucson.com',
                plan='Website Only',
                mrr=250,
                initial_payment=750,
                stripe_status='Active',
                notes='Website launched March 2026. Happy with results.',
                start_date='2026-01-15',
            ),
            Client(
                business_name='Desert Ridge Oral Surgery',
                owner_name='Dr. Anil Kapoor',
                phone='(480) 555-0391',
                email='anil@desertridgeoral.com',
                website_url='https://desertridgeoral.com',
                plan='SEO Only',
                mrr=300,
                initial_payment=500,
                stripe_status='Pending',
                notes='SEO campaign starting next week. Waiting on content.',
                start_date='2026-03-20',
            ),
        ]
        db.session.add_all(seeds)
        db.session.commit()


with app.app_context():
    db.create_all()
    seed_data()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8003))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
