# Dashboard de acidentes rodoviários

Painel interativo em Dash inspirado na imagem `imagem/ACIDENTES_RODOVIAS.jpg`.
Ele usa os arquivos `dados_brutos/acidentes2025.csv` e
`dados_brutos/acidentes2026.csv`, com filtros por ano e UF.

## Como executar

Na raiz de `Projeto_PRF`, instale as dependências e inicie o servidor:

```bash
python -m pip install -r dashboard/requirements.txt
python dashboard/app.py
```

Depois, abra <http://localhost:8050>.

Os gráficos usam Plotly, que é o mecanismo de visualização integrado ao Dash,
e seguem a composição visual da referência: fundo escuro, amarelo de destaque,
cartões de indicadores e ranking horizontal.
