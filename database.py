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
            self.desconectar()
            self.connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                port=4000,
                connection_timeout=10,
            )
            return self.connection.is_connected()
        except Error as e:
            print(f"Error de conexión: {e}")
            self.connection = None
            return False

    def desconectar(self):
        try:
            if self.connection and self.connection.is_connected():
                self.connection.close()
        except Exception:
            pass
        finally:
            self.connection = None

    def _asegurar_conexion(self):
        try:
            if self.connection and self.connection.is_connected():
                self.connection.ping(reconnect=True, attempts=1, delay=0)
                return True
        except Exception:
            pass
        return self.conectar()

    def ejecutar_query(self, query, params=None):
        if not self._asegurar_conexion():
            print("❌ No se pudo establecer conexión con la base de datos.")
            return None

        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            last_id = cursor.lastrowid
            self.connection.commit()
            return last_id
        except Error as e:
            print(f"Error ejecutando query: {e}")
            try:
                self.connection.rollback()
            except Exception:
                pass
            return None
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass

    def obtener_resultados(self, query, params=None):
        if not self._asegurar_conexion():
            print("❌ No se pudo establecer conexión con la base de datos.")
            return []

        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            resultados = cursor.fetchall()
            return resultados or []
        except Error as e:
            print(f"Error obteniendo resultados: {e}")
            return []
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass
