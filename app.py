from flask import Flask, send_from_directory, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
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
        }


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/api/clients', methods=['GET'])
def get_clients():
    clients = Client.query.order_by(Client.created_at.desc()).all()
    return jsonify([c.to_dict() for c in clients])


@app.route('/api/clients', methods=['POST'])
def create_client():
    data = request.get_json()
    c = Client(
        business_name=data.get('business_name', ''),
        owner_name=data.get('owner_name', ''),
        phone=data.get('phone', ''),
        email=data.get('email', ''),
        website_url=data.get('website_url', ''),
        plan=data.get('plan', 'Website Only'),
        mrr=float(data.get('mrr', 0)),
        initial_payment=float(data.get('initial_payment', 0)),
        stripe_status=data.get('stripe_status', 'Pending'),
        notes=data.get('notes', ''),
    )
    db.session.add(c)
    db.session.commit()
    return jsonify(c.to_dict()), 201


@app.route('/api/clients/<int:client_id>', methods=['PUT'])
def update_client(client_id):
    c = Client.query.get_or_404(client_id)
    data = request.get_json()
    c.business_name = data.get('business_name', c.business_name)
    c.owner_name = data.get('owner_name', c.owner_name)
    c.phone = data.get('phone', c.phone)
    c.email = data.get('email', c.email)
    c.website_url = data.get('website_url', c.website_url)
    c.plan = data.get('plan', c.plan)
    c.mrr = float(data.get('mrr', c.mrr))
    c.initial_payment = float(data.get('initial_payment', c.initial_payment))
    c.stripe_status = data.get('stripe_status', c.stripe_status)
    c.notes = data.get('notes', c.notes)
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
