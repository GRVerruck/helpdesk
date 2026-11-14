import os
import secrets
from threading import RLock
from time import time

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from helpdesk.enums import Categoria, Permissao, Prioridade, StatusChamado, TipoAtendimento
from helpdesk.excecoes import HelpDeskError, PermissaoNegadaError
from helpdesk.helpdesk import HelpDesk
from helpdesk.usuarios import Administrador


def criar_app(sistema=None):
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 65536
    if sistema is None:
        senha = os.environ.get("ADMIN_SENHA")
        if not senha:
            raise ValueError("Defina ADMIN_SENHA antes de iniciar a API.")
        admin = Administrador("Administrador", os.environ.get("ADMIN_EMAIL", "admin@helpdesk.com"), senha, "Administrador")
        sistema = HelpDesk("Help Desk", admin)
    sessoes = {}
    trava = RLock()

    def usuario_json(usuario):
        return {"id": usuario.id, "nome": usuario.nome, "email": usuario.email,
                "perfil": usuario.obter_perfil()}

    def chamado_json(chamado):
        return {"id": chamado.id, "titulo": chamado.titulo, "descricao": chamado.descricao,
                "categoria": chamado.categoria.name, "prioridade": chamado.prioridade.name,
                "status": chamado.status.name, "solicitante": usuario_json(chamado.solicitante),
                "responsavel": usuario_json(chamado.responsavel) if chamado.responsavel else None,
                "data_abertura": chamado.data_abertura.isoformat(),
                "data_encerramento": chamado.data_encerramento.isoformat() if chamado.data_encerramento else None}

    def dados():
        valor = request.get_json()
        if not isinstance(valor, dict):
            raise ValueError("Envie um objeto JSON.")
        return valor

    def campo(valor, nome):
        texto = valor.get(nome)
        if not isinstance(texto, str) or not texto.strip():
            raise ValueError(f"Informe {nome}.")
        return texto.strip()

    def enumeracao(tipo, nome):
        try:
            return tipo[nome]
        except (KeyError, TypeError):
            raise ValueError(f"Valor inválido para {tipo.__name__}.")

    def chamado_visivel(id):
        for chamado in sistema.listar_chamados(request.usuario):
            if chamado.id == id:
                return chamado
        return None

    @app.before_request
    def autenticar():
        trava.acquire()
        request.trava_adquirida = True
        if request.path in ("/saude", "/login"):
            return
        token = request.headers.get("Authorization", "").removeprefix("Bearer ")
        sessao = sessoes.get(token)
        if not sessao or sessao[1] <= time() or not sessao[0].esta_ativo():
            sessoes.pop(token, None)
            return jsonify(erro="Sessão inválida ou expirada."), 401
        request.usuario = sessao[0]

    @app.teardown_request
    def liberar_trava(erro):
        if getattr(request, "trava_adquirida", False):
            request.trava_adquirida = False
            trava.release()

    @app.errorhandler(HTTPException)
    def erro_http(erro):
        return jsonify(erro=erro.description), erro.code

    @app.errorhandler(ValueError)
    def erro_validacao(erro):
        return jsonify(erro=str(erro)), 400

    @app.errorhandler(HelpDeskError)
    def erro_negocio(erro):
        return jsonify(erro=str(erro)), 403 if isinstance(erro, PermissaoNegadaError) else 409

    @app.get("/saude")
    def saude():
        return jsonify(status="ok")

    @app.post("/login")
    def login():
        valor = dados()
        email = campo(valor, "email")
        senha = valor.get("senha")
        if not isinstance(senha, str) or not senha:
            raise ValueError("Informe senha.")
        usuario = sistema.autenticar(email, senha, Permissao.ACESSAR_APLICATIVO)
        if usuario is None:
            usuario = sistema.autenticar(email, senha, Permissao.ACESSAR_PAINEL_ADMIN)
        if usuario is None:
            return jsonify(erro="E-mail ou senha inválidos."), 401
        for token, sessao in list(sessoes.items()):
            if sessao[1] <= time():
                del sessoes[token]
        token = secrets.token_urlsafe(32)
        sessoes[token] = (usuario, time() + 28800)
        return jsonify(token=token, usuario=usuario_json(usuario), expira_em_segundos=28800)

    @app.post("/logout")
    def logout():
        sessoes.pop(request.headers.get("Authorization", "").removeprefix("Bearer "), None)
        return "", 204

    @app.post("/usuarios")
    def cadastrar_usuario():
        ator = request.usuario
        if not ator.possui_permissao(Permissao.GERENCIAR_USUARIOS):
            raise PermissaoNegadaError("Somente administradores cadastram usuários pela API.")
        valor = dados()
        nome, email = campo(valor, "nome"), campo(valor, "email")
        senha = valor.get("senha")
        if not isinstance(senha, str) or not senha:
            raise ValueError("Informe senha.")
        perfil = campo(valor, "perfil")
        if perfil == "comum":
            usuario = sistema.cadastrar_usuario_comum(nome, email, senha, campo(valor, "setor"))
        elif perfil == "tecnico":
            usuario = sistema.cadastrar_tecnico(ator, nome, email, senha, campo(valor, "especialidade"))
        elif perfil == "administrador":
            usuario = sistema.cadastrar_administrador(ator, nome, email, senha, campo(valor, "cargo"))
        else:
            raise ValueError("Perfil inválido: comum, tecnico ou administrador.")
        return jsonify(usuario_json(usuario)), 201

    @app.get("/chamados")
    def listar_chamados():
        return jsonify([chamado_json(c) for c in sistema.listar_chamados(request.usuario)])

    @app.post("/chamados")
    def abrir_chamado():
        valor = dados()
        chamado = sistema.abrir_chamado(request.usuario, campo(valor, "titulo"), campo(valor, "descricao"),
                                      enumeracao(Categoria, valor.get("categoria")),
                                      enumeracao(Prioridade, valor.get("prioridade")))
        return jsonify(chamado_json(chamado)), 201

    @app.get("/chamados/<int:id>")
    def consultar_chamado(id):
        chamado = chamado_visivel(id)
        if chamado is None:
            return jsonify(erro="Chamado não encontrado."), 404
        return jsonify(chamado_json(chamado))

    @app.post("/chamados/<int:id>/assumir")
    def assumir_chamado(id):
        chamado = chamado_visivel(id)
        if chamado is None:
            return jsonify(erro="Chamado não encontrado."), 404
        if not request.usuario.possui_permissao(Permissao.ATENDER_CHAMADO):
            raise PermissaoNegadaError("Somente técnicos podem assumir chamados.")
        request.usuario.assumir_chamado(chamado)
        return jsonify(chamado_json(chamado))

    @app.post("/chamados/<int:id>/cancelar")
    def cancelar_chamado(id):
        chamado = chamado_visivel(id)
        if chamado is None:
            return jsonify(erro="Chamado não encontrado."), 404
        chamado.cancelar(request.usuario)
        return jsonify(chamado_json(chamado))

    @app.get("/chamados/<int:id>/atendimentos")
    def listar_atendimentos(id):
        chamado = chamado_visivel(id)
        if chamado is None:
            return jsonify(erro="Chamado não encontrado."), 404
        return jsonify([{"autor": usuario_json(r.autor), "tipo": r.tipo.name, "descricao": r.descricao,
                         "data_hora": r.data_hora.isoformat(), "status_anterior": r.status_anterior.name,
                         "status_novo": r.status_novo.name} for r in chamado.listar_historico()])

    @app.post("/chamados/<int:id>/atendimentos")
    def registrar_atendimento(id):
        chamado = chamado_visivel(id)
        if chamado is None:
            return jsonify(erro="Chamado não encontrado."), 404
        valor = dados()
        status = valor.get("novo_status")
        chamado.registrar_atendimento(request.usuario, enumeracao(TipoAtendimento, valor.get("tipo")),
                                      campo(valor, "descricao"), enumeracao(StatusChamado, status) if status is not None else None)
        return jsonify(chamado_json(chamado)), 201

    return app
