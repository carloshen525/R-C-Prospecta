import ipaddress
import socket
from urllib.parse import urlparse
from app.core.exceptions import SSRFProtectionException

# Domínios de redes sociais e mensageiros que não devem ser processados como sites institucionais
IGNORED_DOMAINS = {
    "instagram.com", "www.instagram.com",
    "facebook.com", "www.facebook.com", "fb.com",
    "wa.me", "api.whatsapp.com", "whatsapp.com", "www.whatsapp.com",
    "tiktok.com", "www.tiktok.com",
    "linkedin.com", "www.linkedin.com",
    "twitter.com", "x.com",
    "youtube.com", "www.youtube.com",
    "t.me", "telegram.org",
    "linktr.ee", "bio.link", "bit.ly", "cutt.ly"
}

def validate_url_safe_for_scraping(url: str) -> str:
    """
    Valida a URL contra SSRF e descarta redes sociais e redirects impróprios.
    Lança SSRFProtectionException se a URL violar as regras de segurança.
    """
    if not url:
        raise SSRFProtectionException("URL não informada")

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)
    hostname = parsed.hostname

    if not hostname:
        raise SSRFProtectionException("Hostname inválido na URL")

    # Verifica se é domínio de rede social ou linktree
    cleaned_host = hostname.lower()
    for ignored in IGNORED_DOMAINS:
        if cleaned_host == ignored or cleaned_host.endswith("." + ignored):
            raise SSRFProtectionException(f"Domínio '{cleaned_host}' é uma rede social ou agregador de links, não um site institucional.")

    # Resolve o IP do hostname para verificar se é privado ou de metadados
    try:
        ip_addresses = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise SSRFProtectionException(f"Não foi possível resolver o hostname: {hostname}")

    for addr_info in ip_addresses:
        ip_str = addr_info[4][0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved or ip_obj.is_multicast:
                raise SSRFProtectionException(f"Acesso bloqueado: IP de rede interna/privada detectado ({ip_str})")
            
            # Bloqueia explicitamente metadados de nuvem (AWS/GCP/Azure: 169.254.169.254)
            if str(ip_obj) == "169.254.169.254":
                raise SSRFProtectionException("Acesso bloqueado a endpoint de metadados da nuvem")
        except ValueError:
            raise SSRFProtectionException(f"Formato de IP inválido: {ip_str}")

    return url
