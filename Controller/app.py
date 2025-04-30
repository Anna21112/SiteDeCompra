from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging
import jwt
from datetime import datetime, timedelta
from functools import wraps
"""
• Criar as rotas da API para listar, cadastrar, atualizar e deletar clientes e produtos. OK
• Criar as rotas para registrar e consultar compras.
• Utilizar SQLite para armazenar todas as informações de forma persistente. OK
• Garantir que as respostas da API estejam no formato JSON.
• Tratar erros comuns, como tentativas de cadastro incompleto ou consulta a registros
inexistentes.
• Implementar autenticação básica para acesso às rotas de administração.
• Criar um sistema de logs para registrar as operações realizadas na API.
• AWT de login e senha para acesso ao sistema.
"""

# Inicialização do app Flask
app = Flask(__name__)

# Configuração do caminho do banco SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'Model', 'sistema_vendas.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#  Inicialização do banco de dados
db = SQLAlchemy(app)

#  Configuração do log da API
logging.basicConfig(filename='api.log', level=logging.INFO)

#  Criação automática das tabelas
with app.app_context():
    db.create_all()
    print("Banco e tabelas criados com sucesso!")

# Função para validação de campos obrigatórios
def validate_fields(data, required_fields):
    missing = [field for field in required_fields if field not in data]
    if missing:
        abort(400, description=f"Campos ausentes: {', '.join(missing)}")

# Função para atualizar instâncias de modelos
def update_model_instance(instance, data, fields):
    for field in fields:
        if field in data:
            setattr(instance, field, data[field])

# ================== ROTAS DE CLIENTES =====================

@app.route('/clients', methods=['GET'])
def get_clients():
    clients = Usuario.query.all()
    return {'clients': [client.to_dict() for client in clients]}, 200

@app.route('/clients/<int:id>', methods=['GET'])
def get_client(id):
    client = Usuario.query.get_or_404(id)
    return client.to_dict(), 200

@app.route('/clients', methods=['POST'])
def add_client():
    data = request.get_json()
    validate_fields(data, ['nome', 'email', 'senha', 'tipo'])
    
    hashed_password = generate_password_hash(data['senha'])
    new_client = Usuario(
        nome=data['nome'],
        email=data['email'],
        senha=hashed_password,
        tipo=data['tipo']
    )
    db.session.add(new_client)
    db.session.commit()
    logging.info(f"Cliente cadastrado: {new_client.email}")
    return {'message': 'Client added successfully'}, 201

@app.route('/clients/<int:id>', methods=['PUT'])
def update_client(id):
    data = request.get_json()
    client = Usuario.query.get_or_404(id)
    
    if 'senha' in data:
        data['senha'] = generate_password_hash(data['senha'])

    update_model_instance(client, data, ['nome', 'email', 'senha', 'tipo'])
    db.session.commit()
    logging.info(f"Cliente atualizado: ID {id}")
    return {'message': 'Client updated successfully'}, 200

@app.route('/clients/<int:id>', methods=['DELETE'])
def delete_client(id):
    client = Usuario.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    logging.info(f"Cliente deletado: ID {id}")
    return {'message': 'Client deleted successfully'}, 200

# ================== ROTAS DE PRODUTOS =====================

@app.route('/products', methods=['GET'])
def get_products():
    products = Produto.query.all()
    return {'products': [product.to_dict() for product in products]}, 200

@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Produto.query.get_or_404(id)
    return product.to_dict(), 200

@app.route('/products', methods=['POST'])
def add_product():
    data = request.get_json()
    validate_fields(data, ['nome', 'tipo', 'preco', 'quantidade', 'info'])

    new_product = Produto(
        nome=data['nome'],
        tipo=data['tipo'],
        preco=data['preco'],
        quantidade=data['quantidade'],
        info=data['info']
    )
    db.session.add(new_product)
    db.session.commit()
    logging.info(f"Produto cadastrado: {new_product.nome}")
    return {'message': 'Product added successfully'}, 201

@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    data = request.get_json()
    product = Produto.query.get_or_404(id)

    update_model_instance(product, data, ['nome', 'tipo', 'preco', 'quantidade', 'info'])
    db.session.commit()
    logging.info(f"Produto atualizado: ID {id}")
    return {'message': 'Product updated successfully'}, 200

@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Produto.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    logging.info(f"Produto deletado: ID {id}")
    return {'message': 'Product deleted successfully'}, 200

