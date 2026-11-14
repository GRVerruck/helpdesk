import unittest
from concurrent.futures import ThreadPoolExecutor

from api import criar_app
from helpdesk.helpdesk import HelpDesk
from helpdesk.usuarios import Administrador


class TestApi(unittest.TestCase):
    def setUp(self):
        admin = Administrador("Admin", "admin@empresa.com", "1234", "Gerente")
        sistema = HelpDesk("Empresa", admin)
        sistema.cadastrar_usuario_comum("Ana", "ana@empresa.com", "1234", "Financeiro")
        sistema.cadastrar_usuario_comum("Bruno", "bruno@empresa.com", "1234", "RH")
        sistema.cadastrar_tecnico(admin, "Carlos", "carlos@empresa.com", "1234", "Software")
        sistema.cadastrar_tecnico(admin, "Diana", "diana@empresa.com", "1234", "Software")
        self.app = criar_app(sistema)
        self.client = self.app.test_client()

    def login(self, nome):
        resposta = self.client.post("/login", json={"email": nome + "@empresa.com", "senha": "1234"})
        self.assertEqual(resposta.status_code, 200)
        return {"Authorization": "Bearer " + resposta.json["token"]}

    def abrir(self, headers):
        return self.client.post("/chamados", headers=headers, json={"titulo": "Erro no relatório",
            "descricao": "Não abre", "categoria": "SOFTWARE", "prioridade": "MEDIA"})

    def test_fluxo_entre_computadores(self):
        ana, tecnico = self.login("ana"), self.login("carlos")
        criado = self.abrir(ana)
        self.assertEqual(criado.status_code, 201)
        id = criado.json["id"]
        outro_pc = self.app.test_client()
        self.assertEqual(len(outro_pc.get("/chamados", headers=tecnico).json), 1)
        self.assertEqual(outro_pc.post(f"/chamados/{id}/assumir", headers=tecnico).status_code, 200)
        resposta = outro_pc.post(f"/chamados/{id}/atendimentos", headers=tecnico,
            json={"tipo": "SOLUCAO", "descricao": "Filtro corrigido", "novo_status": "RESOLVIDO"})
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(self.client.get(f"/chamados/{id}", headers=ana).json["status"], "RESOLVIDO")
        self.assertEqual(len(self.client.get(f"/chamados/{id}/atendimentos", headers=ana).json), 2)

    def test_acesso_e_validacao(self):
        self.assertEqual(self.client.get("/chamados").status_code, 401)
        ana, bruno = self.login("ana"), self.login("bruno")
        id = self.abrir(ana).json["id"]
        self.assertEqual(self.client.get(f"/chamados/{id}", headers=bruno).status_code, 404)
        self.assertEqual(self.client.post("/usuarios", headers=ana, json={}).status_code, 403)
        self.assertEqual(self.client.post("/chamados", headers=ana, json=[]).status_code, 400)
        self.assertEqual(self.client.post("/logout", headers=ana).status_code, 204)
        self.assertEqual(self.client.get("/chamados", headers=ana).status_code, 401)

    def test_dois_tecnicos_assumem_o_mesmo_chamado(self):
        ana = self.login("ana")
        tecnicos = [self.login("carlos"), self.login("diana")]
        id = self.abrir(ana).json["id"]
        def assumir(headers):
            with self.app.test_client() as client:
                return client.post(f"/chamados/{id}/assumir", headers=headers).status_code
        with ThreadPoolExecutor(max_workers=2) as executor:
            resultados = list(executor.map(assumir, tecnicos))
        self.assertEqual(sorted(resultados), [200, 404])

    def test_cadastro_e_cancelamento(self):
        admin = self.login("admin")
        resposta = self.client.post("/usuarios", headers=admin, json={"nome": "Eva",
            "email": "eva@empresa.com", "senha": "1234", "perfil": "comum", "setor": "Vendas"})
        self.assertEqual(resposta.status_code, 201)
        eva = self.login("eva")
        id = self.abrir(eva).json["id"]
        self.assertEqual(self.client.post(f"/chamados/{id}/cancelar", headers=eva).json["status"], "CANCELADO")


if __name__ == "__main__":
    unittest.main()
