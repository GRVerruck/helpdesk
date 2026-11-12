from .excecoes import EstoqueInsuficienteError, EquipamentoBaixadoError
 
class MovimentacaoEstoque:
  def __init__(self,quantidade,motivo,responsavel,chamado = None):
    self.quantidade = quantidade
    self.motivo = motivo
    self.responsavel = responsavel
    self.chamado = chamado
  def descrever(self):
    return (f"Movimenteção de {self.quantidade} equipamentos motivo: {self.motivo} ")

class Equipamento: 
  def __init__(self,codigo,descricao,tipo,quantidade,quantidade_minima,ativo = True):
    self.codigo = codigo
    self.descricao = descricao
    self.tipo = tipo
    self.quantidade = quantidade
    self.quantidade_minima = quantidade_minima
    self.ativo = ativo
    self.movimentacoes =[] 

  def registrar_entrada (self,quantidade_Entrou,responsavel,motivo):
      if not self.ativo:
        raise EquipamentoBaixadoError("Equipamento baixado")
      self.quantidade = self.quantidade + quantidade_Entrou
      mov = MovimentacaoEstoque(quantidade_Entrou,motivo,responsavel)
      self.movimentacoes.append(mov)

  def registrar_saida (self,quantidade_saida,responsavel,motivo,chamado):

    if not self.ativo:
     raise EquipamentoBaixadoError("Equipamento baixado")
    
    if self.quantidade < quantidade_saida:
      raise EstoqueInsuficienteError("Estoque insuficiente")
    
    self.quantidade = self.quantidade - quantidade_saida

    mov_saida = MovimentacaoEstoque(quantidade_saida,motivo,responsavel,chamado)
    self.movimentacoes.append(mov_saida)


  def dar_baixa (self, responsavel,motivo):
    if not self.ativo:
      raise EquipamentoBaixadoError("Equipamento ja baixado")
    self.ativo = False
    mov_baixa = MovimentacaoEstoque(self.quantidade,motivo,responsavel)
    self.movimentacoes.append(mov_baixa)

  def atualizar_dados(self,descricao,quantidade_minima):
    self.descricao = descricao
    self.quantidade_minima = quantidade_minima

  def abaixo_do_minimo(self):
    return self.quantidade < self.quantidade_minima

  
  def listar_movimentacoes(self):
   return self.movimentacoes


 


