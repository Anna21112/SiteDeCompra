from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging
import jwt
from datetime import datetime, timedelta
from functools import wraps

# Configuração principal
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'sistema_vendas.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
logging.basicConfig(filename='api.log', level=logging.INFO)

SECRET_KEY = 'minha_chave_super_secreta'

from Model.models import Usuario, Produto, Pedido, ItemPedido

# ===================== UTILITÁRIOS =====================

def validate_fields(data, required_fields):
    missing = [field for field in required_fields if field not in data]
    if missing:
        abort(400, description=f"Campos ausentes: {', '.join(missing)}")

def update_model_instance(instance, data, fields):
    for field in fields:
        if field in data:
            setattr(instance, field, data[field])

def auth_admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return {'erro': 'Token ausente'}, 401
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            if data.get('tipo') != 'admin':
                return {'erro': 'Acesso restrito ao administrador'}, 403
        except jwt.ExpiredSignatureError:
            return {'erro': 'Token expirado'}, 401
        except jwt.InvalidTokenError:
            return {'erro': 'Token inválido'}, 401
        return f(*args, **kwargs)
    return decorated

# ===================== ROTAS =====================

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = Usuario.query.filter_by(email=data.get('email')).first()
    if user and user.check_password(data.get('senha')):
        token = jwt.encode({
            'id': user.id,
            'tipo': user.tipo,
            'exp': datetime.utcnow() + timedelta(hours=2)
        }, SECRET_KEY, algorithm='HS256')
        return {'token': token}, 200
    return {'erro': 'Credenciais inválidas'}, 401

# ---------- CLIENTES ----------

@app.route('/clients', methods=['POST'])
def add_client():
    data = request.get_json()
    validate_fields(data, ['nome', 'email', 'senha', 'tipo'])
    client = Usuario(nome=data['nome'], email=data['email'], tipo=data['tipo'])
    client.set_password(data['senha'])
    db.session.add(client)
    db.session.commit()
    return {'message': 'Cliente cadastrado'}, 201

@app.route('/clients', methods=['GET'])
def get_clients():
    clients = Usuario.query.all()
    return {'clients': [c.to_dict() for c in clients]}, 200

@app.route('/clients/<int:id>', methods=['GET'])
def get_client(id):
    client = Usuario.query.get_or_404(id)
    return client.to_dict(), 200

@app.route('/clients/<int:id>', methods=['PUT'])
def update_client(id):
    data = request.get_json()
    client = Usuario.query.get_or_404(id)
    if 'senha' in data:
        data['senha'] = generate_password_hash(data['senha'])
    update_model_instance(client, data, ['nome', 'email', 'senha', 'tipo'])
    db.session.commit()
    return {'message': 'Cliente atualizado'}, 200

@app.route('/clients/<int:id>', methods=['DELETE'])
def delete_client(id):
    client = Usuario.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    return {'message': 'Cliente deletado'}, 200

# ---------- PRODUTOS ----------

@app.route('/products', methods=['POST'])
@auth_admin_required
def add_product():
    data = request.get_json()
    validate_fields(data, ['nome', 'tipo', 'preco', 'quantidade', 'info'])
    new_product = Produto(**data)
    db.session.add(new_product)
    db.session.commit()
    return {'message': 'Produto cadastrado'}, 201

@app.route('/products', methods=['GET'])
def get_products():
    products = Produto.query.all()
    return {'products': [p.to_dict() for p in products]}, 200

@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Produto.query.get_or_404(id)
    return product.to_dict(), 200

@app.route('/products/<int:id>', methods=['PUT'])
@auth_admin_required
def update_product(id):
    data = request.get_json()
    product = Produto.query.get_or_404(id)
    update_model_instance(product, data, ['nome', 'tipo', 'preco', 'quantidade', 'info'])
    db.session.commit()
    return {'message': 'Produto atualizado'}, 200

@app.route('/products/<int:id>', methods=['DELETE'])
@auth_admin_required
def delete_product(id):
    product = Produto.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return {'message': 'Produto deletado'}, 200

# ---------- PEDIDOS (COMPRAS) ----------

@app.route('/orders', methods=['POST'])
def registrar_compra():
    data = request.get_json()
    validate_fields(data, ['usuario_id', 'itens'])
    total = 0
    pedido = Pedido(usuario_id=data['usuario_id'], status='confirmado')
    db.session.add(pedido)
    db.session.flush()

    for item in data['itens']:
        produto = Produto.query.get(item['produto_id'])
        if not produto or produto.quantidade < item['quantidade']:
            abort(400, description='Produto inválido ou estoque insuficiente')
        produto.quantidade -= item['quantidade']
        item_pedido = ItemPedido(
            pedido_id=pedido.id,
            produto_id=produto.id,
            quantidade=item['quantidade'],
            preco_unitario=produto.preco
        )
        total += produto.preco * item['quantidade']
        db.session.add(item_pedido)

    pedido.valor_total = total
    db.session.commit()
    return {'message': 'Compra registrada com sucesso', 'pedido_id': pedido.id}, 201

@app.route('/orders/<int:pedido_id>', methods=['GET'])
def consultar_compra(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    return {
        'id': pedido.id,
        'usuario_id': pedido.usuario_id,
        'status': pedido.status,
        'valor_total': pedido.valor_total,
        'codigo_rastreamento': pedido.codigo_rastreamento,
        'data_criacao': pedido.data_criacao.isoformat(),
        'itens': [item.to_dict() for item in pedido.itens]
    }, 200

# ========== EXECUÇÃO ==========
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
