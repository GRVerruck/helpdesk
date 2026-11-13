from .excecoes import EstoqueInsuficienteError, EquipamentoBaixadoError
from datetime import datetime


class MovimentacaoEstoque:
  def __init__(self,quantidade,motivo,responsavel,chamado = None, ):
    self.__quantidade = quantidade
    self.__motivo = motivo
    self.__responsavel = responsavel
    self.__chamado = chamado
    self.__data_hora = datetime.now()

  @property
  def quantidade(self):
    return self.__quantidade
  @property
  def motivo(self):
    return self.__motivo
  @property
  def responsavel(self):
    return self.__responsavel
  @property
  def chamado(self):
    return self.__chamado
  @property
  def data_hora(self):
     return self.__data_hora

  def descrever(self):
    return (
      f"Movimentação de {self.quantidade} equipamentos"
      f" motivo: {self.motivo} ")

class Equipamento: 
  def __init__(self,codigo,descricao,tipo,quantidade,quantidade_minima,ativo = True):
      if not codigo:
        raise ValueError("O código não pode ser vazio")
      if not descricao:
        raise ValueError("A descrição não pode ser vazia")
      if quantidade < 0:
        raise ValueError("A quantidade não pode ser negativa")
      if quantidade_minima < 0:
        raise ValueError("A quantidade mínima não pode ser negativa")
  
      self.__codigo = codigo
      self.__descricao = descricao
      self.__tipo = tipo
      self.__quantidade = quantidade
      self.__quantidade_minima = quantidade_minima
      self.__ativo = ativo
      self.__movimentacoes =[] 

  @property
  def codigo(self):
        return self.__codigo
  @property
  def descricao(self):
        return self.__descricao
  @property
  def tipo(self):
        return self.__tipo
  @property
  def quantidade(self):
        return self.__quantidade
  @property
  def quantidade_minima(self):
        return self.__quantidade_minima
  @property
  def ativo(self):
        return self.__ativo

  def registrar_entrada (self,quantidade_Entrou,responsavel,motivo):
      if quantidade_Entrou <= 0:
         raise ValueError("A quantidade deve ser positiva")
      if not self.ativo:
        raise EquipamentoBaixadoError("Equipamento baixado")
      self.__quantidade = self.quantidade + quantidade_Entrou
      mov = MovimentacaoEstoque(quantidade_Entrou,motivo,responsavel)
      self.__movimentacoes.append(mov)

  def registrar_saida (self,quantidade_saida,responsavel,chamado):
    if quantidade_saida <= 0:
      raise ValueError("A quantidade deve ser positiva")

    if not self.ativo:
     raise EquipamentoBaixadoError("Equipamento baixado")
    
    if self.quantidade < quantidade_saida:
      raise EstoqueInsuficienteError("Estoque insuficiente")
    
    self.__quantidade = self.quantidade - quantidade_saida

    mov_saida = MovimentacaoEstoque(quantidade_saida,"saída vínculada ao chamado",responsavel,chamado)
    self.__movimentacoes.append(mov_saida)


  def dar_baixa (self, responsavel,motivo):
    if not self.ativo:
      raise EquipamentoBaixadoError("Equipamento ja baixado")
    self.__ativo = False
    mov_baixa = MovimentacaoEstoque(self.quantidade,motivo,responsavel)
    self.__movimentacoes.append(mov_baixa)

  def atualizar_dados(self,descricao,quantidade_minima):
    if not descricao:
       raise ValueError("A descrição não pode ser vazia")
    if  quantidade_minima < 0:
       raise ValueError("A quantidade mínima não pode ser negativa")
    self.__descricao = descricao
    self.__quantidade_minima = quantidade_minima

  def abaixo_do_minimo(self):
    return self.quantidade < self.quantidade_minima

  
  def listar_movimentacoes(self):
   return self.__movimentacoes.copy()

class Estoque:
    def __init__(self):
        self.__equipamentos = {}
    def cadastrar_equipamento(self, equipamento):
        if equipamento.codigo in self.__equipamentos:
            raise ValueError("Equipamento já cadastrado")
        self.__equipamentos[equipamento.codigo] = equipamento

    def buscar(self,codigo):
       return self.__equipamentos.get(codigo)
    
    def listar(self,apenas_ativos = False):
       equipamentos = list(self.__equipamentos.values())
       if apenas_ativos:
        equipamentos = [equipamento for equipamento in equipamentos if equipamento.ativo]
       return equipamentos
    
    def listar_abaixo_do_minimo(self):
       return [
          equipamento for equipamento in self.__equipamentos.values()
          if equipamento.abaixo_do_minimo()
       ]


      


 


