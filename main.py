import datetime
from fastapi import FastAPI, status, HTTPException
from alpaca_market_data import market_data
from models import User
from database import conexion, crear_tablas
from config import SYMBOLS


crear_tablas()

app = FastAPI(title="Micro crypto exchange limitado")


@app.get("/", status_code=status.HTTP_200_OK)
def inicio():
    return {'message':'API para gestionar un Micro exchange cripto'}


@app.post("/users/{user_id}", tags=['Crear usuario'], status_code=status.HTTP_201_CREATED)
def crear_usuario(user_id: int):
    conn = conexion()
    user = User.usuario(conn, user_id)
    if user is not None:
        raise HTTPException(status_code=400, detail=f"Usuario con id {user_id} ya existe")
    User.create(conn, user_id)
    return {"message": f"Usuario {user_id} creado exitosamente"}


@app.get("/users/{user_id}/balance", tags=['Consultar balance'], status_code=status.HTTP_200_OK)
def obtener_balance(user_id: int):
    conn = conexion()
    user = User.usuario(conn, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"Usuario {user_id} no encontrado")
    return {"balance": user.balance}


@app.post("/users/{user_id}/depositar", tags=['Depositar'], status_code=status.HTTP_201_CREATED)
def depositar(user_id: int, monto: float):
    conn = conexion()
    user = User.usuario(conn, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"Usuario {user_id} no encontrado")
    user.depositar(conn, monto)
    return {"message": f"Deposito de {monto} realizado satisfactoriamente. El nuevo balance es {user.balance}"}


@app.post("/users/{user_id}/comprar", tags=['Comprar activos'], status_code=status.HTTP_201_CREATED)
def comprar(user_id: int, symbol: str, quantity: float):
    conn = conexion()
    user = User.usuario(conn, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"Usuario {user_id} no encontrado")

    if symbol.upper() not in SYMBOLS:
        raise HTTPException(status_code=404, detail=f"{symbol} no es un nombre de activo válido")
    
    precios = market_data(symbol.upper())
    if not precios:
        raise HTTPException(status_code=400, detail=f"Error al obtener precios") 

    ask_price = precios.get('ask_price')

    costo = quantity * ask_price
    if user.balance < costo:
        raise HTTPException(status_code=400, detail=f"Fondos insuficientes")

    user.depositar(conn, -costo)

    c = conn.cursor()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO transactions (user_id, asset, quantity, price, datetime, type) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, symbol.upper(), quantity, ask_price, now, 'BUY'))
    conn.commit()

    return {"message": "Orden ejecutada exitosamente", "Balance": user.balance}


@app.post("/users/{user_id}/vender", tags=['Vender activos'], status_code=status.HTTP_201_CREATED)
def vender(user_id: int, symbol: str, quantity: float):
    conn = conexion()
    user = User.usuario(conn, user_id)

    if user is None:
        raise HTTPException(status_code=404, detail=f"Usuario {user_id} no encontrado")

    if symbol.upper() not in SYMBOLS:
        raise HTTPException(status_code=404, detail=f"{symbol} no es un nombre de activo válido")
    
    precios = market_data(symbol.upper())
    if not precios:
        raise HTTPException(status_code=400, detail=f"Error al obtener precios") 

    bid_price = precios.get('bid_price') 

    c = conn.cursor()
    c.execute("SELECT SUM(quantity) FROM transactions WHERE user_id = ? AND asset = ?",
              (user_id, symbol.upper()))
    result = c.fetchone()

    if result[0] is not None:
        total_quantity = result[0]
    else:
        total_quantity = 0

    if total_quantity < quantity:
        raise HTTPException(status_code=400, detail=f"Cantidad a vender supera su posición")

    cost = quantity * bid_price
    user.depositar(conn, cost)

    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO transactions (user_id, asset, quantity, price, datetime, type) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, symbol.upper(), -quantity, bid_price, now, 'SELL'))
    conn.commit()

    return {"message": "Venta realizada exitosamente", "Balance": user.balance}


@app.get("/users/{user_id}/transacciones", tags=['Listar compras/ventas'], status_code=status.HTTP_200_OK)
def transacciones(user_id: int):
    conn = conexion()
    user = User.usuario(conn, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"Usuario {user_id} no encontrado")

    c = conn.cursor()
    c.execute("SELECT asset, quantity, price, datetime, type FROM transactions WHERE user_id = ? ORDER BY datetime DESC",
              (user_id,))
    rows = c.fetchall()

    transacciones = [{"asset": row[0], "quantity": row[1], "price": row[2], "datetime": row[3], "type": row[4]} for row in rows]
    return {"transacciones": transacciones}


@app.get("/users/{user_id}/positions", tags=['Listar posiciones abiertas'], status_code=status.HTTP_200_OK)
def obtener_posiciones(user_id: int):
    conn = conexion()
    user = User.usuario(conn, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"Usuario {user_id} no encontrado")
    posiciones = user.posiciones(conn)
    posiciones_abiertas = []
    for posicion in posiciones:
        if posicion['quantity'] > 0:
            posiciones_abiertas.append(posicion)
    return {"posiciones": posiciones_abiertas}


@app.get("/users/{user_id}/pnl", tags=['Obtener P&L'], status_code=status.HTTP_200_OK)
def obtener_pnl(user_id: int):
    conn = conexion()
    user = User.usuario(conn, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"Usuario {user_id} no encontrado")

    pnl = user.pnl(conn)
    return {"pnl": pnl}


@app.get("/precios/", tags=['Consultar precios'], status_code=status.HTTP_200_OK)
def consultar_precio(symbol: str):
    if symbol.upper() not in ['BTC/USD', 'ETH/USD']:
        raise HTTPException(status_code=404, detail=f"{symbol} no es un nombre de activo válido")
        
    precios = market_data(symbol.upper())
    return {'precios': precios}