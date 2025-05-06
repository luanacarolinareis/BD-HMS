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

- **Patient**
- **Doctors**
- **Nurses**
- **Assistants**
- **...**
  
Cada entidade foi modelada com seus atributos principais e relacionamentos apropriados (chaves estrangeiras, relacionamentos N:N, etc).

## 📊 Diagrama Relacional

O diagrama da base de dados pode ser visualizado através do arquivo `Conceptual Diagram.json`, recorrendo ao [ONDA](https://onda.dei.uc.pt/v4/), representando as tabelas e os seus relacionamentos.

## 🚀 Como Executar

1. Instale o PostgreSQL e um cliente como o pgAdmin.
2. Crie uma nova base de dados no PostgreSQL.
3. Execute o script presente em `Generated DDL.txt` para criar as tabelas e triggers necessários.
4. Execute o script Python `hms-api.py` e modifique a função "db_connection()" para corresponder às especificações da base de dados criada.
5. Lance o Postman e execute o script `HMS Collection.postman_collection.json`.
6. Comece a testar o sistema!

## 📸 Capturas de Ecrã

<p align="center">
  <img src="https://github.com/user-attachments/assets/b2be2f31-c2fe-4f08-aae5-eb4d61082a05" width="1000"/>
  <img src="https://github.com/user-attachments/assets/5235f467-69f2-4356-852f-2408b1222a9a" width="1000"/>
  <img src="https://github.com/user-attachments/assets/d84b12dc-60b8-42c4-918f-5d59bd258959" width="1000"/>
  <img src="https://github.com/user-attachments/assets/fb89d58e-6587-4870-ae19-cbb52dbd99ee" width="1000"/>
  <img src="https://github.com/user-attachments/assets/dc0109b3-a508-4b70-8f8f-8cdf7a15d490" width="1000"/>
  <img src="https://github.com/user-attachments/assets/943bb3da-66f3-4357-8842-07753b086532" width="1000"/>
  <img src="https://github.com/user-attachments/assets/00a46398-b6d5-4b88-b319-263c33079fb8" width="1000"/>
</p>

## 👩‍💻 Autores

- [Carolina Reis](https://github.com/luanacarolinareis)
- Diogo Ferreira
- Rafael Silva
