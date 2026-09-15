# 📧 EML IP Route Tracer

Uma ferramenta em Python desenvolvida com foco em **Clean Code** e **Design Patterns** (SRP, Injeção de Dependência) para analisar arquivos de e-mail (`.eml`), extrair endereços IP válidos (IPv4/IPv6) dos cabeçalhos `Received` e rastrear a rota cronológica da mensagem desde a origem até o destino.

---

## ⚡ Destaques

- **Zero dependências externas:** Utiliza exclusivamente a biblioteca padrão do Python (`email`, `ipaddress`, `re`, `pathlib`).
- **Validação rigorosa de IPs:** Filtra falsos positivos e valida a integridade dos endereços.
- **Classificação de redes:** Identifica automaticamente se o IP pertence a uma rede privada (LAN/Interna) ou pública (Internet).
- **Ordem cronológica real:** Inverte o empilhamento padrão dos cabeçalhos `Received` para exibir a rota correta (Origem → Intermediários → Destino).
- **Código modular:** Separação clara entre modelos de domínio, leitores, extratores e camada de apresentação.

---

## 🚀 Como Executar

### Pré-requisitos

- **Python 3.10+** instalado.

### Passo a Passo

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/seu-usuario/eml-ip-route-tracer.git](https://github.com/seu-usuario/eml-ip-route-tracer.git)
   cd eml-ip-route-tracer
   ```

2. **Adicione seu arquivo `.eml`:**
   Coloque o arquivo de e-mail a ser analisado no diretório raiz do projeto com o nome `mensagem.eml` (ou altere o caminho diretamente no arquivo `main.py`).

3. **Execute o script:**
   ```bash
   python main.py
   ```

---

## 📊 Exemplo de Saída

```text
====================================================================
  ROTA DE NAVEGAÇÃO DO E-MAIL (ORIGEM -> DESTINO)
====================================================================

Salto #1
 ├─ IP:         192.168.1.15 (IPv4)
 ├─ Tipo:       Rede Interna / LAN
 └─ Cabeçalho:  from mail.local (192.168.1.15) by smtp.provedor.com...

Salto #2
 ├─ IP:         203.0.113.195 (IPv4)
 ├─ Tipo:       Internet Pública
 └─ Cabeçalho:  from smtp.provedor.com (203.0.113.195) by mx.google.com...
```

---

## 🏗️ Arquitetura do Código

- `Hop`: Modelo de domínio imutável (`dataclass`) representando um salto na rede.
- `IPExtractor`: Responsável exclusivamente pelo parse via Regex e validação de IPs.
- `EmlFileReader`: Cuida da leitura binária e parse estruturado da mensagem MIME.
- `EmailRouteTracer`: Serviço que orquestra a ordenação e criação da rota dos saltos.
- `ConsolePresenter`: Camada de apresentação responsável pela formatação da saída no terminal.

---

## 📄 Licença

Este projeto está sob a licença [MIT](LICENSE).