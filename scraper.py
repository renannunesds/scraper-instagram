import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- Configurações do Backend ---
BACKEND_URL = "http://localhost:8080/api/instagram/sincronizar"
JWT_TOKEN = "eyJhbGciOiJIUzM4NCJ9.eyJzdWIiOiJhZG1pbkBjYW9ndWlhLmNvbSIsInBlcmZpbCI6IkFETUlOIiwiaWF0IjoxNzk0MzM3MzE4LCJleHAiOjE3OTQ0MjM3MTh9.ZqWlbhX2iaXJhnGd5TfYKuGpCwZm1m4NHETYa817bboT0a1ZaAuizJpjJHsWayYO"

# --- Configurações do Instagram ---
PERFIL_ALVO = "caoguiaurutai"

def iniciar_driver():
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # Descomente para rodar sem abrir a janela
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-notifications')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def extrair_ultima_postagem(driver):
    url_perfil = f"https://www.instagram.com/{PERFIL_ALVO}/"
    print(f"Acessando perfil público: {url_perfil}")
    driver.get(url_perfil)
    time.sleep(4)
    
    wait = WebDriverWait(driver, 15)
    
    # 1. Pega dinamicamente o link da postagem mais recente direto do grid do perfil
    grid_items = wait.until(
        EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/p/') or contains(@href, '/reel/')]"))
    )
    
    if not grid_items:
        raise Exception("Nenhuma publicação encontrada no perfil público.")

    primeiro_post = grid_items[0]
    link_post = primeiro_post.get_attribute("href")

    url_imagem = ""
    try:
        img_elem = primeiro_post.find_element(By.TAG_NAME, "img")
        url_imagem = img_elem.get_attribute("src")
    except Exception:
        url_imagem = "https://via.placeholder.com/600x600.png?text=Cao+Guia+Urutai"

    # 2. Entra na página específica da postagem para raspar a legenda real atualizada
    print(f"Extraindo automaticamente a legenda da postagem: {link_post}")
    driver.get(link_post)
    time.sleep(3)

    legenda = ""
    try:
        # Extrai dinamicamente a descrição oficial gerada pelo Instagram para o post
        meta_elem = driver.find_element(By.XPATH, "//meta[@property='og:title'] | //meta[@name='description']")
        meta_texto = meta_elem.get_attribute("content")
        
        if meta_texto and ":" in meta_texto:
            partes = meta_texto.split(":", 1)
            legenda_extraida = partes[1].strip().strip('"').strip('“').strip('”')
            
            # Limpeza cirúrgica para remover o ponto e aspa indesejada no final
            if legenda_extraida.endswith('."'):
                legenda_extraida = legenda_extraida[:-2] + '.'
            elif legenda_extraida.endswith('"'):
                legenda_extraida = legenda_extraida[:-1]

            if len(legenda_extraida) > 2:
                legenda = legenda_extraida
        else:
            legenda = meta_texto
    except Exception as e:
        print(f"Erro ao ler a legenda dinâmica: {e}")

    # Tratamento para garantir que nunca envie vazio
    if not legenda:
        legenda = "Confira a nova publicação no perfil oficial do Cão-Guia Urutaí."

    url_img_curta = url_imagem[:250] if url_imagem else ""
    link_post_curto = link_post[:250] if link_post else ""

    return {
        "linkPostagem": link_post_curto,
        "link_postagem": link_post_curto,
        "urlPost": link_post_curto,
        "urlImagem": url_img_curta,
        "url_imagem": url_img_curta,
        "textoDescricao": legenda,
        "texto_descricao": legenda,
        "descricao": legenda
    }

def enviar_para_backend(dados_post):
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {JWT_TOKEN}"
    }
    
    print("\nEnviando dados dinâmicos para o Spring Boot...")
    
    # Garante o envio correto de caracteres especiais e emojis via UTF-8
    response = requests.post(BACKEND_URL, data=json_com_utf8(dados_post), headers=headers)
    
    if response.status_code in [200, 201]:
        print("\n Postagem dinâmica enviada e salva no banco de dados com sucesso!")
    else:
        print(f"\n Erro no envio (HTTP {response.status_code}):", response.text)

def json_com_utf8(dados):
    import json
    return json.dumps(dados, ensure_ascii=False).encode('utf-8')

def main():
    driver = iniciar_driver()
    try:
        dados = extrair_ultima_postagem(driver)
        enviar_para_backend(dados)
    except Exception as e:
        print(f"Erro durante a automação: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()