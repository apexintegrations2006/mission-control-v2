from flask import Flask, send_from_directory, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import uuid
import os

app = Flask(__name__, static_folder='.', static_url_path='')

database_url = os.environ.get('DATABASE_URL', 'sqlite:///clients.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ── Models ──────────────────────────────────────────────

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
    github_repo = db.Column(db.String(500), default='')
    cloudflare_url = db.Column(db.String(500), default='')
    live_url = db.Column(db.String(500), default='')
    google_business = db.Column(db.String(500), default='')
    google_search_console = db.Column(db.String(500), default='')
    google_analytics = db.Column(db.String(500), default='')
    login_credentials = db.Column(db.Text, default='')
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


class ContractTemplate(db.Model):
    __tablename__ = 'contract_templates'
    id = db.Column(db.Integer, primary_key=True)
    plan_type = db.Column(db.String(50), nullable=False, unique=True)
    content = db.Column(db.Text, nullable=False, default='')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'plan_type': self.plan_type,
            'content': self.content,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class SentContract(db.Model):
    __tablename__ = 'contracts_sent'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('contract_templates.id'), nullable=False)
    filled_content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pending Signature')
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    signed_at = db.Column(db.DateTime, nullable=True)
    signer_name = db.Column(db.String(200), default='')
    signer_ip = db.Column(db.String(50), default='')

    client = db.relationship('Client', backref='contracts')
    template = db.relationship('ContractTemplate')

    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'client_name': self.client.business_name if self.client else '',
            'template_id': self.template_id,
            'plan_type': self.template.plan_type if self.template else '',
            'filled_content': self.filled_content,
            'status': self.status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'signed_at': self.signed_at.isoformat() if self.signed_at else None,
            'signer_name': self.signer_name or '',
            'signer_ip': self.signer_ip or '',
        }


# ── Client helpers ──────────────────────────────────────

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


# ── Routes: Pages ───────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/contract/<contract_id>')
def public_contract(contract_id):
    sc = SentContract.query.get_or_404(contract_id)
    return render_template_string(SIGNING_PAGE_HTML, contract=sc)


# ── Routes: Clients API ────────────────────────────────

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


# ── Routes: Contract Templates API ─────────────────────

@app.route('/api/templates', methods=['GET'])
def get_templates():
    ts = ContractTemplate.query.order_by(ContractTemplate.id).all()
    return jsonify([t.to_dict() for t in ts])


@app.route('/api/templates/<int:tid>', methods=['GET'])
def get_template(tid):
    t = ContractTemplate.query.get_or_404(tid)
    return jsonify(t.to_dict())


@app.route('/api/templates/<int:tid>', methods=['PUT'])
def update_template(tid):
    t = ContractTemplate.query.get_or_404(tid)
    data = request.get_json()
    t.content = data.get('content', t.content)
    t.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(t.to_dict())


# ── Routes: Sent Contracts API ──────────────────────────

@app.route('/api/contracts', methods=['GET'])
def get_contracts():
    cs = SentContract.query.order_by(SentContract.sent_at.desc()).all()
    return jsonify([c.to_dict() for c in cs])


@app.route('/api/contracts/<contract_id>', methods=['GET'])
def get_contract(contract_id):
    c = SentContract.query.get_or_404(contract_id)
    return jsonify(c.to_dict())


@app.route('/api/contracts/send', methods=['POST'])
def send_contract():
    data = request.get_json()
    client_id = data.get('client_id')
    client = Client.query.get_or_404(client_id)

    # Find matching template
    tmpl = ContractTemplate.query.filter_by(plan_type=client.plan).first()
    if not tmpl:
        return jsonify({'error': 'No template found for plan: ' + client.plan}), 404

    # Fill placeholders
    filled = tmpl.content
    filled = filled.replace('{{client_name}}', client.business_name or '')
    filled = filled.replace('{{owner_name}}', client.owner_name or '')
    filled = filled.replace('{{plan}}', client.plan or '')
    filled = filled.replace('{{mrr}}', str(int(client.mrr or 0)))
    filled = filled.replace('{{initial_payment}}', str(int(client.initial_payment or 0)))
    filled = filled.replace('{{start_date}}', client.start_date or 'TBD')
    filled = filled.replace('{{contract_length}}', client.contract_length or 'Month-to-Month')

    sc = SentContract(
        client_id=client.id,
        template_id=tmpl.id,
        filled_content=filled,
    )
    db.session.add(sc)
    db.session.commit()
    return jsonify({'id': sc.id, 'url': '/contract/' + sc.id}), 201


@app.route('/api/contracts/<contract_id>/sign', methods=['POST'])
def sign_contract(contract_id):
    sc = SentContract.query.get_or_404(contract_id)
    if sc.status == 'Signed':
        return jsonify({'error': 'Already signed'}), 400
    data = request.get_json()
    sc.signer_name = data.get('signer_name', '')
    sc.signer_ip = request.remote_addr or ''
    sc.signed_at = datetime.utcnow()
    sc.status = 'Signed'
    db.session.commit()
    return jsonify(sc.to_dict())


# ── Public Signing Page HTML ────────────────────────────

SIGNING_PAGE_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contract - Apex Integrations</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; color: #1e293b; }
        .container { max-width: 800px; margin: 0 auto; padding: 40px 24px; }
        .header { text-align: center; margin-bottom: 32px; }
        .header h1 { font-size: 22px; font-weight: 700; color: #0f172a; }
        .header p { font-size: 13px; color: #64748b; margin-top: 4px; }
        .badge { display: inline-block; font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
        .badge-pending { background: #fef3c7; color: #92400e; }
        .badge-signed { background: #d1fae5; color: #065f46; }
        .contract-body {
            background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
            padding: 32px; white-space: pre-wrap; font-size: 14px; line-height: 1.7;
            color: #334155; margin-bottom: 32px;
        }
        .sign-section {
            background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 28px;
        }
        .sign-section h3 { font-size: 16px; font-weight: 700; margin-bottom: 16px; color: #0f172a; }
        .sign-input {
            width: 100%; padding: 10px 14px; border: 1px solid #cbd5e1; border-radius: 8px;
            font-size: 14px; font-family: inherit; outline: none; margin-bottom: 12px;
        }
        .sign-input:focus { border-color: #7b68ee; }
        .sign-check { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #475569; margin-bottom: 16px; cursor: pointer; }
        .sign-check input { width: 16px; height: 16px; accent-color: #7b68ee; }
        .sign-btn {
            background: #7b68ee; color: #fff; border: none; padding: 10px 24px;
            border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer;
        }
        .sign-btn:hover { background: #6952e0; }
        .sign-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .signed-info {
            background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 12px;
            padding: 24px; text-align: center;
        }
        .signed-info h3 { color: #065f46; font-size: 18px; margin-bottom: 8px; }
        .signed-info p { font-size: 13px; color: #475569; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Apex Integrations &mdash; Service Agreement</h1>
            <p>Contract for {{ contract.client.business_name }}</p>
            <div style="margin-top:8px;">
                {% if contract.status == 'Signed' %}
                <span class="badge badge-signed">Signed</span>
                {% else %}
                <span class="badge badge-pending">Pending Signature</span>
                {% endif %}
            </div>
        </div>

        <div class="contract-body">{{ contract.filled_content }}</div>

        {% if contract.status == 'Signed' %}
        <div class="signed-info">
            <h3>&#10003; Contract Signed</h3>
            <p>Signed by <strong>{{ contract.signer_name }}</strong> on {{ contract.signed_at.strftime('%B %d, %Y at %I:%M %p') }}</p>
        </div>
        {% else %}
        <div class="sign-section">
            <h3>Sign This Contract</h3>
            <input class="sign-input" id="sigName" placeholder="Type your full legal name">
            <label class="sign-check"><input type="checkbox" id="sigAgree"> I agree to the terms above</label>
            <button class="sign-btn" id="sigBtn" onclick="signContract()" disabled>Sign Contract</button>
        </div>
        <script>
            document.getElementById('sigAgree').addEventListener('change', function() {
                document.getElementById('sigBtn').disabled = !(this.checked && document.getElementById('sigName').value.trim());
            });
            document.getElementById('sigName').addEventListener('input', function() {
                document.getElementById('sigBtn').disabled = !(document.getElementById('sigAgree').checked && this.value.trim());
            });
            function signContract() {
                var name = document.getElementById('sigName').value.trim();
                if (!name) return;
                document.getElementById('sigBtn').disabled = true;
                document.getElementById('sigBtn').textContent = 'Signing...';
                fetch('/api/contracts/{{ contract.id }}/sign', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ signer_name: name }),
                }).then(function(r) { return r.json(); })
                  .then(function() { location.reload(); });
            }
        </script>
        {% endif %}
    </div>
</body>
</html>'''


# ── Seed Data ───────────────────────────────────────────

WEBSITE_TEMPLATE = """PROFESSIONAL SERVICES AGREEMENT — WEBSITE DESIGN & DEVELOPMENT

This Professional Services Agreement ("Agreement") is entered into between Apex Integrations ("Provider") and {{client_name}} ("Client"), represented by {{owner_name}}.

1. SCOPE OF SERVICES
Provider agrees to design, develop, and deliver a custom professional website for Client's dental practice. The website will be mobile-responsive, SEO-optimized, and built to modern web standards.

2. SERVICE PLAN
Plan: {{plan}}
Monthly Recurring Fee: ${{mrr}}/month
Initial Setup Fee: ${{initial_payment}} (due upon signing)
Contract Term: {{contract_length}}
Service Start Date: {{start_date}}

3. DELIVERABLES
- Custom homepage design tailored to Client's dental practice brand
- Up to 8 interior pages (About, Services, Team, Contact, etc.)
- Mobile-responsive design across all devices
- Basic on-page SEO setup (meta tags, schema markup, sitemap)
- Contact form integration
- Google Maps integration
- SSL certificate and hosting setup via Cloudflare Pages
- 30-day post-launch support period

4. PAYMENT TERMS
- Initial setup fee of ${{initial_payment}} is due upon execution of this Agreement
- Monthly recurring fee of ${{mrr}} is billed on the 1st of each month via Stripe
- Late payments are subject to a 5% fee after 15 days past due
- Client may cancel monthly services with 30 days written notice

5. INTELLECTUAL PROPERTY
Upon full payment, Client owns all custom content and design assets. Provider retains rights to underlying code frameworks and templates.

6. TERM & TERMINATION
This Agreement begins on {{start_date}} and continues on a {{contract_length}} basis. Either party may terminate with 30 days written notice. Outstanding invoices remain due upon termination.

7. LIMITATION OF LIABILITY
Provider's total liability shall not exceed the total fees paid by Client in the preceding 12 months.

By signing below, both parties agree to the terms outlined in this Agreement.

Provider: Apex Integrations
Date: {{start_date}}

Client: {{client_name}}
Signature: ___________________________"""

SEO_TEMPLATE = """PROFESSIONAL SERVICES AGREEMENT — SEO SERVICES

This Professional Services Agreement ("Agreement") is entered into between Apex Integrations ("Provider") and {{client_name}} ("Client"), represented by {{owner_name}}.

1. SCOPE OF SERVICES
Provider agrees to deliver ongoing Search Engine Optimization (SEO) services to improve Client's dental practice visibility in local and organic search results.

2. SERVICE PLAN
Plan: {{plan}}
Monthly Recurring Fee: ${{mrr}}/month
Initial Setup Fee: ${{initial_payment}} (due upon signing)
Contract Term: {{contract_length}}
Service Start Date: {{start_date}}

3. DELIVERABLES
- Comprehensive SEO audit and keyword research
- Google Business Profile optimization and management
- Monthly on-page SEO improvements
- Local citation building and management
- Monthly performance reporting (rankings, traffic, leads)
- Google Search Console and Analytics setup and monitoring
- Content strategy recommendations
- Quarterly strategy review calls

4. PAYMENT TERMS
- Initial setup fee of ${{initial_payment}} is due upon execution of this Agreement
- Monthly recurring fee of ${{mrr}} is billed on the 1st of each month via Stripe
- Late payments are subject to a 5% fee after 15 days past due
- Client may cancel monthly services with 30 days written notice

5. RESULTS DISCLAIMER
SEO results are not guaranteed. Provider will use industry best practices but search engine algorithms are outside Provider's control. Typical results take 3-6 months to materialize.

6. TERM & TERMINATION
This Agreement begins on {{start_date}} and continues on a {{contract_length}} basis. Either party may terminate with 30 days written notice.

7. LIMITATION OF LIABILITY
Provider's total liability shall not exceed the total fees paid by Client in the preceding 12 months.

By signing below, both parties agree to the terms outlined in this Agreement.

Provider: Apex Integrations
Date: {{start_date}}

Client: {{client_name}}
Signature: ___________________________"""

COMBO_TEMPLATE = """PROFESSIONAL SERVICES AGREEMENT — WEBSITE DESIGN & SEO SERVICES

This Professional Services Agreement ("Agreement") is entered into between Apex Integrations ("Provider") and {{client_name}} ("Client"), represented by {{owner_name}}.

1. SCOPE OF SERVICES
Provider agrees to design, develop, and deliver a custom professional website AND provide ongoing SEO services for Client's dental practice.

2. SERVICE PLAN
Plan: {{plan}}
Monthly Recurring Fee: ${{mrr}}/month
Initial Setup Fee: ${{initial_payment}} (due upon signing)
Contract Term: {{contract_length}}
Service Start Date: {{start_date}}

3. WEBSITE DELIVERABLES
- Custom homepage design tailored to Client's dental practice brand
- Up to 8 interior pages (About, Services, Team, Contact, etc.)
- Mobile-responsive design across all devices
- Contact form integration and Google Maps
- SSL certificate and hosting setup via Cloudflare Pages
- 30-day post-launch support period

4. SEO DELIVERABLES
- Comprehensive SEO audit and keyword research
- Google Business Profile optimization and management
- Monthly on-page SEO improvements
- Local citation building and management
- Monthly performance reporting (rankings, traffic, leads)
- Google Search Console and Analytics setup and monitoring
- Content strategy recommendations
- Quarterly strategy review calls

5. PAYMENT TERMS
- Initial setup fee of ${{initial_payment}} is due upon execution of this Agreement
- Monthly recurring fee of ${{mrr}} is billed on the 1st of each month via Stripe
- Late payments are subject to a 5% fee after 15 days past due
- Client may cancel monthly services with 30 days written notice

6. INTELLECTUAL PROPERTY
Upon full payment, Client owns all custom content and design assets. Provider retains rights to underlying code frameworks and templates.

7. RESULTS DISCLAIMER
SEO results are not guaranteed. Provider will use industry best practices but search engine algorithms are outside Provider's control.

8. TERM & TERMINATION
This Agreement begins on {{start_date}} and continues on a {{contract_length}} basis. Either party may terminate with 30 days written notice. Outstanding invoices remain due upon termination.

9. LIMITATION OF LIABILITY
Provider's total liability shall not exceed the total fees paid by Client in the preceding 12 months.

By signing below, both parties agree to the terms outlined in this Agreement.

Provider: Apex Integrations
Date: {{start_date}}

Client: {{client_name}}
Signature: ___________________________"""


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
                mrr=450, initial_payment=1500,
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
                mrr=250, initial_payment=750,
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
                mrr=300, initial_payment=500,
                stripe_status='Pending',
                notes='SEO campaign starting next week. Waiting on content.',
                start_date='2026-03-20',
            ),
        ]
        db.session.add_all(seeds)
        db.session.commit()

    if ContractTemplate.query.count() == 0:
        templates = [
            ContractTemplate(plan_type='Website Only', content=WEBSITE_TEMPLATE),
            ContractTemplate(plan_type='SEO Only', content=SEO_TEMPLATE),
            ContractTemplate(plan_type='Website + SEO', content=COMBO_TEMPLATE),
        ]
        db.session.add_all(templates)
        db.session.commit()


with app.app_context():
    db.create_all()
    seed_data()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8003))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
