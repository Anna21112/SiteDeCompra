from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging
import jwt
from datetime import datetime, timedelta
from functools import wraps
import logging
from logging.handlers import RotatingFileHandler
from sqlalchemy import func

from Model.models import Usuario, Produto, Pedido, ItemPedido

"""
• Criar as rotas da API para listar, cadastrar, atualizar e deletar clientes e produtos. OK
• Criar as rotas para registrar e consultar compras. OK
• Utilizar SQLite para armazenar todas as informações de forma persistente. OK
• Garantir que as respostas da API estejam no formato JSON. OK
• Tratar erros comuns, como tentativas de cadastro incompleto ou consulta a registros inexistentes. OK
• Implementar autenticação básica para acesso às rotas de administração. OK
• Criar um sistema de logs para registrar as operações realizadas na API. OK
• AWT de login e senha para acesso ao sistema. OK
"""

# Inicialização do app Flask
app = Flask(__name__)

# Configuração do caminho do banco SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'Model', 'sistema_vendas.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#  Inicialização do banco de dados
db = SQLAlchemy(app)

# ================== LOGS =====================

#  Configuração do log da API
os.makedirs('logs', exist_ok=True)
log_handler = RotatingFileHandler('logs/api.log', maxBytes=1000000, backupCount=3)
log_handler.setLevel(logging.INFO)
log_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(funcName)s] %(message)s')
log_handler.setFormatter(log_formatter)
app.logger.addHandler(log_handler)

#Inicialização do log
@app.before_request
def log_request_info():
    app.logger.info(f"Request: {request.method} {request.path} - Body: {request.get_json(silent=True)}")

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

#Lista todos os clientes cadastrados
@app.route('/clients', methods=['GET'])
def get_clients():
    clients = Usuario.query.all()
    return {'clients': [client.to_dict() for client in clients]}, 200

# Lista um cliente específico
@app.route('/clients/<int:id>', methods=['GET'])
def get_client(id):
    client = Usuario.query.get_or_404(id)
    return client.to_dict(), 200

# Cadastra um novo cliente
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

# Atualiza um cliente existente
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

# Deleta um cliente existente
@app.route('/clients/<int:id>', methods=['DELETE'])
def delete_client(id):
    client = Usuario.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    logging.info(f"Cliente deletado: ID {id}")
    return {'message': 'Client deleted successfully'}, 200

# ================== ROTAS DE PRODUTOS =====================

# Lista todos os produtos cadastrados
@app.route('/products', methods=['GET'])
def get_products():
    products = Produto.query.all()
    return {'products': [product.to_dict() for product in products]}, 200

# Lista um produto específico
@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Produto.query.get_or_404(id)
    return product.to_dict(), 200

# Cadastra um novo produto
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

# Atualiza um produto existente
@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    data = request.get_json()
    product = Produto.query.get_or_404(id)

    update_model_instance(product, data, ['nome', 'tipo', 'preco', 'quantidade', 'info'])
    db.session.commit()
    logging.info(f"Produto atualizado: ID {id}")
    return {'message': 'Product updated successfully'}, 200

# Deleta um produto existente
@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Produto.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    logging.info(f"Produto deletado: ID {id}")
    return {'message': 'Product deleted successfully'}, 200

# ================== ROTAS DE PEDIDOS =====================

# Lista todos os pedidos cadastrados
@app.route('/orders', methods=['GET'])
def get_orders():
    orders = Pedido.query.all()
    return {'orders': [order.to_dict() for order in orders]}, 200

# Lista um pedido específico
@app.route('/orders/<int:id>', methods=['GET'])
def get_order(id):
    order = Pedido.query.get_or_404(id)
    return order.to_dict(), 200

# Cadastra um novo pedido
@app.route('/orders', methods=['POST'])
def add_order():
    data = request.get_json()
    validate_fields(data, ['cliente_id', 'produtos'])

    new_order = Pedido(cliente_id=data['cliente_id'])
    db.session.add(new_order)
    db.session.commit()

    for item in data['produtos']:
        product = Produto.query.get_or_404(item['produto_id'])
        new_item = ItemPedido(
            pedido_id=new_order.id,
            produto_id=product.id,
            quantidade=item['quantidade']
        )
        db.session.add(new_item)

    db.session.commit()
    logging.info(f"Pedido cadastrado: ID {new_order.id}")
    return {'message': 'Order added successfully'}, 201

# Atualiza um pedido existente
@app.route('/orders/<int:id>', methods=['PUT'])
def update_order(id):
    data = request.get_json()
    order = Pedido.query.get_or_404(id)

    if 'produtos' in data:
        for item in data['produtos']:
            product = Produto.query.get_or_404(item['produto_id'])
            new_item = ItemPedido(
                pedido_id=order.id,
                produto_id=product.id,
                quantidade=item['quantidade']
            )
            db.session.add(new_item)

    db.session.commit()
    logging.info(f"Pedido atualizado: ID {id}")
    return {'message': 'Order updated successfully'}, 200

# Deleta um pedido existente
@app.route('/orders/<int:id>', methods=['DELETE'])
def delete_order(id):
    order = Pedido.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    logging.info(f"Pedido deletado: ID {id}")
    return {'message': 'Order deleted successfully'}, 200


@app.route('/orders/client/<int:client_id>', methods=['GET'])
def get_orders_by_client(client_id):
    pedidos = Pedido.query.filter_by(usuario_id=client_id).all()
    if not pedidos:
        return jsonify({'message': 'Nenhuma compra encontrada para este cliente'}), 404

    pedidos_formatados = []
    for pedido in pedidos:
        itens = ItemPedido.query.filter_by(pedido_id=pedido.id).all()
        itens_formatados = [
            {
                'produto_id': item.produto_id,
                'quantidade': item.quantidade,
                'preco_unitario': item.preco_unitario
            }
            for item in itens
        ]
        pedidos_formatados.append({
            'pedido_id': pedido.id,
            'data': pedido.data.strftime('%Y-%m-%d %H:%M:%S'),
            'itens': itens_formatados
        })


# ================== RELATÓRIO DE VENDAS POR PRODUTO COM FILTRO DE DATA =====================

@app.route('/reports/sales-by-product', methods=['GET'])
def report_sales_by_product():
    from sqlalchemy import func
    data_inicio = request.args.get('inicio')
    data_fim = request.args.get('fim')

    query = db.session.query(
        Produto.nome,
        func.sum(ItemPedido.quantidade).label('total_vendido')
    ).join(ItemPedido, Produto.id == ItemPedido.produto_id)     .join(Pedido, Pedido.id == ItemPedido.pedido_id)

    if data_inicio and data_fim:
        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d')
            query = query.filter(Pedido.data >= data_inicio, Pedido.data <= data_fim)
        except ValueError:
            return jsonify({'erro': 'Formato de data inválido. Use AAAA-MM-DD'}), 400

    resultados = query.group_by(Produto.id).all()

    relatorio = [
        {'produto': nome, 'quantidade_vendida': int(total)}
        for nome, total in resultados
    ]

    return jsonify({'relatorio_vendas': relatorio}), 200


# ================== AUTENTICAÇÃO =====================
'''
Justificativa: A autenticação é feita através de JWT (JSON Web Tokens), que são gerados quando o usuário faz login. O token contém informações sobre o usuário e é assinado com uma chave secreta. O token é enviado no cabeçalho das requisições para rotas protegidas.

O token tem um tempo de expiração definido (1 hora neste caso) e deve ser renovado após esse período. O uso de JWT permite que a autenticação seja feita de forma segura e escalável, sem a necessidade de armazenar sessões no servidor.
'''

# Rota de login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    validate_fields(data, ['email', 'senha'])

    user = Usuario.query.filter_by(email=data['email']).first()
    if not user or not check_password_hash(user.senha, data['senha']):
        abort(401, description='Invalid credentials')

    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }, 'secret_key', algorithm='HS256')

    return jsonify({'token': token}), 200


# Decorador para proteger rotas
'''
Justificativa: O decorador `token_required` é usado para proteger rotas que exigem autenticação. Ele verifica se o token JWT está presente no cabeçalho da requisição e se é válido. Se o token não for válido ou estiver ausente, a requisição é abortada com um erro 401 (não autorizado).
Se o token for válido, o usuário correspondente é recuperado do banco de dados e passado para a função da rota como argumento.'''
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            abort(401, description='Token is missing')

        try:
            data = jwt.decode(token, 'secret_key', algorithms=['HS256'])
            current_user = Usuario.query.get(data['user_id'])
        except jwt.ExpiredSignatureError:
            abort(401, description='Token has expired')
        except jwt.InvalidTokenError:
            abort(401, description='Invalid token')

        return f(current_user, *args, **kwargs)

    return decorated


@app.route('/logout', methods=['POST'])
def logout():
    # Invalidate the token (this is a placeholder, as JWT tokens are stateless)
    return jsonify({'message': 'Logged out successfully'}), 200

# Função para tratamento de erros
@app.errorhandler(400)
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Erro: {str(e)}", exc_info=True)
    return jsonify({'error': 'Ocorreu um erro interno'}), 500

# ================== EXECUÇÃO DO APP =====================
if __name__ == '__main__':
    app.run(debug=True)
    