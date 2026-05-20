Sistema de Gestión de Citas Médicas - Persistencia Políglota
Universidad El Bosque - Bases de Datos II

Este repositorio contiene la arquitectura de persistencia de datos (SQL y NoSQL) para un sistema hospitalario.

Equipo de Desarrollo
Juan Camilo Beltrán Navarro
Diego Andrés Bonza Figueroa
Juan Pablo Cuervo Rodríguez
Juan David González Hernández

🛠 Tecnologías Utilizadas
Núcleo Transaccional: PostgreSQL (Modelo Relacional 3FN - Principios ACID).
Almacén Clínico: MongoDB (Modelo Documental - Principios BASE).
Integración: Python (psycopg2 y pymongo).

Estructura del Repositorio
/sql/: Scripts DDL (creación de tablas), DML (50 registros de prueba), consultas, triggers y procedimientos almacenados.
/nosql/: Scripts JSON de poblamiento de historias clínicas y consultas de agregación.
/integracion/: Script sincronizador en Python.
