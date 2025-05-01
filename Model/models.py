from app import db

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(10), default='cliente')  # 'admin' ou 'cliente'

    pedidos = db.relationship('Pedido', backref='usuario', lazy=True)

class Produto(db.Model):
    __tablename__ = 'produtos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50))
    preco = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    info = db.Column(db.Text)

    itens_pedido = db.relationship('ItemPedido', backref='produto', lazy=True)

class Pedido(db.Model):
    __tablename__ = 'pedidos'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    status = db.Column(db.String(20), default='pendente')
    valor_total = db.Column(db.Float, default=0.0)
    codigo_rastreamento = db.Column(db.String(50))

    itens = db.relationship('ItemPedido', backref='pedido', lazy=True)

class ItemPedido(db.Model):
    __tablename__ = 'itens_pedido'
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)
