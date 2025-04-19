
# Sistema de Gerenciamento Comercial com Flask e SQLite

Este projeto foi desenvolvido como parte da disciplina de **Sistemas Distribuídos e Mobile**, com o objetivo de integrar conhecimentos teóricos e práticos por meio da construção de uma aplicação completa, com frontend e backend, simulando um sistema comercial.

## 🔧 Tecnologias Utilizadas

- **Frontend**: HTML, CSS, JavaScript (com possibilidade de React, Vue ou Angular na Tarefa 5)
- **Backend**: Python (Flask)
- **Banco de Dados**: SQLite
- **Comunicação**: API REST com JSON

## 📋 Funcionalidades

### 🧩 Entidades do Sistema

- **Cliente**: nome, e-mail, telefone
- **Produto**: nome, descrição, preço
- **Compra**: data, cliente, produtos adquiridos

### ✅ Funcionalidades Implementadas

#### 1. Modelagem do Banco de Dados

- Diagrama Entidade-Relacionamento
- Relacionamentos:
  - Um cliente pode ter várias compras
  - Uma compra pode conter múltiplos produtos

#### 2. API REST com Flask

- CRUD de clientes e produtos
- Registro e consulta de compras
- Respostas no formato JSON
- Tratamento de erros comuns

#### 3. Frontend Responsivo

- Listagem de clientes, produtos e compras
- Formulários para cadastro e edição
- Registro de compras com seleção dinâmica de clientes/produtos
- Requisições assíncronas via Fetch/AJAX

#### 4. Relatórios e Filtros

- Histórico de compras por cliente
- Relatório de vendas por produto
- Filtros por intervalo de datas

#### 5. Funcionalidade Extra (Opcional)

- [ ] Integração com framework moderno (React, Vue ou Angular)
- [ ] Exportação de dados (CSV ou PDF)
- [ ] Painel administrativo com gráficos (Chart.js, D3.js)
- [ ] Middleware com Node.js (cache, autenticação)

## 🧪 Como Executar

```bash
# Clone o repositório
git clone https://github.com/seuusuario/nome-do-repo.git
cd nome-do-repo

# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Instale as dependências
pip install -r requirements.txt

# Execute o servidor
python backend/app.py
```

## 🎥 Demonstração

📹 Um vídeo de 3 a 5 minutos mostrando o funcionamento da aplicação será incluído na entrega final.

## 👨‍🏫 Professor Responsável

**Leonardo Augusto Ferreira**
