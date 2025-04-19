from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from models import Usuario, Produto, Pedido, ItemPedido

"""
• Criar as rotas da API para listar, cadastrar, atualizar e deletar clientes e produtos.
• Criar as rotas para registrar e consultar compras.
• Utilizar SQLite para armazenar todas as informações de forma persistente.
• Garantir que as respostas da API estejam no formato JSON.
• Tratar erros comuns, como tentativas de cadastro incompleto ou consulta a registros
inexistentes.
• Implementar autenticação básica para acesso às rotas de administração.
• Criar um sistema de logs para registrar as operações realizadas na API.
• AWT de login e senha para acesso ao sistema.
"""
app = Flask(__name__)

# Caminho do banco SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '/Model/sistema_vendas.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Cria o banco e as tabelas
with app.app_context():
    db.create_all()
    print("Banco e tabelas criados com sucesso!")

#Busca clients
@app.route('/clients', methods=['GET'])
def get_clients():
    clients = Usuario.query.all()
    return {'clients': [client.to_dict() for client in clients]}, 200

#Busca cliente por id
@app.route('/clients/<int:id>', methods=['GET'])
def get_client(id):
    client = Usuario.query.get_or_404(id)
    return client.to_dict(), 200

#Adiciona client
@app.route('/clients', methods=['POST'])
def add_client():
    data = request.get_json()
    new_client = Usuario(nome=data['nome'], email=data['email'], senha=data['senha'], tipo=data['tipo'])
    db.session.add(new_client)
    db.session.commit()
    return {'message': 'Client added successfully'}, 201

# Edita client
@app.route('/clients/<int:id>', methods=['PUT'])
def update_client(id):
    data = request.get_json()
    client = Usuario.query.get_or_404(id)
    client.nome = data['nome']
    client.email = data['email']
    client.senha = data['senha']
    client.tipo = data['tipo']
    db.session.commit()
    return {'message': 'Client updated successfully'}, 200

# Deleta client
@app.route('/clients/<int:id>', methods=['DELETE'])
def delete_client(id):
    client = Usuario.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    return {'message': 'Client deleted successfully'}, 200

#Busca produtos
@app.route('/products', methods=['GET'])
def get_products():
    products = Produto.query.all()
    return {'products': [product.to_dict() for product in products]}, 200

#Busca produto por id
@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Produto.query.get_or_404(id)
    return product.to_dict(), 200

#Adiciona produto
@app.route('/products', methods=['POST'])
def add_product():
    data = request.get_json()
    new_product = Produto(nome=data['nome'], tipo=data['tipo'], preco=data['preco'], quantidade=data['quantidade'], info=data['info'])
    db.session.add(new_product)
    db.session.commit()
    return {'message': 'Product added successfully'}, 201

# Edita produto
@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    data = request.get_json()
    product = Produto.query.get_or_404(id)
    product.nome = data['nome']
    product.tipo = data['tipo']
    product.preco = data['preco']
    product.quantidade = data['quantidade']
    product.info = data['info']
    db.session.commit()
    return {'message': 'Product updated successfully'}, 200

#Deleta produto
@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Produto.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return {'message': 'Product deleted successfully'}, 200
