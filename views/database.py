import mysql.connector
from mysql.connector import Error


class Database:
    def __init__(self):
        self.host = 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com'
        self.database = 'punto_venta_lucero'
        self.user = '2vQtzbmmMG6qQ7s.root'
        self.password = 'Rm284HCXt9XFwBJn'
        self.connection = None

    def conectar(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                port=4000  # <- Necesario para la conexión en la nube de TiDB Cloud
            )
            return self.connection.is_connected()
        except Error as e:
            print(f"Error de conexión: {e}")
            self.connection = None
            return False

    def desconectar(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def ejecutar_query(self, query, params=None):
        if not self.connection or not self.connection.is_connected():
            if not self.conectar():
                print("❌ No se pudo establecer conexión con la base de datos.")
                return None

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            self.connection.commit()
            return cursor
        except Error as e:
            print(f"Error ejecutando query: {e}")
            return None

    def obtener_resultados(self, query, params=None):
        if not self.connection or not self.connection.is_connected():
            if not self.conectar():
                print("❌ No se pudo establecer conexión con la base de datos.")
                return None

        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            resultados = cursor.fetchall()
            cursor.close()
            return resultados
        except Error as e:
            print(f"Error obteniendo resultados: {e}")
            return None