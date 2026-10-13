"""Automação da camada financeira 2025. Não modifica tabelas originais de faturamento."""
from pathlib import Path
import argparse, importlib.util, re, sys

ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT / "sql"
GENERATOR = ROOT / "python" / "gerar_e_carregar_despesas_2025.py"

def batches(path):
    sql=path.read_text(encoding='utf-8-sig')
    return [s.strip() for s in re.split(r'^\s*GO\s*(?:--[^\n]*)?$',sql,flags=re.I|re.M) if s.strip()]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--servidor',default='PC03')
    parser.add_argument('--banco',default='Projeto_Faturamento_Medico')
    parser.add_argument('--confirmar',action='store_true',help='Autoriza substituir dados da tabela v2.Despesas, se já existirem')
    args=parser.parse_args()
    try: import pyodbc
    except ImportError:
        print('ERRO: pyodbc não instalado. Execute: py -m pip install pyodbc');return 1
    if not GENERATOR.exists():
        print('ERRO: script de geração ausente:',GENERATOR);return 1
    spec=importlib.util.spec_from_file_location('financeiro2025',GENERATOR)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    try:
        rows=mod.generate()
        if len(rows)!=265 or {r['data_competencia'][:7] for r in rows}!={f'2025-{m:02}' for m in range(1,13)}:
            raise ValueError('Base de despesas não passou na conferência de 265 registros e 12 meses')
        drivers=pyodbc.drivers()
        driver=next((d for d in ('ODBC Driver 18 for SQL Server','ODBC Driver 17 for SQL Server') if d in drivers),None)
        if not driver: raise RuntimeError('Instale o Microsoft ODBC Driver 17 ou 18 para SQL Server')
        conn=f'DRIVER={{{driver}}};SERVER={args.servidor};DATABASE={args.banco};Trusted_Connection=yes;TrustServerCertificate=yes;Encrypt=optional;'
        with pyodbc.connect(conn,autocommit=False,timeout=15) as cn:
            cur=cn.cursor()
            cur.execute("SELECT DB_NAME()"); actual=cur.fetchone()[0]
            if actual.lower()!=args.banco.lower():raise RuntimeError('Banco incorreto: '+actual)
            # Preflight: conferir colunas antes de qualquer escrita.
            dependencies = {
                'v2.vw_faturamento_consolidado': [
                    'operadora','id_registro','data_atendimento','data_prevista_pagamento',
                    'valor_apresentado','valor_pago','valor_glosado','elegivel_cobranca',
                    'status_padronizado','data_pagamento'
                ],
            }
            for obj, fields in dependencies.items():
                cur.execute('SELECT OBJECT_ID(?)',obj)
                if cur.fetchone()[0] is None:
                    raise RuntimeError(f'View obrigatória ausente: {obj}. Nenhuma alteração foi realizada.')
                cur.execute('SELECT name FROM sys.columns WHERE object_id=OBJECT_ID(?)',obj)
                found={r[0].lower() for r in cur.fetchall()}
                missing=[f for f in fields if f.lower() not in found]
                if missing:
                    raise RuntimeError(f'{obj} sem colunas necessárias: {missing}. Nenhuma alteração foi realizada.')
            cur.execute("SELECT OBJECT_ID(N'v2.Despesas',N'U')")
            exists=cur.fetchone()[0] is not None
            if exists:
                cur.execute('SELECT COUNT(*) FROM v2.Despesas')
                current=cur.fetchone()[0]
                if current and not args.confirmar:
                    raise RuntimeError(f'v2.Despesas já contém {current} linhas. Nada foi alterado. Para substituir conscientemente, execute com --confirmar.')
            for file in ('01_criar_despesas_v2.sql',):
                for batch in batches(SQL_DIR/file):cur.execute(batch)
            cn.commit()
            print('Tabela v2.Despesas pronta')
            # Carga com rollback em caso de erro; somente a tabela v2.Despesas é substituída.
            mod.load(rows,args.servidor,args.banco)
            for file in ('02_criar_previsoes_v2.sql','04_indicadores_sql_2025.sql'):
                for batch in batches(SQL_DIR/file):cur.execute(batch)
                cn.commit();print('Criado:',file)
            print('\nVALIDAÇÃO AUTOMÁTICA')
            cur.execute('SELECT COUNT(*), COUNT(DISTINCT id_despesa), COUNT(DISTINCT MONTH(data_competencia)) FROM v2.Despesas')
            count,unique,months=cur.fetchone()
            print('Despesas:',count,'IDs:',unique,'meses:',months)
            if (count,unique,months)!=(265,265,12):raise RuntimeError('Falha de validação das despesas')
            cur.execute('SELECT COUNT(*) FROM v2.Despesas WHERE YEAR(data_competencia)<>2025 OR YEAR(data_vencimento)<>2025 OR (data_pagamento IS NOT NULL AND YEAR(data_pagamento)<>2025)')
            if cur.fetchone()[0]:raise RuntimeError('Existem datas de despesas fora de 2025')
            cur.execute('SELECT COUNT(*) FROM v2.vw_fluxo_financeiro_mensal')
            if cur.fetchone()[0]!=12:raise RuntimeError('View mensal não retornou 12 meses')
            cur.execute('SELECT COUNT(*) FROM v2.Contas_Futuras')
            print('Contas previstas:',cur.fetchone()[0]);print('View mensal: 12 meses')
            print('\nSUCESSO: camada financeira SQL preparada. Power BI ainda exige atualização local.')
        return 0
    except Exception as e:
        print('\nERRO:',e)
        print('A automação parou. Verifique o erro antes de tentar novamente.')
        return 1
if __name__=='__main__':sys.exit(main())
