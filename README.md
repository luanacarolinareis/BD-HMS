# 🏥 Hospital Management System (HMS)

Este projeto consiste na modelação e implementação de um sistema de gestão hospitalar utilizando o banco de dados PostgreSQL. Inclui a criação do esquema relacional, inserção de dados e execução de queries úteis para a administração e operação de um hospital.

## 📚 Descrição

O Hospital Management System (HMS) é um projeto que visa representar, de forma simplificada, como funcionaria a estrutura de dados de um hospital num sistema de banco de dados relacional. O sistema contempla as principais entidades envolvidas num hospital, como pacientes, médicos, enfermeiros, departamentos, internações e exames.

## 🛠️ Tecnologias Utilizadas

- PostgreSQL
- Python3
- Postman
- pgAdmin (recomendado para visualização e manipulação da base de dados)

## 🧱 Entidades do Sistema

- **Paciente**
- **Médico**
- **Enfermeiro**
- **Departamento**
- **Internação**
- **Exame**

Cada entidade foi modelada com seus atributos principais e relacionamentos apropriados (chaves estrangeiras, relacionamentos N:N, etc.).

## 📊 Diagrama Relacional

O diagrama do banco de dados pode ser visualizado através do arquivo `Conceptual Diagram.json`, recorrendo ao [ONDA](https://onda.dei.uc.pt/v4/), representando as tabelas e os seus relacionamentos.

## 🚀 Como Executar

1. Instale o PostgreSQL e um cliente como o pgAdmin.
2. Crie uma nova base de dados no PostgreSQL.
3. Execute o script presente em `Generated DDL.txt` para criar as tabelas e triggers necessários.
4. Execute o script Python `hms-api.py` e modifique a função "db_connection()" para corresponder às especificações da base de dados criada.
5. Lance o Postman e execute o script `HMS Collection.postman_collection.json`.
6. Comece a testar o sistema!

## 👩‍💻 Autores

- [Carolina Reis](https://github.com/luanacarolinareis)
- Diogo Ferreira
- Rafael Silva
