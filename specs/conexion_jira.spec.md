# Funcionalidad: [cambio de conexión con servidor jira] 
## Contexto: [En mi empresa han cambiado la configuración de conexión al servidor JIRA. Ya he modificado las ulr que van en las variables de estado, pero hay que hacer algunas modificaciones más en el código. Me han pasado el siguiente código Python que hay que adaptar al proyecto aid que estamos desarrollando.]
[El código python que me han dado es:
import ssl
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
from jira import JIRA

urllib3.disable_warnings()


class TLSRSAAdapter(HTTPAdapter):
    """
    Adapter para servidores con cifrados RSA sin Forward Secrecy.
    Necesario para conectar con infraestructura de la Junta de Andalucía
    desde Python con OpenSSL 3.x (que los bloquea por defecto).
    """
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.set_ciphers("AES256-GCM-SHA384:AES128-GCM-SHA256:AES256-CBC-SHA256:AES256-CBC-SHA:@SECLEVEL=0")
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


def get_jira_client(server: str, username: str, password: str) -> JIRA:
    """
    Devuelve un cliente JIRA conectado, compatible con servidores
    con TLS legacy (sin ECDHE/DHE, solo cifrados RSA).
    """
    jira = JIRA(
        server=server,
        basic_auth=(username, password),
        options={"verify": False},
        get_server_info=False,
        max_retries=0,
    )
    jira._session.mount("https://", TLSRSAAdapter())
    jira._session.verify = False
    return jira


# Uso
if __name__ == "__main__":
    jira = get_jira_client(
        server="https://jira.sspa.juntadeandalucia.es",
        username="tu_usuario",
        password="tu_contraseña",
    )
    print(jira.server_info())
]
## Comportamiento esperado :
### [Actualizar únicamente los elementos necesarios para conectar correctamente al servidor jira]
### [Actualiza los módulos necesarios evitando incluir elementos que no son pertienentes aunque aparezcan en el código de ejemplo]
## Criterios de aceptación
### [La conexión y la ejecución de alguna llamada al servidor jira es correcta.]