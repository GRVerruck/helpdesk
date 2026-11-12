# Help Desk — Sistema de Chamados de TI

Modelagem e implementação orientadas a objetos, em Python, de um sistema interno para abertura e acompanhamento de chamados de suporte técnico e controle de estoque de equipamentos de TI.

**Instituto Federal de Educação, Ciência e Tecnologia Catarinense (IFC) — Campus Concórdia**
Curso de Ciência da Computação
Disciplina: Programação Orientada a Objetos I
Professor: Alisson Borges Zanetti
Trabalho do III Trimestre — Tema: *Sistema de Hierarquia de Usuários (Help Desk)*

## Integrantes

| Nome |
|------|
| Gabriel Verruck |
| Guilherme Bortoletti |
| Mateus Biega |
| Vinicius Begnini Felicio |

## Status do projeto

| Parte | Descrição | Prazo | Situação |
|-------|-----------|-------|----------|
| 1 | Modelagem e arquitetura conceitual (UML + relatório SBC) | 30/10/2026 | Concluída |
| 2 | Implementação em Python e testes | 13/11/2026 | Em desenvolvimento |
| 3 | Interface gráfica com Tkinter | 20/11/2026 | Planejada |
| — | Apresentações (8 a 10 minutos por grupo) | 20/11 a 27/11/2026 | Planejada |

> A Parte 2 está em andamento. A base do pacote, os usuários, os chamados e os registros de atendimento estão implementados. Estoque, testes e `main.py` seguem pendentes.

## Sumário

1. [Introdução](#1-introdução)
2. [Escopo](#2-escopo)
3. [Modelagem](#3-modelagem)
4. [Regras de negócio](#4-regras-de-negócio)
5. [Aplicação dos pilares da POO](#5-aplicação-dos-pilares-da-poo)
6. [Mapeamento UML para Python](#6-mapeamento-uml-para-python)
7. [Arquitetura e organização do código](#7-arquitetura-e-organização-do-código)
8. [Requisitos e execução](#8-requisitos-e-execução)
9. [Testes](#9-testes)
10. [Roadmap](#10-roadmap)
11. [Estrutura do repositório](#11-estrutura-do-repositório)
12. [Referências](#12-referências)

## 1. Introdução

Em ambientes corporativos, solicitações de suporte técnico costumam ser tratadas de forma informal (mensagens, e-mails, pedidos verbais), o que dificulta o rastreamento, a priorização e a mensuração do trabalho da equipe de TI. Sistemas de *help desk* resolvem esse problema ao centralizar os chamados e registrar todo o seu ciclo de vida.

O presente trabalho propõe um sistema de help desk cujo objetivo didático é a aplicação prática dos pilares da Programação Orientada a Objetos (abstração, encapsulamento, herança e polimorfismo) e das relações entre classes (associação, agregação e composição), partindo de um modelo UML e chegando a uma implementação modular em Python.

## 2. Escopo

O sistema é uma solução interna de uma empresa, composta por dois executáveis lógicos que compartilham **um único modelo de domínio**:

- **Aplicativo Principal** (`helpdesk`): usado por Usuários Comuns e Técnicos de TI.
- **Painel Administrativo** (`painel_admin`): usado exclusivamente por Administradores.

O que diferencia os dois aplicativos é a permissão exigida no login, e não a duplicação de classes.

**Dentro do escopo:** autenticação por perfil, abertura e acompanhamento de chamados, atendimento técnico com histórico, controle de estoque de equipamentos e administração de técnicos, usuários e administradores.

**Fora do escopo:** envio de e-mails, integrações externas, controle de prazos (SLA) e banco de dados. Os dados são mantidos em memória durante a execução.

## 3. Modelagem

Os diagramas foram elaborados no [draw.io](https://www.drawio.com/), e os arquivos editáveis (`.drawio`) e as exportações em PDF estão em [`docs/diagramas/`](docs/diagramas).

### 3.1 Casos de uso

O modelo possui **3 atores** e **24 casos de uso**, organizados em dois pacotes dentro da fronteira do sistema.

![Diagrama de casos de uso](docs/img/casos_de_uso.png)

| Ator | Casos de uso |
|------|--------------|
| Usuário Comum | UC01 Cadastrar conta · UC02 Abrir chamado · UC03 Consultar meus chamados · UC04 Cancelar chamado · UC06 Fazer login no aplicativo |
| Técnico de TI | UC06 Fazer login no aplicativo · UC07 Consultar fila de chamados · UC08 Assumir chamado · UC09 Atualizar status do chamado · UC12 Cadastrar equipamento · UC13 Consultar estoque · UC14 Atualizar equipamento · UC15 Dar baixa em equipamento |
| Administrador | UC16 Fazer login no painel · UC17 Cadastrar técnico · UC18 Consultar técnicos · UC19 Atualizar técnico · UC20 Excluir técnico · UC21 Bloquear/desbloquear usuário · UC22 Gerenciar administradores · UC23 Consultar chamados da empresa · UC24 Acompanhar atividades dos técnicos |

Casos de uso alcançados por relacionamento entre casos de uso:

- `«include»` de UC09 para UC10 (Registrar atendimento): toda mudança de status obrigatoriamente registra um atendimento.
- `«extend»` de UC05 (Visualizar histórico do chamado) para UC03 e UC07: comportamento opcional nas consultas.
- `«extend»` de UC11 (Registrar saída de equipamento) para UC10: ocorre apenas quando há entrega ou troca de equipamento.

**Operações CRUD**

| Entidade | Create | Read | Update | Delete |
|----------|--------|------|--------|--------|
| Chamado | UC02 | UC03, UC05, UC07, UC23 | UC08, UC09 | UC04 (cancelamento, exclusão lógica que preserva o histórico) |
| Equipamento | UC12 | UC13 | UC14, UC11 | UC15 (baixa) |
| Técnico | UC17 | UC18 | UC19 | UC20 |

### 3.2 Diagrama de classes

![Diagrama de classes](docs/img/diagrama_classes.png)

O modelo contém **10 classes** e **6 enumerações**.

| Grupo | Elementos |
|-------|-----------|
| Hierarquia de usuários | `Usuario` (abstrata), `UsuarioComum`, `Tecnico`, `Administrador` |
| Chamados | `Chamado`, `RegistroAtendimento` |
| Estoque | `Estoque`, `Equipamento`, `MovimentacaoEstoque` |
| Fachada do sistema | `HelpDesk` |
| Enumerações | `StatusChamado`, `Prioridade`, `Categoria`, `TipoAtendimento`, `TipoMovimentacao`, `Permissao` |

### 3.3 Relatório de justificativa teórica

As decisões de modelagem estão justificadas no relatório em formato SBC (LaTeX), disponível em [`docs/relatorio/`](docs/relatorio).

## 4. Regras de negócio

| Código | Regra | Método responsável |
|--------|-------|--------------------|
| RN01 | Somente o solicitante pode cancelar o chamado, e apenas enquanto o status for `ABERTO`. | `Chamado.cancelar()` |
| RN02 | Somente chamados `ABERTO` podem ser assumidos, e cada técnico pode ter no máximo 5 chamados `EM_ATENDIMENTO`. | `Tecnico.pode_assumir()` |
| RN03 | Toda mudança de status gera um `RegistroAtendimento`. Resolver exige uma `SOLUCAO` anterior ou registrada na mesma operação. | `Chamado.registrar_atendimento()` |
| RN04 | A quantidade em estoque nunca fica negativa, e equipamento baixado não pode ser movimentado. | `Equipamento.registrar_saida()` |
| RN05 | Técnico com chamados `EM_ATENDIMENTO` não pode ser excluído. | `HelpDesk.excluir_tecnico()` |
| RN06 | O autocadastro cria apenas Usuário Comum; técnicos e administradores só são cadastrados por administradores, e deve existir sempre ao menos um administrador ativo. | `HelpDesk.desativar_administrador()` |

Transições permitidas: `ABERTO → EM_ATENDIMENTO/CANCELADO`, `EM_ATENDIMENTO ↔ PENDENTE` e `EM_ATENDIMENTO/PENDENTE → RESOLVIDO`. Em atendimento ou pendente, também é possível registrar sem mudar o status. Pendentes não contam no limite de cinco; a retomada verifica o limite novamente.

## 5. Aplicação dos pilares da POO

**Abstração e herança.** `Usuario` é abstrata porque não existe um "usuário genérico" no domínio: toda pessoa é Usuário Comum, Técnico ou Administrador. A classe concentra o que é comum (dados de acesso, `autenticar()`, `bloquear()`) e declara três métodos abstratos: `obter_perfil()`, `listar_permissoes()` e `pode_visualizar()`. As três subclasses concretas acrescentam apenas o que é próprio de cada perfil. Os tipos de registro e de movimentação foram modelados como enumerações, e não como subclasses, pois variam apenas os dados e não o comportamento, o que evita uma herança artificial.

**Encapsulamento.** Os atributos seguem a notação de visibilidade da UML: `-` (privado), `#` (protegido) e `+` (público). Dados sujeitos a regras, como `senha_hash`, `status` e `quantidade`, são privados e só se alteram por métodos que validam as regras de negócio. Por exemplo, o status de um chamado só muda por `registrar_atendimento()`, que utiliza o método privado `validar_transicao()`.

**Polimorfismo.** As subclasses de `Usuario` sobrescrevem os métodos abstratos. `possui_permissao()` delega a `listar_permissoes()`, que retorna um conjunto distinto em cada subclasse; assim, `HelpDesk.autenticar()` verifica a permissão exigida por cada aplicativo sem testar o tipo do objeto. Da mesma forma, `pode_visualizar(chamado)` permite que `HelpDesk.listar_chamados()` atenda a todos os perfis com o mesmo código.

**Relações entre classes.** Foram consideradas relações todo-parte, em número de seis.

| Relação | Tipo | Justificativa |
|---------|------|---------------|
| `HelpDesk` ◆ `Chamado` | Composição | Chamados são criados apenas por `abrir_chamado()` e não existem fora do sistema. |
| `HelpDesk` ◆ `Estoque` | Composição | O estoque nasce junto com o sistema. |
| `Chamado` ◆ `RegistroAtendimento` | Composição | O histórico pertence ao chamado. |
| `Equipamento` ◆ `MovimentacaoEstoque` | Composição | As movimentações são geradas pelo próprio equipamento. |
| `HelpDesk` ◇ `Usuario` | Agregação | O usuário é criado e depois incluído no cadastro; um técnico excluído continua referenciado em registros antigos. |
| `Estoque` ◇ `Equipamento` | Agregação | O equipamento é um bem físico criado fora do estoque e apenas adicionado a ele. |

As demais ligações (*solicita*, *atende*, *autor*, *responsável* e *referencia*) são **associações**, pois não há relação todo-parte. A associação *atende* tem multiplicidade `0..1` porque um chamado recém-aberto ainda não possui responsável.

## 6. Mapeamento UML para Python

| Conceito no modelo | Implementação prevista em Python |
|--------------------|----------------------------------|
| Classe abstrata e método abstrato | `abc.ABC` e `@abstractmethod` |
| Atributo privado (`-`) | Prefixo `__` (com *name mangling*) |
| Atributo protegido (`#`) | Prefixo `_` |
| *Getters* e *setters* (omitidos do diagrama) | `@property` e `@<atributo>.setter`, com validação |
| Enumerações | `enum.Enum` |
| Dicas de tipo (`list[Chamado]`, `Tecnico \| None`) | *Type hints* nativos (Python 3.10 ou superior) |
| Associação com classes de outros módulos (`chamado: Chamado`) | Parâmetro sem dica de tipo, para evitar importação circular entre `usuarios.py` e `chamados.py` |
| Violação de regra de negócio | Exceções próprias, definidas em `excecoes.py` |
| Hash de senha (`gerar_hash`) | Módulo `hashlib` da biblioteca padrão |

## 7. Arquitetura e organização do código

O projeto utiliza **somente Python e a biblioteca padrão**, sem dependências externas. O código é dividido por responsabilidade:

| Arquivo | Responsabilidade |
|---------|------------------|
| `helpdesk/enums.py` | Enumerações do domínio (`StatusChamado`, `Prioridade`, `Permissao` etc.). |
| `helpdesk/excecoes.py` | Exceções específicas das regras de negócio (uma por violação relevante). |
| `helpdesk/usuarios.py` | Hierarquia de usuários: `Usuario` (abstrata), `UsuarioComum`, `Tecnico` e `Administrador`. |
| `helpdesk/chamados.py` | `Chamado` e `RegistroAtendimento`. |
| `helpdesk/estoque.py` | `Estoque`, `Equipamento` e `MovimentacaoEstoque`. |
| `helpdesk/servicos.py` | Classe `HelpDesk`, que coordena os casos de uso e aplica as regras entre objetos. |
| `main.py` | Script de demonstração: instancia objetos, executa cenários e exibe os resultados. |
| `tests/` | Testes automatizados das regras de negócio (RN01 a RN06). |

**Decisões de implementação que não foram detalhadas no diagrama**

- **Primeiro administrador:** o `HelpDesk` é criado com `HelpDesk(nome_empresa, admin_inicial)`. O administrador é instanciado fora e incluído no cadastro (agregação), garantindo desde o início a RN06 (sempre existe ao menos um administrador ativo).
- **Identificador dos usuários:** é gerado automaticamente por um contador da classe `Usuario` e é atribuído somente depois que nome, e-mail e senha forem validados.
- **Validações:** nome e especialidade não podem ser vazios, o e-mail precisa ter formato válido (é armazenado em minúsculas e não pode se repetir no sistema) e a senha deve ter pelo menos 4 caracteres.
- **Desativação de administrador:** é feita por meio do bloqueio (`bloquear()`), e o mesmo limite da RN06 vale para `alterar_bloqueio()`.
- **Métodos privados auxiliares no `HelpDesk`:** `__verificar_permissao()`, que exige que o usuário esteja cadastrado, ativo e tenha a permissão da operação, e `__verificar_cadastro()`, que impede operar sobre usuários fora do sistema.
- **`__str__` em `Usuario`:** exibe id, nome, e-mail, perfil e situação, para facilitar a saída no console.
- **Autor do registro:** usa `Usuario` para identificar o solicitante no cancelamento. Atendimentos técnicos exigem o técnico responsável e ativo. Essa alteração ainda precisa ser refletida no UML e no relatório.
- **Atribuição:** `Tecnico.assumir_chamado()` chama `Chamado.atribuir_tecnico()`. Após validar, o chamado usa `_adicionar_chamado()` para atualizar a lista do técnico uma única vez.
- **Histórico e encerramento:** atribuição e cancelamento geram observações automáticas. Resolver ou cancelar define a data de encerramento e impede novos registros.

Na Parte 3, a interface em Tkinter será uma camada separada que apenas chama métodos de `HelpDesk`. Nenhuma regra de negócio ficará no código da interface.

## 8. Requisitos e execução

**Requisitos**

- Python 3.10 ou superior
- Nenhuma biblioteca externa (Tkinter acompanha a instalação padrão do Python e só será necessário na Parte 3)

**Obtenção do código**

```bash
git clone git@github.com:GRVerruck/helpdesk.git
cd helpdesk
```

**Execução da demonstração** *(disponível após a implementação da Parte 2)*

```bash
python main.py
```

## 9. Testes

Os testes utilizam o módulo `unittest` da biblioteca padrão e cobrem cada regra de negócio, tanto o caminho válido quanto a violação esperada.

```bash
python -m unittest discover -s tests -v
```

| Regra | Cenários previstos |
|-------|--------------------|
| RN01 | Cancelar com status `ABERTO` pelo solicitante; recusar por outro usuário; recusar com status diferente de `ABERTO`. |
| RN02 | Assumir chamado `ABERTO`; recusar chamado em outro status; recusar o sexto chamado simultâneo. |
| RN03 | Mudança de status gera registro; `RESOLVIDO` sem registro `SOLUCAO` é recusado. |
| RN04 | Saída com quantidade suficiente; recusar saída que deixaria o estoque negativo; recusar movimentação de equipamento baixado. |
| RN05 | Excluir técnico sem chamados em atendimento; recusar com chamados `EM_ATENDIMENTO`. |
| RN06 | Autocadastro gera apenas Usuário Comum; recusar cadastro de técnico por não administrador; manter ao menos um administrador ativo. |

## 10. Roadmap

- [x] Diagrama de casos de uso
- [x] Diagrama de classes
- [x] Relatório de justificativa teórica (formato SBC)
- [x] Enumerações e exceções
- [x] Hierarquia de usuários (classe abstrata, subclasses, `@property`)
- [x] `Chamado` e `RegistroAtendimento`
- [ ] `Estoque`, `Equipamento` e `MovimentacaoEstoque`
- [x] Classe `HelpDesk`: cadastro e administração de usuários (RN05 e RN06)
- [x] Classe `HelpDesk`: abertura e consulta de chamados
- [ ] Classe `HelpDesk`: integração com estoque
- [ ] Testes das regras RN01 a RN06
- [ ] `main.py` de demonstração
- [ ] Interface gráfica com Tkinter (Parte 3)

## 11. Estrutura do repositório

Estrutura-alvo ao final da Parte 2:

```
.
├── .gitignore
├── README.md
├── main.py
├── helpdesk/
│   ├── __init__.py
│   ├── enums.py
│   ├── excecoes.py
│   ├── usuarios.py
│   ├── chamados.py
│   ├── estoque.py
│   └── servicos.py
├── tests/
│   ├── __init__.py
│   ├── test_chamado.py
│   ├── test_estoque.py
│   └── test_helpdesk.py
└── docs/
    ├── img/
    │   ├── casos_de_uso.png
    │   └── diagrama_classes.png
    ├── diagramas/
    │   ├── casos_de_uso_helpdesk.drawio
    │   ├── casos_de_uso_helpdesk.pdf
    │   ├── diagrama_classes_helpdesk.drawio
    │   └── diagrama_classes_helpdesk.pdf
    └── relatorio/
        ├── relatorio_helpdesk.tex
        ├── sbc-template.sty
        └── relatorio_helpdesk.pdf
```

## 12. Referências

- ZANETTI, A. B. *Programação Orientada a Objetos I — Trabalho III Trimestre*. Instituto Federal Catarinense, Campus Concórdia, 2026.
- OBJECT MANAGEMENT GROUP. *Unified Modeling Language (UML) Specification*. Disponível em: <https://www.omg.org/spec/UML>.
- PYTHON SOFTWARE FOUNDATION. *abc — Abstract Base Classes*. Disponível em: <https://docs.python.org/3/library/abc.html>.
- PYTHON SOFTWARE FOUNDATION. *Built-in Functions: property*. Disponível em: <https://docs.python.org/3/library/functions.html#property>.
- PYTHON SOFTWARE FOUNDATION. *unittest — Unit testing framework*. Disponível em: <https://docs.python.org/3/library/unittest.html>.
- SOCIEDADE BRASILEIRA DE COMPUTAÇÃO. *SBC Conferences Template*.

---

Projeto acadêmico desenvolvido para fins didáticos na disciplina de Programação Orientada a Objetos I, IFC — Campus Concórdia.
