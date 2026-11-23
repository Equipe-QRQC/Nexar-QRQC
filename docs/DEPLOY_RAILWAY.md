# Publicar no Railway

O repositório já traz o necessário: `railway.json` (comando de início), `scripts/railway_start.sh`
(gunicorn, volume e base de demonstração), `gunicorn` no `requirements.txt` e `.python-version`.

## Passo a passo

1. **New Project → Deploy from GitHub repo** → `Nexar-QRQC`. Em **Settings → Source**, escolha a
   branch que vai para o ar.
2. **Volume** (obrigatório para não perder dados a cada deploy): no serviço, **+ New → Volume**,
   ponto de montagem `/data`. O script detecta o volume sozinho e guarda nele o banco, a chave de
   sessão, as fotos e documentos enviados e os CADs importados.
3. **Variables**:

   | Variável | Valor |
   |---|---|
   | `SECRET_KEY` | `python -c "import secrets; print(secrets.token_hex(32))"` |
   | `ADMIN_EMAIL` | `admin@nexar.com` (ou outro) |
   | `ADMIN_PASSWORD` | senha forte — vale também para rh@, manutencao@ e operador@ da demonstração |
   | `GEMINI_API_KEY` | diagnóstico da ocorrência e assistente |
   | `OPENAI_API_KEY` | Sensor AI e inspeção de documento |
   | `SEED_DEMO` | `1` para criar a base de demonstração no primeiro início (depois pode apagar) |

4. **Settings → Networking → Generate Domain**. O endereço `https://….up.railway.app` abre no
   computador e no celular.

## Observações

- Rode com **1 réplica**: o banco é SQLite no volume.
- A **importação de CAD** precisa do conversor (`requirements-cad.txt`, ~1,1 GB), das bibliotecas
  gráficas `libgl1` e `libx11-6` e, para otimizar, do Node.js; nada disso vai na imagem padrão.
  Os modelos que já estão no repositório funcionam normalmente. O caminho recomendado é converter
  CADs novos no computador (ver [CAD_3D.md](CAD_3D.md)) e subir pelo git. Para importar pelo
  sistema no Railway, instale esses pacotes no build do serviço (comando de build e pacotes de
  sistema nas configurações do Railway) e confira o primeiro deploy: a imagem cresce bastante.
- Máquinas novas na base de demonstração só entram num banco vazio. Para um banco que já está
  em uso, cadastre a máquina em **Máquinas → Nova máquina** e escolha o modelo 3D na lista.
- Para recriar a demonstração do zero: apague `/data/qrqc.db` (ou rode
  `python scripts/seed_demo.py --forcar --sem-ia` pelo shell do Railway).
