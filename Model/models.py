from Model.extensions import db

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(10), default='cliente')  # 'admin' ou 'cliente'

    pedidos = db.relationship('Pedido', backref='usuario', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'tipo': self.tipo
        }

class Produto(db.Model):
    __tablename__ = 'produtos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50))
    preco = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    info = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'tipo': self.tipo,
            'preco': self.preco,
            'quantidade': self.quantidade,
            'info': self.info
        }

class Pedido(db.Model):
    __tablename__ = 'pedidos'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    status = db.Column(db.String(20), default='pendente')
    valor_total = db.Column(db.Float, default=0.0)
    codigo_rastreamento = db.Column(db.String(50))
    data_criacao = db.Column(db.DateTime, default=db.func.current_timestamp())

    def calcular_valor_total(self):
        self.valor_total = sum(item.preco_unitario * item.quantidade for item in self.itens_pedido)

    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'status': self.status,
            'valor_total': self.valor_total,
            'codigo_rastreamento': self.codigo_rastreamento,
            'data_criacao': self.data_criacao.strftime('%Y-%m-%d %H:%M:%S')
        }

class ItemPedido(db.Model):
    __tablename__ = 'itens_pedido'
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)
    
    pedido = db.relationship('Pedido', backref='itens_pedido', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'pedido_id': self.pedido_id,
            'produto_id': self.produto_id,
            'quantidade': self.quantidade,
            'preco_unitario': self.preco_unitario
        }
