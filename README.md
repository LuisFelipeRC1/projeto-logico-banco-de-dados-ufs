# Trabalho de Banco de Dados 
# Projeto Lógico de Banco de Dados – Sistema de Gestão de Empresas e Pesquisas

Este repositório contém a **aplicação de demonstração CRUD** desenvolvida a partir do **Projeto Lógico de Banco de Dados** elaborado com base em um Diagrama Entidade-Relacionamento (DER), conforme apresentado no trabalho acadêmico da disciplina de Banco de Dados.

O banco de dados foi projetado para dar suporte a um **sistema de gestão de empresas, usuários, pesquisas, créditos e leads**, garantindo integridade referencial, consistência dos dados e aderência ao modelo relacional.

---

## 🎯 Objetivo da Aplicação

A aplicação tem como objetivo exclusivo:

- Demonstrar a comunicação com um SGBD
- Executar operações básicas de manipulação de dados (CRUD):
  - Inserção (INSERT)
  - Leitura (SELECT)
  - Atualização (UPDATE)
  - Remoção (DELETE)
- Mostrar o efeito direto dessas operações no banco de dados

⚠️ **Observação importante:**  
Esta aplicação **não representa o sistema final descrito na especificação do projeto**. Ela foi desenvolvida apenas para fins acadêmicos, conforme exigido no enunciado do trabalho.

---

## 🧩 Modelo de Dados Utilizado

O modelo de dados foi derivado do DER conceitual e inclui, entre outras, as seguintes entidades:

- Empresa
- Usuário
- Usuário_Comum
- Admin_da_Empresa
- Admin_do_Sistema
- Pesquisa
- Lead
- Resultado_de_pesquisa
- Crédito
- Pagamento
- Integração
- Log_de_acesso

### Relacionamentos relevantes:
- Uma **Empresa** possui vários **Usuários**
- Um **Usuário_Comum** realiza várias **Pesquisas**
- O relacionamento **N:N entre Pesquisa e Lead** é resolvido pela entidade associativa `Resultado_de_pesquisa`
- Uma **Empresa** pode possuir vários **Créditos, Pagamentos e Integrações**

---

## 🔄 Estruturas Utilizadas no CRUD

Conforme exigido no trabalho, a aplicação realiza operações CRUD sobre **três estruturas** do modelo relacional:

- ✅ Duas tabelas oriundas de **entidades**
- ✅ Uma tabela oriunda de um **relacionamento/agregação** (entidade associativa)

Essas estruturas foram escolhidas para demonstrar corretamente operações sobre entidades fortes e relacionamentos do modelo.


---

## 🛠️ Tecnologias Utilizadas

- **Banco de Dados:** PostgreSQL  
- **Banco de Dados:** MySQL 
- **Modelagem:** MySQL Workbench  


---


## 📎 Observações Finais

- O script SQL de criação das tabelas acompanha o trabalho
- O banco de dados foi criado conforme o projeto lógico apresentado no relatório
- Este repositório atende exclusivamente aos requisitos da etapa de aplicação do trabalho

## 📌 Descrição Geral - NoSQL

Este repositório contém a implementação da **parte NoSQL** do trabalho da disciplina de Banco de Dados.  
O objetivo desta etapa é demonstrar o mapeamento de um projeto conceitual para um **modelo NoSQL**, bem como o desenvolvimento de uma aplicação simples que realiza operações CRUD em um banco de dados NoSQL.

O SGBD escolhido foi o **MongoDB**, utilizando o modelo orientado a documentos.

---

## 🧠 SGBD NoSQL Escolhido

- **MongoDB**
- Modelo orientado a documentos
- Dados armazenados em formato BSON (JSON)
- Utilização de documentos embutidos e agregações

---

## 🗂 Estrutura do Banco de Dados

O banco de dados é composto pelas seguintes collections principais:

### 📁 `usuarios`
Representa usuários do sistema (usuário comum, administrador da empresa e administrador do sistema), utilizando um campo discriminador para substituir herança do modelo relacional.

### 📁 `leads`
Representa entidades do tipo Lead, contendo informações de contato e endereço.

### 📁 `companies`
Representa empresas cadastradas, utilizada para fins de demonstração de operações CRUD.

### 📁 `searches`
Representa pesquisas realizadas, funcionando como uma agregação que associa usuários e leads, incluindo atributos do relacionamento.

---

## 🔧 Funcionalidades Implementadas

A aplicação implementa operações CRUD (Create, Read, Update e Delete) para as seguintes estruturas:

- Usuários
- Leads
- Empresas
- Pesquisas (relacionamento/agregação)

Todas as operações são executadas através de uma aplicação desenvolvida em **Python**, utilizando a biblioteca `pymongo`.

---

## 🐍 Tecnologias Utilizadas

- Python 3.x
- MongoDB Atlas
- Biblioteca `pymongo`

---


## ▶️ Como Executar o Projeto

1. Clonar o repositório:
   ```bash
   git clone <LINK_DO_GITHUB_AQUI>


## 👨‍🎓 Autor

- **Luis Felipe Ramalho Carvalho**  
- Universidade Federal de Sergipe  
- Disciplina: Banco de Dados  
- Professor: André Britto
- Link do GitHub: https://github.com/LuisFelipeRC1/projeto-logico-banco-de-dados-ufs

