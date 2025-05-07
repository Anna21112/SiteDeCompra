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
from flask import render_template
from flask import redirect, url_for
from flask_cors import CORS
from pytz import timezone

# Importa o objeto `db` do arquivo extensions.py
from Model.extensions import db

# Inicialização do app Flask
app = Flask(__name__)

# Configuração do caminho do banco SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'Model', 'sistema_vendas.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# Inicialização do banco de dados
db.init_app(app)

from Model.models import Usuario, Produto, Pedido, ItemPedido
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
    itens = ItemPedido.query.filter_by(pedido_id=order.id).all()

    order_details = {
        'id': order.id,
        'usuario_id': order.usuario_id,
        'status': order.status,
        'valor_total': order.valor_total,
        'data_criacao': order.data_criacao.strftime('%Y-%m-%d %H:%M:%S'),
        'itens': []
    }

    for item in itens:
        produto = Produto.query.get(item.produto_id)
        if not produto:
            app.logger.error(f"Produto com ID {item.produto_id} não encontrado.")
            continue  # Ignora o item se o produto não for encontrado

        order_details['itens'].append({
            'produto_id': item.produto_id,
            'produto_nome': produto.nome,
            'quantidade': item.quantidade,
            'preco_unitario': item.preco_unitario
        })

    return jsonify(order_details), 200

# Cadastra um novo pedido
@app.route('/orders', methods=['POST'])
def add_order():
    data = request.get_json()
    validate_fields(data, ['usuario_id', 'itens'])

    novo_pedido = Pedido(usuario_id=data['usuario_id'], data_criacao=datetime.now())
    db.session.add(novo_pedido)
    db.session.flush()  # Garante que o ID do pedido seja gerado

    for item in data['itens']:
        produto = Produto.query.get(item['produto_id'])
        if not produto:
            return jsonify({'erro': f"Produto ID {item['produto_id']} não encontrado"}), 404
        if produto.quantidade < item['quantidade']:
            return jsonify({'erro': f"Estoque insuficiente para produto {produto.nome}"}), 400

        produto.quantidade -= item['quantidade']
        item_pedido = ItemPedido(
            pedido_id=novo_pedido.id,
            produto_id=produto.id,
            quantidade=item['quantidade'],
            preco_unitario=produto.preco
        )
        db.session.add(item_pedido)

    # Calcula o valor total do pedido
    novo_pedido.calcular_valor_total()
    db.session.commit()

    app.logger.info(f"Compra registrada para cliente ID {data['usuario_id']}")
    return jsonify({'mensagem': 'Compra registrada com sucesso', 'pedido_id': novo_pedido.id}), 201

# Atualiza um pedido existente
@app.route('/orders/<int:pedido_id>', methods=['PUT'])
def update_order(pedido_id):
    data = request.get_json()
    validate_fields(data, ['itens'])

    pedido = Pedido.query.get_or_404(pedido_id)

    # Reverter estoque anterior
    itens_anteriores = ItemPedido.query.filter_by(pedido_id=pedido.id).all()
    for item in itens_anteriores:
        produto = Produto.query.get(item.produto_id)
        produto.quantidade += item.quantidade
        db.session.delete(item)

    db.session.flush()

    # Adicionar novos itens
    for item in data['itens']:
        produto = Produto.query.get(item['produto_id'])
        if not produto:
            return jsonify({'erro': f"Produto ID {item['produto_id']} não encontrado"}), 404
        if produto.quantidade < item['quantidade']:
            return jsonify({'erro': f"Estoque insuficiente para o produto {produto.nome}"}), 400

        produto.quantidade -= item['quantidade']
        novo_item = ItemPedido(
            pedido_id=pedido.id,
            produto_id=produto.id,
            quantidade=item['quantidade'],
            preco_unitario=produto.preco
        )
        db.session.add(novo_item)

    # Recalcula o valor total do pedido
    pedido.calcular_valor_total()
    db.session.commit()

    return jsonify({'mensagem': 'Pedido atualizado com sucesso'}), 200

# Deleta um pedido existente
@app.route('/orders/<int:id>', methods=['DELETE'])
def delete_order(id):
    order = Pedido.query.get_or_404(id)
    
    # Deleta os itens associados ao pedido
    itens = ItemPedido.query.filter_by(pedido_id=order.id).all()
    for item in itens:
        db.session.delete(item)
    
    # Deleta o pedido
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
                'produto_nome': Produto.query.get(item.produto_id).nome,
                'quantidade': item.quantidade,
                'preco_unitario': item.preco_unitario
            }
            for item in itens
        ]
        pedidos_formatados.append({
            'pedido_id': pedido.id,
            'data_criacao': pedido.data_criacao.strftime('%Y-%m-%d %H:%M:%S'),
            'valor_total': pedido.valor_total,
            'itens': itens_formatados
        })
        
    return jsonify({'pedidos': pedidos_formatados}), 200


@app.route('/api/user-dashboard', methods=['GET'])
def get_user_dashboard():
    client_id = request.args.get('clientId', type=int)

    if not client_id:
        return jsonify({'error': 'clientId é obrigatório'}), 400

    pedidos = Pedido.query.filter_by(usuario_id=client_id).all()

    if not pedidos:
        return jsonify({
            'lastPurchase': None,
            'totalSpent': 0.0,
            'purchasesCount': 0
        }), 200

    total_spent = sum(pedido.valor_total for pedido in pedidos)
    purchases_count = len(pedidos)
    last_purchase_date = max(pedido.data_criacao for pedido in pedidos)

    local_tz = timezone('America/Sao_Paulo')
    last_purchase_date_local = last_purchase_date.astimezone(local_tz)

    return jsonify({
        'lastPurchase': last_purchase_date_local.strftime('%Y-%m-%d %H:%M:%S'),
        'totalSpent': total_spent,
        'purchasesCount': purchases_count
    }), 200
    
    
# ================== RELATÓRIO DE VENDAS POR PRODUTO COM FILTRO DE DATA =====================

@app.route('/api/relatorioVendas', methods=['GET'])
def relatorio_vendas():
    app.logger.info('Rota /api/relatorioVendas chamada.')
    data_inicio = request.args.get('inicio')
    data_fim = request.args.get('fim')
    app.logger.info(f"Parâmetros recebidos - Início: {data_inicio}, Fim: {data_fim}")

    # Query para buscar os dados do relatório
    query = db.session.query(
        Pedido.data_criacao,
        Pedido.id.label('pedido_id'),
        Usuario.nome.label('cliente'),
        Produto.nome.label('produto'),
        func.sum(ItemPedido.quantidade).label('itens'),
        func.sum(ItemPedido.quantidade * ItemPedido.preco_unitario).label('total'),
        Pedido.status
    ).join(Usuario, Pedido.usuario_id == Usuario.id) \
     .join(ItemPedido, Pedido.id == ItemPedido.pedido_id) \
     .join(Produto, Produto.id == ItemPedido.produto_id)

    # Filtro por data, se fornecido
    if data_inicio and data_fim:
        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d')
            data_fim = data_fim.replace(hour=23, minute=59, second=59)
            query = query.filter(Pedido.data_criacao >= data_inicio, Pedido.data_criacao <= data_fim)
        except ValueError:
            app.logger.error('Formato de data inválido.')
            return jsonify({'erro': 'Formato de data inválido. Use AAAA-MM-DD'}), 400

    query = query.group_by(Pedido.id, Produto.id).all()
    app.logger.info(f"Resultados da query: {query}")

    # Formata os dados do relatório
    relatorio = [
        {
            'data': pedido.data_criacao.strftime('%Y-%m-%d'),
            'pedido': pedido.pedido_id,
            'cliente': pedido.cliente,
            'produto': pedido.produto,
            'itens': int(pedido.itens),
            'total': float(pedido.total),
            'status': pedido.status
        }
        for pedido in query
    ]

    # Calcula os produtos mais vendidos
    produtos_agrupados = {}
    for item in relatorio:
        if item['produto'] not in produtos_agrupados:
            produtos_agrupados[item['produto']] = 0
        produtos_agrupados[item['produto']] += item['itens']

    # Ordena os produtos por quantidade vendida e pega os 5 mais vendidos
    produtos_mais_vendidos = sorted(produtos_agrupados.items(), key=lambda x: x[1], reverse=True)[:5]

    # Calcula o resumo
    total_vendido = sum(item['total'] for item in relatorio)
    quantidade_vendas = len(relatorio)
    ticket_medio = total_vendido / quantidade_vendas if quantidade_vendas > 0 else 0

    app.logger.info(f"Resumo - Total Vendido: {total_vendido}, Quantidade de Vendas: {quantidade_vendas}, Ticket Médio: {ticket_medio}")

    return jsonify({
        'relatorio': relatorio,
        'resumo': {
            'total_vendido': total_vendido,
            'quantidade_vendas': quantidade_vendas,
            'ticket_medio': ticket_medio
        },
        'produtos_mais_vendidos': produtos_mais_vendidos
    }), 200

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
        abort(401, description='Credenciais inválidas')

    # Retorna o ID do usuário junto com o token e o tipo de usuário
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }, 'secret_key', algorithm='HS256')

    return jsonify({'token': token, 'clientId': user.id, 'tipo': user.tipo}), 200


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


#===================== TEMPLATES =====================

@app.route('/')
@app.route('/login', methods=['GET'])
def render_login():
    return render_template('login.html')

@app.route('/cadastro', methods=['GET'])
def render_cadastro():
    return render_template('cadastro.html')

@app.route('/dashboard', methods=['GET'])
def render_dashboard():
    return render_template('dashboard.html')

@app.route('/gerenciaClientes', methods=['GET'])
def render_gerencia_clientes():
    return render_template('gerencia_clientes.html')

@app.route('/gerenciaPedidos', methods=['GET'])
def render_gerencia_pedidos():
    return render_template('gerencia_pedidos.html')

@app.route('/gerenciaProdutos', methods=['GET'])
def render_gerencia_produtos():
    return render_template('gerencia_produtos.html')

@app.route('/historicoCompras', methods=['GET'])
def render_historico_compras():
    return render_template('historico_compra_admin.html')

@app.route('/gerenciaUsuarios', methods=['GET'])
def render_gerencia_usuarios():
    return render_template('gerencia_usuarios.html')

@app.route('/dashboardClient', methods=['GET'])
def render_dashboard_client():
    return render_template('dashboardClient.html')

@app.route('/meuPerfil', methods=['GET'])
def render_meu_perfil():
    return render_template('meuPerfil.html')

@app.route('/novaCompra', methods=['GET'])
def render_nova_compra():
    return render_template('novaCompra.html')

@app.route('/historicoComprasClient', methods=['GET'])
def render_historico_compras_cliente():
    return render_template('historicoCompra.html')

@app.route('/visualizarProdutos', methods=['GET'])
def render_visualizar_produtos():
    return render_template('visualizarProduto.html')

@app.route('/relatorioVendas', methods=['GET'])
def render_relatorio_vendas():
    return render_template('relatorioVendas.html')

# ================== EXECUÇÃO DO APP =====================
if __name__ == '__main__':
    # Habilita o CORS para todas as rotas
    CORS(app)
    app.run(debug=True)
    