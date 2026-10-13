"""Gera despesas sintéticas de 2025 a partir de referência 2026 e carrega em SQL Server.
Não altera as bases v2 de faturamento. Requer pyodbc apenas para --carregar.
Uso: python gerar_e_carregar_despesas_2025.py
     python gerar_e_carregar_despesas_2025.py --carregar
"""
from __future__ import annotations
import argparse, calendar, csv, datetime as dt, decimal, pathlib, collections

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent if HERE.name.lower() in ('python', 'scripts') else HERE
SOURCE = ROOT / 'data' / 'raw' / 'despesas_referencia_2026.csv'
DEST = ROOT / 'data' / 'processed' / 'despesas_2025.csv'
DEST.parent.mkdir(parents=True, exist_ok=True)
COLS = ['id_despesa','data_competencia','data_vencimento','data_pagamento','categoria','fornecedor','descricao','forma_pagamento','valor_previsto_rs','valor_pago_rs','status','recorrente','observacao']

def parse_date(s): return dt.date.fromisoformat(s) if s else None

def relocate(d, year, month):
    if d is None: return ''
    return dt.date(year, month, min(d.day, calendar.monthrange(year,month)[1])).isoformat()

def generate():
    with SOURCE.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f,delimiter=';'))
    assert rows and list(rows[0])==COLS, 'Estrutura do CSV de referência inesperada'
    months=collections.defaultdict(list)
    for r in rows:
        d=parse_date(r['data_competencia'])
        if not d or d.year!=2026: raise ValueError('Data de competência inválida na referência')
        months[d.month].append(r)
    if not all(months.get(m) for m in range(2,8)):
        raise ValueError('A referência não contém todos os meses de fevereiro a julho de 2026')
    output=[]
    for target_month in range(1,13):
        # Meses ausentes: replicação explícita de um mês de referência, sem alegar histórico real.
        source_month = target_month if target_month in months else (2 if target_month==1 else ((target_month-8)%6)+2)
        for base in months[source_month]:
            r=dict(base)
            competence=parse_date(base['data_competencia'])
            r['data_competencia']=relocate(competence,2025,target_month)
            # Mantém deslocamentos de dias entre competência e vencimento/pagamento,
            # inclusive se a data original cair no mês seguinte.
            anchor=dt.date(2025,target_month,min(competence.day,calendar.monthrange(2025,target_month)[1]))
            for col in ('data_vencimento','data_pagamento'):
                old=parse_date(base[col])
                r[col]=(anchor+(old-competence)).isoformat() if old else ''
            r['id_despesa']=f'DSP25-{len(output)+1:05d}'
            origin='convertido da referência 2026' if target_month==source_month else f'mês {target_month:02d} simulado com referência {source_month:02d}/2026'
            r['observacao']=((base['observacao'] or '')+' | '+origin).strip(' |')
            # Se algum vencimento/pagamento atravessar 2025, mantém integridade temporal e reporta.
            output.append(r)
    with DEST.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=COLS,delimiter=';');w.writeheader();w.writerows(output)
    print(f'Gerado {DEST.name}: {len(output)} registros; meses 01 a 12 de 2025')
    years={parse_date(r[c]).year for r in output for c in ('data_competencia','data_vencimento','data_pagamento') if r[c]}
    if years!={2025}: raise ValueError(f'Datas fora de 2025: {years}. Rever deslocamentos antes de carregar.')
    return output

def load(rows,server,database):
    try: import pyodbc
    except ImportError as e: raise SystemExit('Instale pyodbc: pip install pyodbc') from e
    drivers=pyodbc.drivers()
    driver=next((d for d in ('ODBC Driver 18 for SQL Server','ODBC Driver 17 for SQL Server') if d in drivers),None)
    if not driver: raise RuntimeError('Instale ODBC Driver 17 ou 18 for SQL Server')
    connection=(f'DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;Encrypt=optional;')
    with pyodbc.connect(connection,autocommit=False) as cn:
        cur=cn.cursor()
        try:
            cur.execute('DELETE FROM v2.Despesas')
            stmt='INSERT INTO v2.Despesas ('+','.join('['+c+']' for c in COLS)+') VALUES ('+','.join('?' for _ in COLS)+')'
            for r in rows:
                vals=[]
                for col in COLS:
                    val=r[col]
                    if col in ('data_competencia','data_vencimento','data_pagamento'): val=parse_date(val)
                    elif col in ('valor_previsto_rs','valor_pago_rs'): val=decimal.Decimal(str(val).replace(',','.')) if val not in ('',None) else None
                    elif val=='':val=None
                    vals.append(val)
                cur.execute(stmt,*vals)
            cn.commit()
        except Exception:
            cn.rollback();raise
    print(f'Carregados {len(rows)} registros em {database}.v2.Despesas')

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--carregar',action='store_true')
    ap.add_argument('--servidor',default='PC03')
    ap.add_argument('--banco',default='Projeto_Faturamento_Medico')
    args=ap.parse_args()
    rows=generate()
    if args.carregar: load(rows,args.servidor,args.banco)
