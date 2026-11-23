import pytest
from app.services.website_analysis.ssrf_protection import validate_url_safe_for_scraping
from app.core.exceptions import SSRFProtectionException

def test_ssrf_blocks_localhost():
    with pytest.raises(SSRFProtectionException) as exc:
        validate_url_safe_for_scraping("http://localhost:8000/api")
    assert "interna/privada" in str(exc.value)

def test_ssrf_blocks_127_0_0_1():
    with pytest.raises(SSRFProtectionException) as exc:
        validate_url_safe_for_scraping("http://127.0.0.1:8000")
    assert "interna/privada" in str(exc.value)

def test_ssrf_blocks_private_subnet_192_168():
    with pytest.raises(SSRFProtectionException) as exc:
        validate_url_safe_for_scraping("http://192.168.1.100")
    assert "interna/privada" in str(exc.value)

def test_ssrf_blocks_social_media_instagram():
    with pytest.raises(SSRFProtectionException) as exc:
        validate_url_safe_for_scraping("https://www.instagram.com/clinicaexemplo")
    assert "rede social" in str(exc.value)

def test_ssrf_blocks_social_media_whatsapp_link():
    with pytest.raises(SSRFProtectionException) as exc:
        validate_url_safe_for_scraping("https://wa.me/5516999999999")
    assert "rede social" in str(exc.value)

def test_ssrf_allows_public_domain():
    # Deve validar sem exceções domínios públicos válidos (ex: google.com)
    url = validate_url_safe_for_scraping("https://google.com")
    assert url == "https://google.com"
