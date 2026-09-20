#!/usr/bin/env python3
import argparse
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
class IPInfo:
    """Encapsula as propriedades e regras de um endereço IP."""
    ip: ipaddress.IPv4Address | ipaddress.IPv6Address

    @property
    def is_private(self) -> bool:
        return self.ip.is_private

    @property
    def network_type(self) -> str:
        return "Rede Interna / LAN" if self.is_private else "Internet Pública"

    @property
    def version(self) -> str:
        return f"IPv{self.ip.version}"


@dataclass(frozen=True)
class Hop:
    """Representa um cabeçalho Received (Salto) e todos os IPs contidos nele."""
    number: int
    raw_header: str
    ips: list[IPInfo]


# ==============================================================================
# 2. CORE SERVICES (EXTRAÇÃO E PARSING)
# ==============================================================================

class IPExtractor:
    """Responsável exclusivamente por localizar e validar endereços IP em texto."""

    _IPV4_PATTERN = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
    # Regex flexível para IPv6: captura padrões completos e abreviados com '::'
    _IPV6_PATTERN = re.compile(r"\b[0-9a-fA-F]{0,4}(?::[0-9a-fA-F]{0,4}){2,7}\b")

    @classmethod
    def extract_valid_ips(cls, text: str) -> Iterator[ipaddress.IPv4Address | ipaddress.IPv6Address]:
        """Localiza candidatos via Regex e valida com o módulo ipaddress."""
        candidates = cls._IPV4_PATTERN.findall(text) + cls._IPV6_PATTERN.findall(text)

        seen_in_header = set()
        for candidate in candidates:
            try:
                ip_obj = ipaddress.ip_address(candidate)

                if ip_obj not in seen_in_header:
                    seen_in_header.add(ip_obj)
                    yield ip_obj

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

            # Captura todos os IPs válidos deste cabeçalho específico
            found_ips = [
                IPInfo(ip)
                for ip in self._ip_extractor.extract_valid_ips(clean_header)
            ]

            # Apenas cria o Salto se houver ao menos um IP válido no cabeçalho
            if found_ips:
                hops.append(
                    Hop(
                        number=hop_counter,
                        raw_header=clean_header,
                        ips=found_ips,
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

        print("=" * 72)
        print("  ROTA DE NAVEGAÇÃO DO E-MAIL (ORIGEM -> DESTINO)")
        print("=" * 72 + "\n")

        for hop in hops:
            snippet = (
                (hop.raw_header[:75] + "...")
                if len(hop.raw_header) > 75
                else hop.raw_header
            )
            print(f"Salto #{hop.number}")
            print(f"Cabeçalho: {snippet}")
            print("  │")

            total_ips = len(hop.ips)
            for idx, ip_info in enumerate(hop.ips, start=1):
                is_last = idx == total_ips
                tree_branch = "  └──" if is_last else "  ├──"
                tree_indent = "     " if is_last else "  │  "

                print(f"{tree_branch} IP:   {ip_info.ip} ({ip_info.version})")
                print(f"{tree_indent} Tipo: {ip_info.network_type}")
                if not is_last:
                    print("  │")

            print("\n" + "─" * 72 + "\n")



# ==============================================================================
# 4. CLI ARGUMENT PARSER & ENTRY POINT (PONTO DE ENTRADA DO APLICATIVO)
# ==============================================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extrai a rota de IPs de um arquivo .eml a partir dos cabeçalhos Received.")
    parser.add_argument(
        "file_path",
        nargs="?",
        default="mensagem.eml",
        type=Path,
        help="Caminho para o arquivo .eml (padrão: mensagem.eml)",
    )
    return parser.parse_args()

def main():
    args = parse_args()
    eml_path: Path = args.file_path

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

