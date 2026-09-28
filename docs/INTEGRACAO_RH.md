# Integração com o sistema de RH

O Nexar QRQC recebe as pessoas e as habilitações (ASO, NR-10, NR-12, NR-33, NR-35, Integração)
do sistema de RH da empresa. Com isso, admissões, mudanças de setor, desligamentos e renovações
passam a valer na conferência de documentos sem planilha.

## Como ativar

1. Em **Configurações → Integrações** (administrador), clique em **Gerar chave de integração**.
   A chave aparece uma única vez; o sistema guarda só o hash.
2. Entregue a chave à equipe de TI que cuida do sistema de RH (TOTVS, Senior, ADP ou um
   integrador/ETL). Ela configura um envio periódico (ex.: diário) para o endereço abaixo.
3. Cada envio aparece em **Últimas sincronizações** e na **Auditoria**.
4. Para cortar o acesso, clique em **Revogar**.

## O envio

```
POST https://<servidor>/api/integracao/rh/colaboradores
Authorization: Bearer <chave>
Content-Type: application/json

{
  "origem": "TOTVS Protheus",
  "modo": "parcial",
  "colaboradores": [
    {"matricula": "10234", "nome": "Marcos Pereira",
     "setor": "Manutenção", "funcao": "Mecânico", "vinculo": "CLT",
     "gestor": "Fernanda Costa", "admissao": "2021-03-15", "ativo": true,
     "qualificacoes": {"ASO": "2027-03-01", "NR-10": "2027-05-10"}}
  ]
}
```

- A pessoa é identificada pela **matrícula**; se não existe, é criada.
- Campos que não vierem não são apagados (dá para mandar só as renovações).
- `qualificacoes` traz a **data de validade** de cada habilitação (`AAAA-MM-DD` ou `DD/MM/AAAA`).
- `"modo": "completo"` marca como desligado quem não vier na lista — use no envio diário com todos.
  Trava de segurança: se a lista tiver menos da metade das pessoas ativas, nenhum desligamento é feito.
- Resposta: `{"ok": true, "recebidos": 120, "criados": 2, "atualizados": 118, "desligados": 0, "erros": []}`.
- Limite: 5.000 pessoas por envio e 30 envios por minuto.

Exemplo com `curl`:

```bash
curl -X POST https://<servidor>/api/integracao/rh/colaboradores \
  -H "Authorization: Bearer nxr_..." -H "Content-Type: application/json" \
  -d '{"origem":"teste","colaboradores":[{"matricula":"10234","nome":"Marcos Pereira","qualificacoes":{"NR-10":"2027-05-10"}}]}'
```

## LGPD

Envie só o necessário para a conferência de documentos: matrícula, nome, setor, função, vínculo,
gestor, admissão, situação e validade das habilitações. **Não envie** salário, CPF, endereço ou
dados de saúde além da validade do ASO.

## Próximos passos

- Conector direto com a API do sistema de RH usado pela empresa (depende de credenciais e da
  documentação do fornecedor).
- Importação agendada de arquivo (CSV em pasta compartilhada/SFTP), para sistemas sem API.
