class CamadaEnlace:
    ignore_checksum = False

    def __init__(self, linhas_seriais):
        """
        Inicia uma camada de enlace com um ou mais enlaces, cada um conectado
        a uma linha serial distinta. O argumento linhas_seriais é um dicionário
        no formato {ip_outra_ponta: linha_serial}. O ip_outra_ponta é o IP do
        host ou roteador que se encontra na outra ponta do enlace, escrito como
        uma string no formato 'x.y.z.w'. A linha_serial é um objeto da classe
        PTY (vide camadafisica.py) ou de outra classe que implemente os métodos
        registrar_recebedor e enviar.
        """
        self.enlaces = {}
        self.callback = None
        # Constrói um Enlace para cada linha serial
        for ip_outra_ponta, linha_serial in linhas_seriais.items():
            enlace = Enlace(linha_serial)
            self.enlaces[ip_outra_ponta] = enlace
            enlace.registrar_recebedor(self._callback)

    def registrar_recebedor(self, callback):
        """
        Registra uma função para ser chamada quando dados vierem da camada de enlace
        """
        self.callback = callback

    def enviar(self, datagrama, next_hop):
        """
        Envia datagrama para next_hop, onde next_hop é um endereço IPv4
        fornecido como string (no formato x.y.z.w). A camada de enlace se
        responsabilizará por encontrar em qual enlace se encontra o next_hop.
        """
        # Encontra o Enlace capaz de alcançar next_hop e envia por ele
        self.enlaces[next_hop].enviar(datagrama)

    def _callback(self, datagrama):
        if self.callback:
            self.callback(datagrama)


class Enlace:
    def __init__(self, linha_serial):
        self.linha_serial = linha_serial
        self.linha_serial.registrar_recebedor(self.__raw_recv)
        self.dados_residuais = b''


    def registrar_recebedor(self, callback):
        self.callback = callback

    def enviar(self, datagrama):
        # Adicionando os bytes de escape para 0xC0 e 0xDB
        datagrama = datagrama.replace(b'\xdb', b'\xdb\xdd')
        datagrama = datagrama.replace(b'\xc0', b'\xdb\xdc')
        # Adicionando o byte 0xC0 no começo e no fim do datagrama e enviando 
        # para a linha serial
        self.linha_serial.enviar(b'\xc0' + datagrama + b'\xc0')
        pass

    def __raw_recv(self, dados):
        # Tratar mensagens recebidas incompletas ou de forma múltipla
        dados = self.dados_residuais + dados
        self.dados_residuais = b''
        if not dados.endswith(b'\xc0'):
            dados = dados.split(b'\xc0')
            dados = list(filter((b'').__ne__, dados))
            self.dados_residuais += dados.pop(-1)
        else:
            dados = dados.split(b'\xc0')
            dados = list(filter((b'').__ne__, dados))
        for datagrama in dados:
        # Tratar caracteres de escape
            datagrama = datagrama.replace(b'\xdb\xdc', b'\xc0')
            datagrama = datagrama.replace(b'\xdb\xdd', b'\xdb') 
        # Tratar datagrama mal formado
            try:
                self.callback(datagrama)
            except:
                import traceback
                traceback.print_exc()
        pass
