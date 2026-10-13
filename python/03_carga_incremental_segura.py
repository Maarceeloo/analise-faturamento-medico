"""Carga incremental segura para Projeto_Faturamento_Medico.
Por padrão SOMENTE SIMULA; use --aplicar para gravar após conferir a prévia.
Requer: pip install pandas pyodbc. Arquivos CSV UTF-8, separados por ponto e vírgula.
"""
import argparse
import hashlib
from pathlib import Path
import pandas as pd
import pyodbc

# Reaproveita conversões já utilizadas no projeto; manter este arquivo na pasta python/.
from importlib.util import spec_from_file_location, module_from_spec

FONTES = {
    'atendimentos_particulares': ('atendimentos_particulares', ('id_atendimento',)),
    'producao_bradesco': ('faturamento_bradesco', ('numero_guia_prestador', 'sequencial_item')),
    'guias_unimed': ('faturamento_unimed', ('numero_guia_prestador', 'codigo_tuss', 'data_atendimento')),
}

def carregar_conversor():
    caminho = Path(__file__).with_name('03_carga_automatica.py')
    spec = spec_from_file_location('carga_original', caminho)
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.converter

def identificar(nome):
    for prefixo, config in FONTES.items():
        if nome.lower().startswith(prefixo.lower()) and nome.lower().endswith('.csv'):
            return config
    return None

def assinatura(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b''):
            h.update(bloco)
    return h.hexdigest()

def chave(row, colunas):
    return tuple(str(row[c]).strip() for c in colunas)

def executar(args):
    pasta = Path(args.pasta)
    if not pasta.is_dir():
        raise ValueError(f'Pasta não encontrada: {pasta}')
    arquivos = sorted(p for p in pasta.iterdir() if p.is_file() and identificar(p.name))
    if not arquivos:
        print('Nenhum CSV compatível encontrado. Prefixos:', ', '.join(FONTES))
        return
    converter = carregar_conversor()
    conexao = (f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={args.servidor};'
               f'DATABASE={args.banco};Trusted_Connection=yes;TrustServerCertificate=yes;')
    with pyodbc.connect(conexao, autocommit=False) as conn:
        cur = conn.cursor()
        for path in arquivos:
            tabela, chaves = identificar(path.name)
            digest = assinatura(path)
            cur.execute('SELECT COUNT(*) FROM v2.controle_cargas WHERE hash_arquivo=? AND status=?', digest, 'CONCLUIDA')
            if cur.fetchone()[0]:
                print(f'IGNORADO (arquivo já processado): {path.name}')
                continue
            df = pd.read_csv(path, sep=';', dtype=str, encoding='utf-8-sig', keep_default_na=False)
            if df.empty:
                raise ValueError(f'Arquivo vazio: {path.name}')
            cur.execute('SELECT c.name, ty.name FROM sys.columns c JOIN sys.types ty ON c.user_type_id=ty.user_type_id WHERE c.object_id=OBJECT_ID(?) ORDER BY c.column_id', f'v2.{tabela}')
            colunas = cur.fetchall()
            nomes = [c[0] for c in colunas]
            if set(df.columns) != set(nomes):
                raise ValueError(f'{path.name}: colunas faltantes {sorted(set(nomes)-set(df.columns))}; extras {sorted(set(df.columns)-set(nomes))}')
            df = df[nomes]
            for c in chaves:
                if df[c].astype(str).str.strip().eq('').any():
                    raise ValueError(f'{path.name}: chave vazia em {c}')
            # Compara chaves no formato SQL convertido (datas, números), não texto bruto do CSV.
            convertidas = {nome: converter(df[nome], tipo, nome) for nome, tipo in colunas}
            linhas = list(zip(*(convertidas[n] for n in nomes)))
            indices = [nomes.index(c) for c in chaves]
            def chave_sql(linha):
                return tuple(linha[i] for i in indices)
            novas_chaves = [chave_sql(r) for r in linhas]
            if len(set(novas_chaves)) != len(novas_chaves):
                raise ValueError(f'{path.name}: chaves duplicadas no próprio arquivo')
            lista_chaves = ', '.join('[' + c + ']' for c in chaves)
            cur.execute(f'SELECT {lista_chaves} FROM v2.[{tabela}]')
            existentes = set(tuple(row) for row in cur.fetchall())
            novos = [r for r in linhas if chave_sql(r) not in existentes]
            repetidos = len(linhas) - len(novos)
            print(f'{path.name}: {len(linhas)} lidos; {len(novos)} novos; {repetidos} já existentes')
            if not args.aplicar:
                continue
            # Uma transação por arquivo: inserções e histórico são confirmados juntos.
            try:
                cur.execute('INSERT INTO v2.controle_cargas (nome_arquivo, origem, hash_arquivo, registros_lidos, registros_inseridos, registros_atualizados, status, finalizado_em, mensagem) VALUES (?, ?, ?, ?, ?, 0, ?, SYSDATETIME(), ?)',
                            path.name, tabela, digest, len(linhas), len(novos), 'CONCLUIDA', f'{repetidos} registros já existentes; não atualizados')
                if novos:
                    campos = ', '.join('[' + c + ']' for c in nomes)
                    parametros = ', '.join('?' for _ in nomes)
                    sql = f'INSERT INTO v2.[{tabela}] ({campos}) VALUES ({parametros})'
                    for linha in novos:
                        cur.execute(sql, linha)
                conn.commit()
                print(f'GRAVADO: {len(novos)} novos registros em v2.{tabela}')
            except Exception:
                conn.rollback()
                raise
    if not args.aplicar:
        print('SIMULAÇÃO CONCLUÍDA. Nenhum registro foi alterado. Use --aplicar somente após revisar os totais.')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--pasta', required=True, help='Pasta de entrada com arquivos CSV')
    p.add_argument('--servidor', default='PC03')
    p.add_argument('--banco', default='Projeto_Faturamento_Medico')
    p.add_argument('--aplicar', action='store_true', help='Autoriza gravar no SQL Server')
    executar(p.parse_args())
