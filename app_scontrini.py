import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Vibe Smart Spesa", page_icon="🛒")

# --- CREDENZIALI ---
# Usiamo il formato corretto per la chiave privata
pk = "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDVRc8s7nIENYVi\nn+zdpX1hk5NE72ye7xHTyC5KyaCjJy2VqIoHC16eKhJrMr3DdwV2QM1CIdLRooJL\nCb9ljwA0ybIZCHqJ/WMhIWQ1VTJbWyDpFO+ZdMJOFofvCVOk+qxDl5WdO8m0twEf\nFTaxWn6zCDZ1Ar0iICMoWqy85IB4EroKXPr28OuYd2739QQ4Wtvuwp0Gq3Wt8Cyg\nSlJoX9hvPm+YF/Zdo7gZ9CKKw+rznID4q1qOf9NgRpHSKMrvwDGBSVN8fo+utDYu\njc0CJ+qTngVa7YPdVxi7B14LrI1nJackJZE64+8r5vyfh1GzDp9KJXMVcbFrcpHI\nTcL7eUtLAgMBAAECggEAJnph1oluqLO/TPvtkE+7P0+Q0m8f+czIOp1zPKsEAGuh\nHc86l+rFN2P/zrdo5UskASHP5o6Tqp7XQxKPJZOXRe7d4wZUlXDR4bhUjArC+xiF\n54ePcvBN3ijSfZ4BKVLQoaFHrQaMbb5WxXTeWUEqesKQkKvd07pYnX8+ixXu17q0\n12zq72wydJHuGev9fGwF9+SWpwS6Bx5EyMnNXnqfz457RvdvS6MWGhbIu9DuhH76\njEYuTwwDVWtzFsViaTjTHvyyZ3E9mDFw2T/7kBp5diaL2pxm1h2Srex07yW2yQl6\nUEjY4kCoq2nmpe6tfGwXxwsfjphZ6gjCheIe/DiqAQKBgQDyQ7eVugsIGhGWGekB\nhyctRjwAXSjj7LVUWf6cZNRhPkGEXQqe4emgb5QpnXTcmufuGvvv/0/r3z991Uwk\nfD/Pz39hFs3An0wXnpe+HpU1s187EOVP+9CZSS5XLqUji3XGtJ7qgZnX3MlxAbl0\nQ5hzmyGhsATT6e53uIi9ol/pOwKBgQDhXUxQ4PGgRdZftlZUQ4d2dFXMj/m2kI1h\nTUEvbQcsJT8yIKp6Z5VVvBwDnAnlWiUt0NokeHJdQPem0bkd/oRFdz+ykUKKRBUh\nctgpj5wy9QeqvY47y0JpBnpk1jdvxjQiY63xp8MZePnR8Sy1W4I0Rq51CiWqiAo9\nFCwlmbaFMQKBgQDaOqu2AReM3ca3unFNAg0FWH4WKdT6s7CH4mVbReyWCDmGXTWC\n96e28Ku7bO3nBtcjgkUt5IN+yuRrmmbzesUUkiqBL8R53kTyBddU2EG6VPDUyRx3\nlzNJ0UUgHZF+WlLmgq+gOMx3SZhf5pjDJVy/zp9WAbPnnJNGXwE2KX1SHwKBgEt/\nWOijYu7hVn6789HIyaG6OWANP4eUh3h4TAUaTlPQqoodfV8CQnn1SaE/7eTCvT/K\n/rlHDHEHKa/eBFjzAdbPqywkE5mEU1vgQGAz9wzvH0FovTR01GuguvH6/ZlZWe/H\nWudg3zAyYeaeF+8tl8Hxh9I3swSdDGkHz/5Mr2ORAoGBAJS/uHLFzIUkclsx6QCZ\nMya/YbgqtkDZoJJVNV1nquiILubjDBh2CKBeTkpDJHjn1Mw2R8PuIlxS1kuUb2Dx\niynfbItQcJSdSInLefWif9D7LwLqXjH4JMmOf0HJQaqhzyZQTGSY4vkLu3AxDIh+\npgmYaCyTcGdaV4Bz8nFnWGdq\n-----END PRIVATE KEY-----\n"

google_secrets = {
    "type": "service_account",
    "project_id": "app-spesa-494412",
    "private_key_id": "6dedc4d2d9b1e8c27dd280eb5d12fc6a7122e5e7",
    "private_key": pk.replace("\\n", "\n"), # CORREZIONE FONDAMENTALE
    "client_email": "spesa-bot@app-spesa-494412.iam.gserviceaccount.com",
    "client_id": "101057625591465586788",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/spesa-bot%40app-spesa-494412.iam.gserviceaccount.com"
}

for key, value in google_secrets.items():
    st.secrets[f"connections.gsheets.{key}"] = value

# --- CONNESSIONE ---
URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1BTa0dIFYpVGGRR_DXn-qnRpcR8NOHVq1NPgZEUnKyt0/edit"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_inventario = conn.read(spreadsheet=URL_FOGLIO, worksheet="0")
    st.success("✅ Database collegato!")
except Exception as e:
    st.error(f"❌ Errore: {e}")
    df_inventario = pd.DataFrame(columns=['Codice a Barre', 'PUNTO VENDITA', 'Nome Prodotto', 'Prezzo standard'])

st.title("🛒 Vibe Smart Spesa")
# ... resto del codice ...
