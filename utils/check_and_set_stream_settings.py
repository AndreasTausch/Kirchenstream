from obsws_python import ReqClient

# === Verbindungskonfiguration (anpassen!) ===
OBS_HOST = "localhost"
OBS_PORT = 4455
OBS_PASSWORD = "RRzN7LS7IMtDXGwE"

# === Ziel-Stream-Daten (anpassen!) ===
RTMP_SERVER = "rtmp://a.rtmp.youtube.com/live2"
STREAM_KEY = "18q6-1zm0-9szu-mm6f-47tg"

try:
    print(f"🔌 Verbinde mit OBS @ {OBS_HOST}:{OBS_PORT} ...")
    client = ReqClient(host=OBS_HOST, port=OBS_PORT, password=OBS_PASSWORD)
    print("✅ Verbindung hergestellt.")

    print("➡️  Sende Befehl: SetStreamServiceSettings")
    client.set_stream_service_settings(
        "rtmp_custom",
        {
            "server": RTMP_SERVER,
            "key": STREAM_KEY,
            "use_auth": False
        }
    )
    print("✅ Einstellungen gesetzt.")

    print("🔍 Lese aktuelle Einstellungen mit GetStreamServiceSettings ...")
    result = client.get_stream_service_settings()
    current_type = result.stream_service_type
    current_data = result.stream_service_settings
    current_server = current_data.get("server") or ""
    current_key = current_data.get("key") or ""   

    print("📤 Antwort von OBS:")
    print(f"  Typ:    {current_type}")
    print(f"  Server: {current_server}")
    print(f"  Key:    {current_key}")

    print("\n🧪 Validierung:")
    if current_type != "rtmp_custom":
        print("❌ Falscher Typ gesetzt.")
    elif current_server != RTMP_SERVER:
        print("❌ RTMP-Server stimmt nicht überein.")
    elif current_key != STREAM_KEY:
        print("❌ Stream-Key stimmt nicht überein.")
    else:
        print("✅ Einstellungen korrekt übernommen.")

    client.disconnect()
    print("\n🔌 Verbindung zu OBS getrennt.")

except Exception as e:
    print("❌ Fehler bei Verbindung oder WebSocket-Befehl:")
    print(str(e))
