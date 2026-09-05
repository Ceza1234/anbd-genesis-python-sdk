# ANBD-GENESIS — SDK oficial em Python

SDK não-oficialmente-publicado-no-PyPI-ainda (por enquanto, é um arquivo avulso `anbd_genesis.py` — copie para o seu projeto) para consumir a API do ANBD-GENESIS sem precisar montar `requests`/`curl` na mão.

## Instalação

pip install requests
## Uso rápido

from anbd_genesis import AnbdGenesisClient, signup

conta = signup(name="Minha Empresa")
print(conta["api_key"])

client = AnbdGenesisClient(api_key=conta["api_key"])

decisao = client.decide("Cliente pediu reembolso de pedido já entregue há 40 dias")
print(decisao.action, decisao.confidence_score, decisao.rationale)

if decisao.needs_human:
    pass