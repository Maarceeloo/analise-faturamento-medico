"""Validação local estática: não conecta ao banco nem altera arquivos."""
from pathlib import Path
import ast, csv, sys
root = Path(__file__).resolve().parent.parent
needed = [
    'powerbi/Dashboard_Gestao_Financeira_e_Glosas.pbix',
    'python/03_carga_incremental_segura_corrigida.py',
    'python/03_carga_automatica.py',
    'automacao/executar_carga.ps1',
    'automacao/instalar_agendamento.ps1',
    'data/raw/2025/atendimentos_particulares_2025.csv',
    'data/raw/2025/guias_unimed_2025.csv',
    'data/raw/2025/producao_bradesco_2025.csv',
]
errors=[]
for name in needed:
    if not (root/name).is_file(): errors.append('Arquivo ausente: '+name)
for p in (root/'python').glob('*.py'):
    try: ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
    except Exception as e: errors.append(str(e))
for p in (root/'data'/'raw'/'2025').glob('*.csv'):
    with p.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.reader(f,delimiter=';'); header=next(reader,[])
        if not header or len(set(header)) != len(header): errors.append('Cabeçalho inválido: '+str(p))
print('Pacote OK (checagem estática)' if not errors else '\n'.join(errors))
sys.exit(bool(errors))
