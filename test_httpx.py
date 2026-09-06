import httpx

try:
    response = httpx.get("https://httpbin.org/get")
    if response.status_code == 200:
        print("✅ HTTPX responde correctamente. Código:", response.status_code)
    else:
        print("⚠️ Respuesta inesperada:", response.status_code)
except Exception as e:
    print("❌ Error ejecutando solicitud con HTTPX:", e)