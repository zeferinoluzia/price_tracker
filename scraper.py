from playwright.sync_api import sync_playwright


def pegar_preco_amazon(pagina, url):

    print("Abrindo página...")

    pagina.goto(url, wait_until="domcontentloaded")

    print("Página carregada!")

    preco = pagina.locator(".a-offscreen").first

    texto_preco = preco.inner_text()

    print("Preço encontrado:", texto_preco)

    texto_preco = texto_preco.replace("R$", "")
    texto_preco = texto_preco.replace(".", "")
    texto_preco = texto_preco.replace(",", ".")

    preco_numero = float(texto_preco)

    return preco_numero