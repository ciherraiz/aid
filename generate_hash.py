import streamlit_authenticator as stauth

hashed = stauth.Hasher(["MI_CONTRASEÑA_REAL"]).generate()
print(hashed)