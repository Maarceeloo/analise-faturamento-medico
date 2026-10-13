/*
Projeto: Análise de Faturamento Médico com IA
Objetivo: criar o banco de dados do projeto.
*/

IF DB_ID('Projeto_Faturamento_Medico') IS NULL
BEGIN
    CREATE DATABASE Projeto_Faturamento_Medico;
END;
GO

USE Projeto_Faturamento_Medico;
GO