import datetime as dt
from tabulate import tabulate 
import json
import csv
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side, Alignment
import sys
import sqlite3
from sqlite3 import Error
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

fecha_hoy = dt.date.today()

try:
    with sqlite3.connect("Eventos.db") as conn:
        mi_cursor = conn.cursor()
        mi_cursor.execute("CREATE TABLE IF NOT EXISTS CLIENTES (ID_CLIENTE INTEGER PRIMARY KEY, NOMBRE TEXT NOT NULL, APELLIDO TEXT NOT NULL);")
        print("Tabla CLIENTES creada exitosamente")
        mi_cursor.execute("CREATE TABLE IF NOT EXISTS SALAS (ID_SALA INTEGER PRIMARY KEY, NOMBRE TEXT NOT NULL, CAPACIDAD INTEGER NOT NULL);")
        print("Tabla SALAS creada exitosamente")
        mi_cursor.execute("CREATE TABLE IF NOT EXISTS EVENTOS (ID_EVENTO INTEGER PRIMARY KEY, ID_SALA INTEGER, ID_CLIENTE INTEGER, NOMBRE_EVENTO TEXT NOT NULL, TURNO TEXT NOT NULL, FECHA timestamp, FOREIGN KEY (ID_SALA) REFERENCES SALAS(ID_SALA), FOREIGN KEY (ID_CLIENTE) REFERENCES CLIENTES(ID_CLIENTE));")
        print("Tabla EVENTOS creada exitosamente")
except Error as e:
    print (e)
except:
    print(f"Se produjo el siguiente error: {sys.exc_info()[0]}")

print("*"*70)
print("\t**Bienvenido al sistema de reservacion de eventos**")
print("*"*70)

while True:
    print("\n===============Menu===============")
    print("1.Registrar evento")
    print("2.Editar nombre del evento")
    print("3.Consultar reservaciones")
    print("4.Registrar cliente")
    print("5.Registrar sala")
    print("6.Salir")
    print("="*34)
    
    try:
        opcion = int(input("Ingrese una opcion: "))
    except ValueError:
        print("Favor de digitar un numero valido\n")
        continue
    
    match opcion:
        case 1:
            print("\n===============Registrar evento===============\n")
            try:
                with sqlite3.connect("Eventos.db") as conn:
                    mi_cursor = conn.cursor()
                    mi_cursor.execute("SELECT COUNT(*) FROM CLIENTES")
                    registros = mi_cursor.fetchall()
                    if registros[0][0] == 0:
                        print("Favor de registrar un cliente previamente para poder registrar un evento\n")
                        continue
                    mi_cursor.execute("SELECT COUNT(*) FROM SALAS")
                    registros = mi_cursor.fetchall()
                    if registros[0][0] == 0:
                        print("Favor de registrar una sala previamente para poder registrar un evento\n")
                        continue
            except Error as e:
                print (e)
            except:
                print(f"Se produjo el siguiente error: {sys.exc_info()[0]}")
                        
            lista_clientes = []
            claves_clientes_validas = []
            try:
                with sqlite3.connect("Eventos.db") as conn:
                    mi_cursor = conn.cursor()
                    mi_cursor.execute("SELECT ID_CLIENTE, APELLIDO, NOMBRE FROM CLIENTES ORDER BY APELLIDO, NOMBRE")
                    lista_clientes = mi_cursor.fetchall()
                    claves_clientes_validas = [cliente[0] for cliente in lista_clientes]
            except Error as e:
                print (e)
            except:
                print(f"Se produjo el siguiente error: {sys.exc_info()[0]}")
                    
            while True:
                print("\n******Clientes registrados******")
                encabezados_clientes = ["ID Cliente", "Apellidos", "Nombre(s)"]
                print(tabulate(lista_clientes, headers=encabezados_clientes, tablefmt="fancy_grid", stralign="center", numalign="center"))
                
                try:
                    clave_cliente_elegida = int(input("Ingresa tu clave de cliente: "))                  
                    if clave_cliente_elegida not in claves_clientes_validas:
                        print("El cliente no existe\n")
                        salida = input("Escriba X si quiere regresar al menu principal, si no digita cualquier otro caracter: ")
                        if salida.upper() == "X":
                            break
                        continue
                except ValueError:
                    print("Favor de digitar un numero valido\n")
                    continue
                
                while True:     
                    fecha_elegida = input("\nIngrese la fecha del evento (dd/mm/aaaa): ")
                    try:
                        fecha_evento = dt.datetime.strptime(fecha_elegida, "%d/%m/%Y").date()
                    except ValueError:
                        print("Favor de digitar una fecha valida\n")
                        continue
                    if (fecha_evento - fecha_hoy).days <= 2:
                        print(f"La fecha debe ser, por lo menos, dos días posteriores a la fecha actual\n")
                        continue

                    if fecha_evento.weekday() == 6: 
                        lunes_siguiente = fecha_evento + dt.timedelta(days=1)
                        monday_siguiente_str = lunes_siguiente.strftime('%d/%m/%Y')                       
                        print(f"No se pueden realizar reservaciones para los dias domingo")
                        
                        opcion_domingo = input(f"Se propone reservar para el lunes siguiente ({lunes_siguiente}), colocar S para aceptar: ")                            
                        if opcion_domingo.upper() == "S":
                            fecha_evento = lunes_siguiente
                            break 
                        else:
                            continue
                    break 
                    
                salas_info = {} 
                ids_salas_validas = []
                valor = (fecha_evento.isoformat(),) 
                
                try:
                    with sqlite3.connect("Eventos.db") as conn:
                        mi_cursor = conn.cursor()
                        mi_cursor.execute("SELECT ID_SALA, NOMBRE, CAPACIDAD FROM SALAS")
                        lista_salas_data = mi_cursor.fetchall() 
                        mi_cursor.execute("SELECT ID_SALA, TURNO FROM EVENTOS WHERE DATE(FECHA) = ?", valor)
                        eventos_en_fecha = mi_cursor.fetchall()
                except Error as e:
                    print(e)
                except:
                    print(f"Se produjo el siguiente error: {sys.exc_info()[0]}")
                    
                for sala in lista_salas_data:
                    salas_info[sala[0]] = [sala[1], sala[2]] 
                    ids_salas_validas.append(sala[0])

                salas_turnos_disponibles = {}
                turnos_validos = ["MATUTINO", "VESPERTINO", "NOCTURNO"]

                for sala_id, sala_info in salas_info.items():
                    capacidad_sala = sala_info[1]                    
                    turnos_ocupados = [evento_db[1] for evento_db in eventos_en_fecha if evento_db[0] == sala_id]                     
                    turnos_disponibles = [turno for turno in turnos_validos if turno not in turnos_ocupados]                   
                    salas_turnos_disponibles[sala_id] = [capacidad_sala, turnos_disponibles]

                print(f"\n\t**Salas disponibles para la fecha {fecha_elegida}**")
                filas_tabla_salas = []
                for sala_id, info in salas_turnos_disponibles.items():
                    nombre_sala = salas_info[sala_id][0]
                    capacidad = info[0]
                    turnos_str = ', '.join(info[1]) if info[1] else "--- NINGUNO ---"
                    filas_tabla_salas.append([sala_id, nombre_sala, capacidad, turnos_str])
                
                headers = ["Sala ID","Nombre Sala", "Cupo","TURNOS DISPONIBLES"]
                tabla = tabulate(filas_tabla_salas, headers, tablefmt="fancy_grid", stralign="center", numalign="center")
                print(tabla)
                
                while True:
                    try:
                        sala_elegida = int(input("Ingrese el ID de la sala: "))
                    except:
                        print("Favor de digitar un numero valido\n")
                        continue  
                    if sala_elegida not in ids_salas_validas:
                        print("La sala no existe\n")
                        continue
                    break 

                while True:
                    turno_elegido = input("Ingrese el turno a elegir: ").upper()
                    if turno_elegido not in turnos_validos:
                        print("Turno no valido \n")
                        continue
                    salida = ""
                    if turno_elegido not in salas_turnos_disponibles[sala_elegida][1]:
                        print("Este turno ya está ocupado para la sala y fecha seleccionadas. Por favor, elija otro turno\n")
                        salida = input("Escriba X si quiere regresar al menu principal, si no digita cualquier otro caracter: ")
                        if salida.upper() == "X":
                            break
                        continue
                    break
                if salida.upper() == "X":
                    break
                
                while True:
                    nombre_evento = input("Ingrese el nombre del evento: ")
                    if not nombre_evento:
                        print("El nombre del evento no puede estar vacio\n") 
                        continue
                    if nombre_evento.isspace():
                        print("El nombre del evento no puede consistir solo en espacios en blanco\n")
                        continue
                    if nombre_evento.isdigit():
                        print("El nombre del evento no puede ser un numero\n")
                        continue
                    break 
                
                valores = (sala_elegida, clave_cliente_elegida, nombre_evento.upper(), turno_elegido.upper(), fecha_evento)

                try:
                    with sqlite3.connect("Eventos.db") as conn:
                        mi_cursor = conn.cursor()
                        mi_cursor.execute("INSERT INTO EVENTOS (ID_SALA, ID_CLIENTE, NOMBRE_EVENTO, TURNO, FECHA) VALUES (?, ?, ?, ?, ?)", valores)
                        print("\n**Evento registrado con exito**")
                except Error as e:
                    print (e)
                except:
                    print(f"Se produjo el siguiente error: {sys.exc_info()[0]}")
                break 