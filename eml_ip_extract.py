import email
from email import policy
from email.message import EmailMessage
import ipaddress
from pathlib import Path
import re
from dataclasses import dataclass
from typing import Iterator

# ==============================================================================
# 1. DOMAIN MODELS (MODELOS DE DOMÍNIO)
# ==============================================================================

@dataclass(frozen=True)
class Hop:
    """Representa um salto individual (hop) no percurso do e-mail.
    
    Encapsula os dados do salto e regras de negócio relativas ao IP.
    """
    number: int
    ip: ipaddress.IPv4Address | ipaddress.IPv6Address
    raw_header: str

    @property
    def is_private(self) -> bool:
        return self.ip.is_private

    @property
    def network_type(self) -> str:
        return "Rede Interna / LAN" if self.is_private else "Internet Pública"

    @property
    def version(self) -> str:
        return f"IPv{self.ip.version}"



# ==============================================================================
# 2. CORE SERVICES (EXTRAÇÃO E PARSING)
# ==============================================================================

class IPExtractor:
    """Responsável exclusivamente por localizar e validar endereços IP em texto."""

    _IPV4_PATTERN = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
    _IPV6_PATTERN = re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b")

    @classmethod
    def extract_valid_ips(cls, text: str) -> Iterator[ipaddress.IPv4Address | ipaddress.IPv6Address]:
        """Localiza candidatos via Regex e valida com o módulo ipaddress."""
        matches = cls._IPV4_PATTERN.findall(text) + cls._IPV6_PATTERN.findall(text)

        for match in matches:
            try:
                yield ipaddress.ip_address(match)
            except ValueError:
                continue # Descarta números fora do intervalo IP



class EmlFileReader:
    """Responsável apenas por carregar arquivos .eml do sistema de arquivos."""

    @staticmethod
    def load(file_path: Path) -> EmailMessage:
        if not file_path.is_file():
            raise FileNotFoundError(f"Arquivo de email não encontrado: {file_path}")

        with open(file_path, "rb") as file:
            return email.message_from_binary_file(file, policy=policy.default)



class EmailRouteTracer:
    """Serviço de domínio que orquestra a reconstrução da rota do e-mail."""

    def __init__(self, ip_extractor: type[IPExtractor] = IPExtractor):
        self._ip_extractor = ip_extractor

    def trace_route(self, message: EmailMessage) -> list[Hop]:
        """Extrai os cabeçalhos 'Received' em ordem cronológica (origem -> destino)."""

        received_headers = message.get_all("Received", [])[::-1]

        hops: list[Hop] = []
        hop_counter = 1

        for header_value in received_headers:
            clean_header = " ".join(str(header_value).split())

            for ip in self._ip_extractor.extract_valid_ips(clean_header):
                hops.append(
                    Hop(
                        number=hop_counter,
                        ip=ip,
                        raw_header=clean_header
                    )
                )
                hop_counter += 1

        return hops



# ==============================================================================
# 3. PRESENTATION LAYER (INTERFACE DE USUÁRIO / SAÍDA)
# ==============================================================================

class ConsolePresenter:
    """Responsável exclusivamente pela formatação e exibição do resultado."""

    @staticmethod
    def display_route(hops: list[Hop]) -> None:
        if not hops:
            print("Nenhum cabeçalho 'Received' ou IP válido foi encontrado.")
            return

        print("=" * 68)
        print("  ROTA DE NAVEGAÇÃO DO E-MAIL (ORIGEM -> DESTINO)")
        print("=" * 68 + "\n")

        for hop in hops:
            snippet = (hop.raw_header[:70] + "...") if len(hop.raw_header) > 70 else hop.raw_header
            print(f"Salto #{hop.number}")
            print(f" ├─ IP:         {hop.ip} ({hop.version})")
            print(f" ├─ Tipo:       {hop.network_type}")
            print(f" └─ Cabeçalho:  {snippet}\n")



# ==============================================================================
# 4. ENTRY POINT (PONTO DE ENTRADA DO APLICATIVO)
# ==============================================================================

def main():
    eml_path = Path("mensagem.eml")

    try:
        # 1. Carrega o e-mail
        email_message = EmlFileReader.load(eml_path)

        # 2. Executa a análise de rota (injetando o serviço extractor)
        tracer = EmailRouteTracer()
        route_hops = tracer.trace_route(email_message)

        # 3. Exibe os resultados
        ConsolePresenter.display_route(route_hops)

    except FileNotFoundError as err:
        print(f"[ERRO DE ARQUIVO] {err}")
    except Exception as err:
        print(f"[ERRO INESPERADO] {err}")




if __name__ == "__main__":
    main()

