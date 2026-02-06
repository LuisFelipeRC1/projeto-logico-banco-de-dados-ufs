CREATE SCHEMA IF NOT EXISTS new_schema1;
SET search_path TO new_schema1;

-- =========================
-- Empresa
-- =========================
CREATE TABLE Empresa (
    idEmpresa SERIAL PRIMARY KEY,
    nome_da_empresa VARCHAR(180),
    cnpj VARCHAR(18) UNIQUE,
    quantidade_de_funcionarios INT,
    data_de_cadastro TIMESTAMP
);

-- =========================
-- Usuario
-- =========================
CREATE TABLE Usuario (
    idUsuario SERIAL PRIMARY KEY,
    nome VARCHAR(180),
    email VARCHAR(180) UNIQUE,
    senha VARCHAR(255),
    data_de_criacao TIMESTAMP,
    idEmpresa INT,
    CONSTRAINT fk_usuario_empresa
        FOREIGN KEY (idEmpresa)
        REFERENCES Empresa(idEmpresa)
        ON DELETE CASCADE
);

-- =========================
-- Especializações
-- =========================
CREATE TABLE Usuario_Comum (
    idUsuario INT PRIMARY KEY,
    CONSTRAINT fk_usuario_comum
        FOREIGN KEY (idUsuario)
        REFERENCES Usuario(idUsuario)
        ON DELETE CASCADE
);

CREATE TABLE Admin_do_Sistema (
    idUsuario INT PRIMARY KEY,
    CONSTRAINT fk_admin_sistema
        FOREIGN KEY (idUsuario)
        REFERENCES Usuario(idUsuario)
        ON DELETE CASCADE
);

CREATE TABLE Admin_da_Empresa (
    idUsuario INT PRIMARY KEY,
    CONSTRAINT fk_admin_empresa
        FOREIGN KEY (idUsuario)
        REFERENCES Usuario(idUsuario)
        ON DELETE CASCADE
);

-- =========================
-- Integracao
-- =========================
CREATE TABLE Integracao (
    idIntegracao SERIAL PRIMARY KEY,
    chave_api VARCHAR(180),
    tipo_de_integracao VARCHAR(45),
    idEmpresa INT NOT NULL,
    CONSTRAINT fk_integracao_empresa
        FOREIGN KEY (idEmpresa)
        REFERENCES Empresa(idEmpresa)
        ON DELETE CASCADE
);

-- =========================
-- Pagamento
-- =========================
CREATE TABLE Pagamento (
    idPagamento SERIAL PRIMARY KEY,
    valor DECIMAL(10,2),
    data_de_pagamento TIMESTAMP,
    tipo_de_pagamento VARCHAR(45),
    idEmpresa INT,
    CONSTRAINT fk_pagamento_empresa
        FOREIGN KEY (idEmpresa)
        REFERENCES Empresa(idEmpresa)
        ON DELETE CASCADE
);

-- =========================
-- Log de acesso
-- =========================
CREATE TABLE Log_de_acesso (
    id_log SERIAL PRIMARY KEY,
    ip VARCHAR(180),
    data_hora TIMESTAMP,
    idUsuario INT,
    CONSTRAINT fk_log_usuario
        FOREIGN KEY (idUsuario)
        REFERENCES Usuario(idUsuario)
        ON DELETE CASCADE
);

-- =========================
-- Credito
-- =========================
CREATE TABLE Credito (
    idCredito SERIAL PRIMARY KEY,
    quantidade INT,
    data_de_validade TIMESTAMP,
    idEmpresa INT,
    CONSTRAINT fk_credito_empresa
        FOREIGN KEY (idEmpresa)
        REFERENCES Empresa(idEmpresa)
        ON DELETE CASCADE
);

-- =========================
-- Pesquisa
-- =========================
CREATE TABLE Pesquisa (
    idPesquisa SERIAL PRIMARY KEY,
    data_de_pesquisa TIMESTAMP,
    termo_de_busca VARCHAR(80),
    quantidade_de_leads INT,
    idUsuario INT,
    idCredito INT,
    CONSTRAINT fk_pesquisa_usuario
        FOREIGN KEY (idUsuario)
        REFERENCES Usuario_Comum(idUsuario),
    CONSTRAINT fk_pesquisa_credito
        FOREIGN KEY (idCredito)
        REFERENCES Credito(idCredito)
        ON DELETE CASCADE
);

-- =========================
-- Lead
-- =========================
CREATE TABLE Lead (
    idLead SERIAL PRIMARY KEY,
    nome VARCHAR(45),
    email VARCHAR(45) UNIQUE,
    endereco VARCHAR(100),
    estado VARCHAR(45),
    cidade VARCHAR(45),
    cep VARCHAR(45),
    rua VARCHAR(18),
    cnpj VARCHAR(45) UNIQUE
);

-- =========================
-- Resultado de pesquisa (N:N)
-- =========================
CREATE TABLE Resultado_de_pesquisa (
    idPesquisa INT,
    idLead INT,
    data_de_associacao TIMESTAMP,
    ordem VARCHAR(45),
    relevancia VARCHAR(45),
    PRIMARY KEY (idPesquisa, idLead),
    CONSTRAINT fk_resultado_pesquisa
        FOREIGN KEY (idPesquisa)
        REFERENCES Pesquisa(idPesquisa)
        ON DELETE CASCADE,
    CONSTRAINT fk_resultado_lead
        FOREIGN KEY (idLead)
        REFERENCES Lead(idLead)
        ON DELETE CASCADE
);
