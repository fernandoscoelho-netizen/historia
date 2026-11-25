#!/usr/bin/env python3
"""Gera projetos.json com as pastas do repositório e os ficheiros de cada uma.

Usado pela GitHub Action «Atualizar índice de projetos», mas também pode ser
corrido à mão na raiz do repositório:  python .github/gerar_projetos.py
"""
import json, os
from datetime import datetime, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IGNORAR = {"info.txt", "readme.md", "license", ".gitkeep", "desktop.ini", "thumbs.db"}
PASTAS_IGNORADAS = {".github", ".git", "assets", "node_modules"}

def ler_info(caminho):
    try:
        with open(caminho, encoding="utf-8-sig") as f:
            linhas = [l.strip() for l in f.read().splitlines()]
    except (OSError, UnicodeDecodeError):
        return {}
    while linhas and not linhas[0]:
        linhas.pop(0)
    if not linhas:
        return {}
    info = {"titulo": linhas[0]}
    resto = " ".join(l for l in linhas[1:] if l).strip()
    if resto:
        info["descricao"] = resto
    return info

pastas = []
for pasta in sorted(os.listdir(RAIZ)):
    caminho = os.path.join(RAIZ, pasta)
    if not os.path.isdir(caminho) or pasta.startswith(".") or pasta in PASTAS_IGNORADAS:
        continue
    ficheiros = []
    for atual, subpastas, nomes in os.walk(caminho):
        subpastas[:] = [d for d in subpastas if not d.startswith(".")]
        rel = os.path.relpath(atual, caminho)
        for nome in sorted(nomes):
            if nome.startswith(".") or nome.lower() in IGNORAR:
                continue
            # ficheiros da própria pasta; nas subpastas só os index.html
            if rel != "." and nome.lower() != "index.html":
                continue
            nome_rel = nome if rel == "." else f"{rel}/{nome}".replace(os.sep, "/")
            ficheiros.append({
                "nome": nome_rel,
                "caminho": f"{pasta}/{nome_rel}",
                "tamanho": os.path.getsize(os.path.join(atual, nome)),
            })
    entrada = {"pasta": pasta, **ler_info(os.path.join(caminho, "info.txt")), "ficheiros": ficheiros}
    pastas.append(entrada)

dados = {"gerado": datetime.now(timezone.utc).isoformat(timespec="seconds"), "pastas": pastas}
destino = os.path.join(RAIZ, "projetos.json")
# só reescreve se a lista mudou (evita commits vazios)
try:
    with open(destino, encoding="utf-8") as f:
        antigo = json.load(f)
    if antigo.get("pastas") == pastas:
        print("projetos.json já está atualizado.")
        raise SystemExit(0)
except (OSError, ValueError):
    pass
with open(destino, "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=2)
    f.write("\n")
print(f"projetos.json: {len(pastas)} pastas, {sum(len(p['ficheiros']) for p in pastas)} ficheiros.")
