"""Carga inicial 2025 (snapshot) para tabelas v2 no SQL Server.

Executar no Windows: python 03_carga_inicial_2025.py --pasta "C:\\...\\data\\raw\\2025" --servidor PC03 --banco Projeto_Faturamento_Medico
Instalar: pip install pandas pyodbc
IMPORTANTE: substitui integralmente as linhas de CADA tabela v2, não toca nas dbo.
Não é ainda carga incremental; executar novamente repõe o snapshot sem duplicá-lo.
"""
import argparse
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
import pandas as pd
import pyodbc

ARQUIVOS = {
    'atendimentos_particulares_2025.csv': 'atendimentos_particulares',
    'producao_bradesco_2025.csv': 'faturamento_bradesco',
    'guias_unimed_2025.csv': 'faturamento_unimed',
}

def dinheiro(valor):
    if pd.isna(valor) or str(valor).strip() in ('', '-'):
        return None
    s = re.sub(r'[^\d,.-]', '', str(valor).strip())
    if ',' in s:
        s = s.replace('.', '').replace(',', '.')
    try:
        return Decimal(s)
    except InvalidOperation as exc:
        raise ValueError(f'Valor monetario invalido: {valor!r}') from exc

def converter(serie, tipo, nome):
    tipo = tipo.lower()
    if tipo in ('money','smallmoney','decimal','numeric'):
        return [dinheiro(v) for v in serie]
    if tipo in ('date','datetime','datetime2','smalldatetime'):
        out = pd.to_datetime(serie.replace('', pd.NA), dayfirst=True, errors='coerce')
        invalid = serie.notna() & serie.astype(str).str.strip().ne('') & out.isna()
        if invalid.any():
            raise ValueError(f'Data invalida na coluna {nome}: {serie[invalid].iloc[0]!r}')
        return [None if pd.isna(v) else v.to_pydatetime() for v in out]
    if tipo == 'time':
        return [None if pd.isna(v) or str(v).strip()=='' else str(v).strip() for v in serie]
    if tipo in ('int','bigint','smallint','tinyint','float','real'):
        vals = pd.to_numeric(serie.replace('', pd.NA).astype('string').str.replace(',','.',regex=False), errors='coerce')
        invalid = serie.notna() & serie.astype(str).str.strip().ne('') & vals.isna()
        if invalid.any():
            raise ValueError(f'Numero invalido na coluna {nome}: {serie[invalid].iloc[0]!r}')
        if tipo in ('int','bigint','smallint','tinyint'):
            if (vals.dropna() % 1 != 0).any(): raise ValueError(f'Inteiro invalido: {nome}')
            if tipo=='tinyint' and ((vals.dropna()<0)|(vals.dropna()>255)).any(): raise ValueError(f'Valor fora de tinyint: {nome}')
            return [None if pd.isna(v) else int(v) for v in vals]
        return [None if pd.isna(v) else float(v) for v in vals]
    return [None if pd.isna(v) or str(v).strip()=='' else str(v) for v in serie]

def executar(args):
    pasta = Path(args.pasta)
    connstr = (f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={args.servidor};'
               f'DATABASE={args.banco};Trusted_Connection=yes;TrustServerCertificate=yes;')
    try:
        conn = pyodbc.connect(connstr, autocommit=False)
    except pyodbc.Error as e:
        raise RuntimeError('Falha na conexao. Confira servidor, banco e ODBC Driver 17.') from e
    try:
        cur = conn.cursor()
        for arquivo, tabela in ARQUIVOS.items():
            path = pasta / arquivo
            if not path.is_file(): raise FileNotFoundError(path)
            df = pd.read_csv(path, sep=';', dtype=str, encoding='utf-8-sig', keep_default_na=False)
            if df.empty: raise ValueError(f'Arquivo vazio: {arquivo}')
            cur.execute('SELECT c.name, ty.name FROM sys.columns c JOIN sys.types ty ON c.user_type_id=ty.user_type_id WHERE c.object_id=OBJECT_ID(?) ORDER BY c.column_id', f'v2.{tabela}')
            cols = cur.fetchall()
            if not cols: raise ValueError(f'Tabela v2.{tabela} nao encontrada')
            names = [c[0] for c in cols]
            if set(df.columns) != set(names):
                raise ValueError(f'{arquivo}: faltam {sorted(set(names)-set(df.columns))}; sobram {sorted(set(df.columns)-set(names))}')
            df = df[names]
            converted = [converter(df[n],t,n) for n,t in cols]
            rows = list(zip(*converted))
            identifiers = ', '.join('['+n.replace(']',']]')+']' for n in names)
            params = ','.join('?' for _ in names)
            # Snapshot atomico de uma tabela por arquivo: rollback se falhar.
            try:
                cur.execute(f'DELETE FROM v2.[{tabela}]')
                cur.fast_executemany = True
                cur.executemany(f'INSERT INTO v2.[{tabela}] ({identifiers}) VALUES ({params})', rows)
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            print(f'OK: v2.{tabela} = {len(rows)} linhas')
        print('Carga inicial concluida. Confira totais no SSMS.')
    finally:
        conn.close()

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--pasta',required=True)
    p.add_argument('--servidor',default='PC03')
    p.add_argument('--banco',default='Projeto_Faturamento_Medico')
    executar(p.parse_args())
