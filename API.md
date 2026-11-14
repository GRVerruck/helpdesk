# API do Help Desk

O servidor compartilha uma instância de HelpDesk entre os aplicativos Tkinter.
Os dados e as sessões ficam em memória. Reiniciar o servidor apaga ambos.
As regras continuam nas classes existentes. A API converte requisições e respostas em JSON.

## Executar

Requer Python 3.10 ou superior.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:ADMIN_EMAIL = "admin@empresa.com"
$env:ADMIN_SENHA = "escolha-uma-senha"
python servidor.py
```

O servidor escuta na porta 8000; a variável PORT permite mudar a porta.
Em outro computador, use http://IP-DO-SERVIDOR:8000.
Em hospedagem Python, configure instalação `pip install -r requirements.txt`,
início `python servidor.py` e as variáveis ADMIN_EMAIL e ADMIN_SENHA.
Use o endereço HTTPS fornecido pela hospedagem.

Execute **um único processo e uma única instância**. Vários processos teriam
memórias separadas. Waitress atende as conexões; uma trava coordena o acesso ao modelo.
Não use múltiplos workers, réplicas ou recarga automática.

## Login e uso

POST /login recebe `{"email":"admin@empresa.com","senha":"sua-senha"}`.
A resposta contém token e usuário. Nas próximas requisições envie
`Authorization: Bearer SEU_TOKEN`. A sessão dura 8 horas. POST /logout a encerra.
O administrador cadastra as contas usadas nos outros computadores.
Senhas são enviadas exatamente como digitadas; evite espaços nas extremidades.

| Método | Caminho | Uso |
|---|---|---|
| GET | /saude | Verificar servidor, sem login |
| POST | /login | Autenticar |
| POST | /logout | Encerrar sessão |
| POST | /usuarios | Administrador cadastra conta |
| GET | /chamados | Listar conforme o perfil |
| POST | /chamados | Abrir chamado |
| GET | /chamados/ID | Consultar chamado |
| POST | /chamados/ID/assumir | Técnico assume |
| POST | /chamados/ID/cancelar | Solicitante cancela |
| GET | /chamados/ID/atendimentos | Consultar histórico |
| POST | /chamados/ID/atendimentos | Registrar atendimento/status |

Cadastro de usuário: nome, email, senha e perfil (`comum`, `tecnico` ou
`administrador`), com setor, especialidade ou cargo, respectivamente.

Abertura:
```json
{"titulo":"Erro no relatório","descricao":"Erro ao filtrar o período","categoria":"SOFTWARE","prioridade":"MEDIA"}
```

Atendimento e resolução:
```json
{"tipo":"SOLUCAO","descricao":"Filtro corrigido","novo_status":"RESOLVIDO"}
```

Para registrar sem mudar o estado, omita novo_status. Enumerações usam seus nomes
em maiúsculas, conforme helpdesk/enums.py. Datas usam ISO 8601, no horário local do servidor.
Erros retornam `{"erro":"mensagem"}`: 400 dados inválidos, 401 sessão inválida,
403 acesso negado, 404 chamado inexistente ou não visível, 409 regra de negócio.

Na futura interface, consulte GET /chamados periodicamente e faça as chamadas de
rede fora da thread da janela para não travar o Tkinter. A identidade vem do token,
não de um ID de usuário enviado pelo cliente.

## Testes

```text
python -m unittest discover -s tests -v
python -m unittest test_api -v
```

Os testes da API verificam o fluxo entre clientes, privacidade, logout,
cadastro, cancelamento e disputa de dois técnicos pelo mesmo chamado.
